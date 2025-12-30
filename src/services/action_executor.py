"""
Action executor engine.
Executes action definitions from JSON files.
"""
import logging
import time
import json
import traceback
import re
import os
from copy import deepcopy
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from newAgent.src.services.action_loader import ActionLoader, get_action_loader
from newAgent.src.services.action_variables import ActionVariableResolver, create_resolver
from newAgent.src.services.config_manager import ConfigManager
from newAgent.src.services.config_helper import ConfigHelper
from newAgent.src.services.action_error_handler import ActionErrorHandler
from newAgent.src.data.attributes import Attrs
from newAgent.src.robot.scraper import Bot

logger = logging.getLogger(__name__)


class ActionExecutor:
    """Executes action definitions from JSON files."""
    
    def __init__(self, bot: Bot, action: Any, saved_item: Optional[Any] = None,
                 campaign: Optional[Any] = None, api_client: Optional[Any] = None):
        """
        Initialize action executor.
        
        Args:
            bot: Bot instance (from scraper.py) for webdriver operations
            action: Action object with properties
            saved_item: Optional SavedItem for iteration context
            campaign: Optional Campaign object
            api_client: Optional API client for saving data
        """
        self.bot = bot
        self.action = action
        self.saved_item = saved_item
        self.campaign = campaign
        self.api_client = api_client
        
        self.action_loader = get_action_loader()
        # Get platform from bot instance for database initialization
        platform = getattr(bot, 'platform', 'MAC')  # Default to MAC if not available
        self.config_manager = ConfigManager(platform=platform)
        self.error_handler = ActionErrorHandler()
        
        # Create variable resolver
        self.resolver = create_resolver(action, saved_item, campaign)
        
        # Execution context
        self.context: Dict[str, Any] = {
            'elements': {},  # Store found elements by step ID
            'data': {},  # Store extracted data
            'variables': {
                'configContext': None  # Initialize config context
            },  # Store computed variables
            'step_results': {},  # Store step execution results
            'extracted_items': [],  # Store items for batch saving
            'recursion_counts': {}  # Track recursion depth per step
        }

        # Safety limit for recursive conditions
        self.MAX_RECURSION_DEPTH = 50  # Prevent infinite loops
        
        # Load action definition
        platform = getattr(action, 'source', '').upper()
        action_type = getattr(action, 'type', '').upper()
        
        logger.info(f"Loading action definition for platform={platform}, type={action_type}")
        logger.info(f"Action object attributes: source={getattr(action, 'source', None)}, type={getattr(action, 'type', None)}")
        
        self.action_def = self.action_loader.load_action(platform, action_type)
        
        if not self.action_def:
            logger.error(f"Could not load action definition for {platform}/{action_type}")
            logger.error(f"Available actions: {self.action_loader.list_actions(platform)}")
            raise ValueError(f"Could not load action definition for {platform}/{action_type}")
    
    def execute(self) -> Dict[str, Any]:
        """
        Execute the action definition.
        
        Returns:
            Dictionary with execution results
        """
        logger.info("=" * 60)
        logger.info("ActionExecutor.execute() called")
        logger.info(f"Action definition loaded: {self.action_def is not None}")
        
        if not self.action_def:
            logger.error("No action definition loaded")
            return {'success': False, 'error': 'No action definition loaded'}
        
        logger.info(f"Action definition keys: {list(self.action_def.keys())}")
        logger.info(f"Steps count: {len(self.action_def.get('steps', []))}")
        logger.info(f"Loops count: {len(self.action_def.get('loops', []))}")
        
        try:
            # First, execute initial steps (those not referenced in loops)
            # Then execute loops if defined
            all_steps = self.action_def.get('steps', [])
            loops = self.action_def.get('loops', [])
            
            # Collect all step IDs referenced in loops (including those in condition branches)
            loop_step_ids = set()
            
            def get_all_referenced_ids(step_ids):
                referenced = set(step_ids)
                for sid in step_ids:
                    # Find step definition
                    step = next((s for s in all_steps if s.get('id') == sid), None)
                    if step and step.get('type') == 'condition':
                        then_ids = step.get('then', [])
                        else_ids = step.get('else', [])
                        referenced.update(get_all_referenced_ids(then_ids))
                        referenced.update(get_all_referenced_ids(else_ids))
                return referenced

            for loop_def in loops:
                loop_step_ids.update(get_all_referenced_ids(loop_def.get('steps', [])))
            
            # Separate initial steps from loop steps
            initial_steps = [step for step in all_steps if step.get('id') not in loop_step_ids]
            
            # Execute initial steps first
            if initial_steps:
                logger.info(f"Executing {len(initial_steps)} initial steps (before loops)...")
                initial_result = self._execute_steps(initial_steps)
                if not initial_result.get('success', False):
                    logger.warning("Initial steps failed, but continuing...")
            
            # Execute loops if defined
            if loops:
                logger.info("Executing loops...")
                result = self._execute_loops()
                
                # Aggregate all extracted data from context
                extracted_items = []
                for step_id, data in self.context.get('data', {}).items():
                    if isinstance(data, list):
                        extracted_items.extend(data)
                    elif data:  # Single value
                        extracted_items.append(data)
                
                # Add context with extracted items to result
                result['context'] = {
                    'extracted_items': extracted_items,
                    'data': self.context.get('data', {}),
                    'variables': self.context.get('variables', {})
                }
                
                logger.info(f"Aggregated {len(extracted_items)} extracted items from context")
                return result
            
            # Execute steps directly if no loops
            if all_steps and not loops:
                logger.info(f"Executing {len(all_steps)} steps...")
                result = self._execute_steps(all_steps)
                logger.info(f"Steps execution completed. Success: {result.get('success')}")
                
                # Aggregate all extracted data from context
                extracted_items = []
                for step_id, data in self.context.get('data', {}).items():
                    if isinstance(data, list):
                        extracted_items.extend(data)
                    elif data:  # Single value
                        extracted_items.append(data)
                
                # Add context with extracted items to result
                result['context'] = {
                    'extracted_items': extracted_items,
                    'data': self.context.get('data', {}),
                    'variables': self.context.get('variables', {})
                }
                
                logger.info(f"Aggregated {len(extracted_items)} extracted items from context")
                return result
            
            logger.error("No steps or loops defined in action")
            return {'success': False, 'error': 'No steps or loops defined'}
            
        except Exception as e:
            logger.error(f"Error executing action: {e}", exc_info=True)
            import traceback
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            return {'success': False, 'error': str(e)}
    
    def _execute_loops(self) -> Dict[str, Any]:
        """Execute action loops."""
        results = {'success': True, 'iterations': []}
        
        # If saved_item is provided directly, execute steps without loop
        if self.saved_item:
            # Execute steps directly (single item execution)
            steps = self.action_def.get('steps', [])
            return self._execute_steps(steps)
        
        for loop_def in self.action_def.get('loops', []):
            loop_id = loop_def.get('id')
            iterator_path = loop_def.get('iterator')
            index_var = loop_def.get('indexVar', 'reachedIndex')
            step_ids = loop_def.get('steps', [])
            
            # #region agent log
            import json
            from datetime import datetime
            with open('/Users/morteza/Desktop/monoes/mono-agent/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"timestamp": datetime.now().timestamp() * 1000, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "action_executor.py:161", "message": f"_execute_loops: Starting loop {loop_id}", "data": {"iterator_path": iterator_path, "step_ids": step_ids}}) + '\n')
            # #endregion
            
            # Get iterator collection
            print(f"\n🔍 Resolving iterator '{iterator_path}' for loop '{loop_id}'...")
            logger.debug(f"Available variables in context: {list(self.context.get('variables', {}).keys())}")
            
            # Sync resolver context with executor variables before resolving iterator
            # Merge executor variables into resolver context
            resolver_vars = self.resolver.context.get('variables', {})
            resolver_vars.update(self.context['variables'])
            self.resolver.set_context({
                **self.resolver.context,
                'variables': resolver_vars
            })
            
            iterator = self.resolver._resolve_path(iterator_path)
            logger.debug(f"Iterator '{iterator_path}' resolved to: {type(iterator).__name__} = {iterator if not isinstance(iterator, list) else f'[list with {len(iterator)} items]'}")
            if not iterator or not isinstance(iterator, list):
                logger.warning(f"❌ Invalid iterator for loop {loop_id}: {iterator_path}")
                print(f"❌ ERROR: Could not find valid iterator '{iterator_path}' (got: {type(iterator).__name__})")
                # #region agent log
                with open('/Users/morteza/Desktop/monoes/mono-agent/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"timestamp": datetime.now().timestamp() * 1000, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "B", "location": "action_executor.py:168", "message": f"_execute_loops: Invalid iterator", "data": {"iterator_path": iterator_path, "iterator_type": type(iterator).__name__, "iterator_value": str(iterator)[:100]}}) + '\n')
                # #endregion
                continue

            print(f"✅ Found {len(iterator)} items to iterate over")
            
            # #region agent log
            with open('/Users/morteza/Desktop/monoes/mono-agent/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"timestamp": datetime.now().timestamp() * 1000, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "C", "location": "action_executor.py:171", "message": f"_execute_loops: Iterator resolved", "data": {"iterator_path": iterator_path, "iterator_count": len(iterator) if isinstance(iterator, list) else 0}}) + '\n')
            # #endregion
            
            # Find steps to execute
            steps_to_execute = self._get_steps_by_ids(step_ids)
            
            # Execute loop
            total_items = len(iterator)
            print(f"\n{'='*60}")
            print(f"🔄 LOOP: '{loop_id}'")
            print(f"{'='*60}")
            print(f"📊 Total items to process: {total_items}")
            print(f"{'='*60}\n")

            for index, item in enumerate(iterator):
                # #region agent log
                with open('/Users/morteza/Desktop/monoes/mono-agent/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"timestamp": datetime.now().timestamp() * 1000, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "D", "location": "action_executor.py:177", "message": f"_execute_loops: Processing iteration {index}", "data": {"index": index, "item": str(item)[:200]}}) + '\n')
                # #endregion

                # Print progress with clear visual markers
                print(f"\n{'─'*60}")
                print(f"📍 ITEM {index + 1}/{total_items}: {str(item)[:80]}")
                print(f"{'─'*60}")

                # Update context with current item
                # Handle both dict and object items
                if isinstance(item, str):
                    # Item is already a string (URL), use it directly
                    self.resolver.add_to_context('item', item)
                    logger.debug(f"Loop item (string URL): {item}")
                elif isinstance(item, dict):
                    self.resolver.add_to_context('item', item)
                    # Also set item directly as string if it's a URL
                    if 'url' in item:
                        self.resolver.add_to_context('item', item['url'])
                    elif len(item) == 1 and isinstance(list(item.values())[0], str):
                        # If dict has single string value, use that
                        self.resolver.add_to_context('item', list(item.values())[0])
                else:
                    # Convert object to dict for resolver
                    item_dict = {
                        'url': getattr(item, 'url', ''),
                        'id': getattr(item, 'id', ''),
                        'platform_username': getattr(item, 'platform_username', ''),
                        'full_name': getattr(item, 'full_name', ''),
                    }
                    if hasattr(item, 'variables'):
                        item_dict.update(item.variables)
                    # If item has a url attribute, use that as the direct item value
                    if hasattr(item, 'url') and item.url:
                        self.resolver.add_to_context('item', item.url)
                    else:
                        self.resolver.add_to_context('item', item_dict)
                
                self.context['variables'][index_var] = index
                
                # Execute steps for this iteration
                iteration_result = self._execute_steps(steps_to_execute)
                results['iterations'].append({
                    'index': index,
                    'item': item,
                    'result': iteration_result
                })
                
                # Check if we should break
                if not iteration_result.get('success', False):
                    if iteration_result.get('abort', False):
                        break
            
            # Handle onComplete
            on_complete = loop_def.get('onComplete')
            if on_complete:
                self._handle_completion_action(on_complete)
        
        return results
    
    def _execute_steps(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute a list of steps."""
        results = {'success': True, 'steps': []}
        
        logger.info(f"Executing {len(steps)} steps...")
        
        for idx, step_def in enumerate(steps):
            step_id = step_def.get('id', f'step_{idx}')
            step_type = step_def.get('type', 'unknown')
            
            logger.info(f"[{idx+1}/{len(steps)}] Executing step: {step_id} (type: {step_type})")
            
            try:
                # Sync resolver context with executor variables before resolving
                self.resolver.set_context({
                    **self.resolver.context,
                    'variables': self.context.get('variables', {})
                })
                
                # Resolve variables in step definition
                logger.debug(f"Step {step_id}: Resolving variables...")
                resolved_step = self.resolver.resolve_dict(deepcopy(step_def))
                logger.info(f"Step {step_id} (resolved type: {resolved_step.get('type')}) starting...")
                
                # Execute step
                step_result = self._execute_step(resolved_step)
                
                print(f"✅ Step {step_id} executed. Success: {step_result.get('success')}")
                if 'data' in step_result:
                    data_preview = str(step_result['data'])[:200]
                    print(f"📊 Step {step_id} data preview: {data_preview}")
                
                logger.info(f"Step {step_id} result: success={step_result.get('success')}")
                
                # Store step result in context for condition evaluation
                self.context['step_results'][step_id] = step_result
                
                results['steps'].append({
                    'id': step_id,
                    'type': step_type,
                    'success': step_result.get('success', False),
                    'result': step_result
                })
                
                # Store element if found
                if 'element' in step_result:
                    self.context['elements'][step_id] = step_result['element']

                
                # Store data if extracted
                if 'data' in step_result:
                    self.context['data'][step_id] = step_result['data']
                
                # Store step result for condition evaluation
                self.context['step_results'][step_id] = {
                    'success': step_result.get('success', False),
                    'result': step_result
                }
                
                # Handle step-level error
                if not step_result.get('success', False):
                    error_handler = step_def.get('onError')
                    if error_handler:
                        logger.info(f"Step {step_id} failed. Handling with: {error_handler.get('action')}")
                        error_result = self.error_handler.handle_step_error(
                            error_handler, step_result, self.bot, self.context
                        )
                        if error_result.get('abort', False):
                            logger.error(f"Step {step_id} failed and error handler chose to ABORT.")
                            results['success'] = False
                            results['abort'] = True
                            break
                        elif error_result.get('skip', False):
                            logger.info(f"Step {step_id} failed and error handler chose to SKIP.")
                            continue
                    else:
                        logger.error(f"Step {step_id} failed and no error handler provided. BREAKING.")
                        results['success'] = False
                        break
                
                # Handle step-level success
                success_handler = step_def.get('onSuccess')
                if success_handler and step_result.get('success', False):
                    self._handle_success_action(success_handler)
                
            except Exception as e:
                logger.error(f"CRITICAL ERROR executing step {step_id}: {e}")
                logger.error(traceback.format_exc())
                print(f"❌ CRITICAL ERROR in step {step_id}: {e}")
                
                results['steps'].append({
                    'id': step_id,
                    'type': step_type,
                    'success': False,
                    'error': str(e)
                })
                results['success'] = False
                
                # Try error handler
                error_handler = step_def.get('onError')
                if error_handler:
                    error_result = self.error_handler.handle_step_error(
                        error_handler, {'success': False, 'error': str(e)},
                        self.bot, self.context
                    )
                    if error_result.get('abort', False):
                        break

        
        return results
    
    def _execute_step(self, step_def: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single step."""
        step_type = step_def.get('type', '')
        step_id = step_def.get('id', '')
        
        logger.debug(f"Executing step handler for type: {step_type}")
        
        # Route to appropriate step handler
        handlers = {
            'navigate': self._step_navigate,
            'wait': self._step_wait,
            'refresh': self._step_refresh,
            'find_element': self._step_find_element,
            'click': self._step_click,
            'type': self._step_type,
            'scroll': self._step_scroll,
            'hover': self._step_hover,
            'extract_text': self._step_extract_text,
            'extract_attribute': self._step_extract_attribute,
            'extract_multiple': self._step_extract_multiple,
            'condition': self._step_condition,
            'update_progress': self._step_update_progress,
            'save_data': self._step_save_data,
            'mark_failed': self._step_mark_failed,
            'log': self._step_log,
            'call_bot_method': self._step_call_bot_method
        }
        
        handler = handlers.get(step_type)
        if not handler:
            logger.error(f"Unknown step type: {step_type} for step {step_id}")
            logger.error(f"Available handlers: {list(handlers.keys())}")
            return {'success': False, 'error': f'Unknown step type: {step_type}'}
        
        logger.debug(f"Calling handler for {step_type}...")
        result = handler(step_def)
        logger.debug(f"Handler returned: {result}")
        return result
    
    def _get_steps_by_ids(self, step_ids: List[str]) -> List[Dict[str, Any]]:
        """Get step definitions by their IDs."""
        all_steps = self.action_def.get('steps', [])
        step_map = {step.get('id'): step for step in all_steps}
        return [step_map[sid] for sid in step_ids if sid in step_map]
    
    # Step handlers
    
    def _step_navigate(self, step_def: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate to URL."""
        url_template = step_def.get('url', '')
        timeout = step_def.get('timeout', 30)
        wait_for = step_def.get('waitFor', 'page_load')
        
        # Resolve variables in URL - check both resolver and context variables
        url = url_template
        
        # First try resolver (for action properties)
        url = self.resolver.resolve(url_template)
        
        # If resolver returned None or empty, try direct lookup
        if not url or url == 'None':
            # Check if it's a simple variable reference like {{item}}
            import re
            var_match = re.match(r'^\{\{([^}]+)\}\}$', url_template)
            if var_match:
                var_path = var_match.group(1).strip()
                # Try direct lookup in resolver context
                direct_value = self.resolver._resolve_path(var_path)
                if direct_value:
                    url = str(direct_value)
                else:
                    # Try in executor variables
                    url = str(self.context.get('variables', {}).get(var_path, ''))
        
        # Then check context variables (for executor-managed variables like searchUrl)
        if '{{' in url:
            # Replace any remaining variables from context
            for var_name, var_value in self.context.get('variables', {}).items():
                placeholder = f"{{{{{var_name}}}}}"
                if placeholder in url:
                    url = url.replace(placeholder, str(var_value))
        
        # Validate URL before navigation
        if not url or url.strip() == '' or url == 'None':
            error_msg = f"Invalid or empty URL resolved from template: {url_template}"
            logger.error(error_msg)
            print(f"❌ NAVIGATION ERROR: {error_msg}")
            print(f"   Template: {url_template}")
            print(f"   Resolved: {url}")
            print(f"   Available variables: {list(self.resolver.context.keys())}")
            if 'item' in self.resolver.context:
                print(f"   Item value: {self.resolver.context['item']}")
            return {'success': False, 'error': error_msg}
        
        # Ensure URL is properly formatted
        url = url.strip()
        if not url.startswith('http://') and not url.startswith('https://'):
            # If it's a relative URL, make it absolute to Instagram
            if url.startswith('/'):
                url = f"https://www.instagram.com{url}"
            else:
                url = f"https://www.instagram.com/{url}"
        
        # Extract username from URL for later use (if it's an Instagram profile URL)
        if 'instagram.com/' in url and '/p/' not in url and '/explore/' not in url:
            # Extract username from URL (e.g., https://www.instagram.com/username/ -> username)
            url_parts = url.rstrip('/').split('/')
            if len(url_parts) > 0:
                potential_username = url_parts[-1]
                # Only set if it looks like a username (not a page like 'home', 'explore', etc.)
                if potential_username and potential_username not in ['home', 'explore', 'reels', 'direct', 'accounts', 'accounts', '']:
                    self.context['variables']['username'] = potential_username
                    self.resolver.add_to_context('username', potential_username)
        
        # Log the final URL for debugging
        logger.debug(f"Final resolved URL: {url}")
        if url != url_template:
            print(f"   🔗 URL resolved: {url_template} → {url}")
        
        # URL encode search queries properly
        import urllib.parse
        if '?q=' in url or '&q=' in url:
            # Extract and encode the query parameter
            if '?q=' in url:
                parts = url.split('?q=', 1)
                if len(parts) == 2:
                    base_url = parts[0]
                    query_part = parts[1].split('&', 1)[0]  # Get query value before any other params
                    # Only encode if it's not already encoded
                    if '%' not in query_part:
                        encoded_query = urllib.parse.quote(query_part)
                        url = f"{base_url}?q={encoded_query}"
                        if '&' in parts[1]:
                            url += '&' + parts[1].split('&', 1)[1]  # Add remaining params
        
        try:
            logger.info(f"Navigating to: {url}")
            self.bot.driver.get(url)
            self.bot.driver.implicitly_wait(4)
            
            # Update current_url in resolver and context
            try:
                current_url = self.bot.driver.current_url
                self.resolver.add_to_context('current_url', current_url)
                self.context['variables']['current_url'] = current_url
                logger.info(f"Current URL after navigation: {current_url}")
            except:
                pass
            
            if wait_for == 'page_load':
                # Wait for page to load
                time.sleep(Attrs.sleep_config.get('page_load', 3))
            
            return {'success': True}
        except Exception as e:
            logger.error(f"Navigation error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _step_wait(self, step_def: Dict[str, Any]) -> Dict[str, Any]:
        """Wait for condition."""
        duration = step_def.get('duration', 1.0)
        wait_for = step_def.get('waitFor', 'time')
        
        try:
            if wait_for == 'time':
                time.sleep(duration)
            elif wait_for == 'element_visible':
                element_ref = step_def.get('elementRef')
                timeout = step_def.get('timeout', 10)
                element = self._get_element(element_ref)
                if element:
                    WebDriverWait(self.bot.driver, timeout).until(
                        EC.visibility_of(element)
                    )
            
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _step_refresh(self, step_def: Dict[str, Any]) -> Dict[str, Any]:
        """Refresh page."""
        try:
            self.bot.driver.refresh()
            self.bot.driver.implicitly_wait(4)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _step_find_element(self, step_def: Dict[str, Any]) -> Dict[str, Any]:
        """Find element using config or XPath."""
        config_key = step_def.get('configKey')
        xpath = step_def.get('xpath')
        timeout = step_def.get('timeout', 20)
        wait_for = step_def.get('waitFor', 'element_visible')
        alternatives = step_def.get('alternatives', [])
        variable_name = step_def.get('variable_name')
        
        # Try to get XPath from config
        config = None
        if config_key:
            platform = getattr(self.action, 'source', '').lower()
            action_name, config_context, schema = self._get_config_params()

            config = self.config_manager.get_config(
                social=platform,
                action=action_name,
                config_context=config_context,
                html_content=self.bot.driver.page_source,
                purpose=f"Find {config_key}",
                schema=schema
            )
            
            if config:
                xpath = ConfigHelper.get_xpath(config, config_key)
        
        # Try alternatives if main XPath fails
        xpaths_to_try = [xpath] if xpath else []
        if alternatives:
            # Resolve alternative config keys or use as raw XPaths
            for alt_key in alternatives:
                if config_key and config:
                    # Try to resolve as a config key first
                    alt_xpath = ConfigHelper.get_xpath(config, alt_key)
                    if alt_xpath:
                        xpaths_to_try.append(alt_xpath)
                        continue
                
                # If no config or not a config key, use as raw XPath
                xpaths_to_try.append(alt_key)
        
        variable_name = step_def.get('variable_name')
        
        # Try each XPath
        for xpath_to_try in xpaths_to_try:
            if not xpath_to_try:
                continue
            
            try:
                # Convert to list format for legacy compatibility
                xpath_list = [xpath_to_try] if isinstance(xpath_to_try, str) else xpath_to_try
                element = self.bot.find_element(xpath_list, timeout=timeout)
                
                if element:
                    if variable_name:
                        self.context['variables'][variable_name] = element
                    return {'success': True, 'element': element}
            except Exception:
                continue
        
        # If element not found, still initialize variable to None if it's a variable_name
        if variable_name:
            self.context['variables'][variable_name] = None
            
        return {'success': False, 'error': 'Element not found'}
    
    def _step_click(self, step_def: Dict[str, Any]) -> Dict[str, Any]:
        """Click element."""
        element_ref = step_def.get('elementRef')
        wait_for = step_def.get('waitFor')
        timeout = step_def.get('timeout', 10)
        
        element = self._get_element(element_ref)
        if not element:
            return {'success': False, 'error': f'Element not found: {element_ref}'}
        
        try:
            # Use bot's click method if available, otherwise direct click
            if hasattr(self.bot, 'find_element_clickable'):
                self.bot.find_element_clickable(element_ref, timeout=timeout)
            else:
                element.click()
            
            # Wait for condition if specified
            if wait_for:
                time.sleep(Attrs.sleep_config['action_min'])
            
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _step_type(self, step_def: Dict[str, Any]) -> Dict[str, Any]:
        """Type text into element."""
        element_ref = step_def.get('elementRef')
        text = step_def.get('text', '')
        human_like = step_def.get('humanLike', False)
        
        element = self._get_element(element_ref)
        if not element:
            # Try to find by config key
            config_key = step_def.get('configKey')
            if config_key:
                find_result = self._step_find_element({
                    'configKey': config_key,
                    'timeout': 10
                })
                if find_result.get('success'):
                    element = find_result.get('element')
        
        if not element:
            return {'success': False, 'error': f'Element not found: {element_ref}'}
        
        try:
            if human_like and hasattr(self.bot, 'write_like_human'):
                self.bot.write_like_human(element, text)
            else:
                element.clear()
                element.send_keys(text)
            
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _step_scroll(self, step_def: Dict[str, Any]) -> Dict[str, Any]:
        """Scroll to element or scroll page."""
        element_ref = step_def.get('elementRef')
        scroll_type = step_def.get('scrollType', 'element')
        direction = step_def.get('direction', 'down')
        
        try:
            if scroll_type == 'page':
                # Scroll the page itself
                if direction == 'down':
                    self.bot.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                elif direction == 'up':
                    self.bot.driver.execute_script("window.scrollTo(0, 0);")
                else:
                    self.bot.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(Attrs.sleep_config['action_min'])
                return {'success': True}
            else:
                # Scroll to element (original behavior)
                element = self._get_element(element_ref)
                if not element:
                    return {'success': False, 'error': f'Element not found: {element_ref}'}
                
                self.bot.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(Attrs.sleep_config['action_min'])
                return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _step_hover(self, step_def: Dict[str, Any]) -> Dict[str, Any]:
        """Hover over element."""
        element_ref = step_def.get('elementRef')
        
        element = self._get_element(element_ref)
        if not element:
            return {'success': False, 'error': f'Element not found: {element_ref}'}
        
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            ActionChains(self.bot.driver).move_to_element(element).perform()
            time.sleep(Attrs.sleep_config['action_min'])
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _step_extract_text(self, step_def: Dict[str, Any]) -> Dict[str, Any]:
        """Extract text from element."""
        variable_name = step_def.get('variable_name')
        element_ref = step_def.get('elementRef')
        config_key = step_def.get('configKey')
        step_id = step_def.get('id', 'extract_text')
        timeout = step_def.get('timeout', 10)
        attribute = step_def.get('attribute', '')
        
        element = self._get_element(element_ref)
        if not element and config_key:
            # Try to find element using config
            platform = getattr(self.action, 'source', 'INSTAGRAM').upper()
            action_name, config_context, schema = self._get_config_params()
            
            config = self.config_manager.get_config(
                social=platform,
                action=action_name,
                config_context=config_context,
                html_content=self.bot.driver.page_source if hasattr(self.bot, 'driver') and self.bot.driver else "",
                purpose=f"Extract text {config_key}",
                schema=schema
            )
            
            if config:
                xpath = ConfigHelper.get_xpath(config, config_key)
                if xpath:
                    # Check if xpath ends with attribute selector (e.g., /@href, /@src, /@alt)
                    import re
                    attr_match = re.search(r'/@(\w+)$', xpath)
                    if attr_match:
                        # Strip attribute selector and use it for extraction
                        attribute = attr_match.group(1)
                        xpath = xpath[:attr_match.start()]
                        logger.info(f"extract_text: Detected attribute XPath, using element xpath: {xpath}, attribute: {attribute}")
                    
                    try:
                        from selenium.webdriver.common.by import By
                        from selenium.webdriver.support.ui import WebDriverWait
                        from selenium.webdriver.support import expected_conditions as EC
                        
                        if timeout > 0:
                            element = WebDriverWait(self.bot.driver, timeout).until(
                                EC.presence_of_element_located((By.XPATH, xpath))
                            )
                        else:
                            element = self.bot.driver.find_element(By.XPATH, xpath)
                    except Exception as e:
                        logger.warning(f"extract_text: XPath '{xpath}' failed: {e}")
                        self.context['data'][step_id] = ''
                        return {'success': False, 'error': f'Element not found: {xpath}', 'data': ''}
            
            # Fallback to find_element step
            if not element:
                find_result = self._step_find_element(step_def)
                if find_result.get('success'):
                    element = find_result.get('element')
        
        if not element:
            error_msg = f'Element not found: {element_ref or config_key}'
            self.context['data'][step_id] = ''
            return {'success': False, 'error': error_msg, 'data': ''}
        
        try:
            # If attribute is specified, get attribute value; otherwise get text
            if attribute:
                value = element.get_attribute(attribute)
            else:
                value = element.text
            
            print(f"✅ extract_text: Extracted value: '{value}'")
            self.context['data'][step_id] = value or ''
            self.context['variables'][f'{step_id}.data'] = value or ''
            if variable_name:
                self.context['variables'][variable_name] = value or ''
            return {'success': True, 'data': value or ''}
        except Exception as e:
            self.context['data'][step_id] = ''
            if variable_name:
                self.context['variables'][variable_name] = ''
            return {'success': False, 'error': str(e), 'data': ''}
    
    def _step_extract_attribute(self, step_def: Dict[str, Any]) -> Dict[str, Any]:
        """Extract an attribute from an element."""
        variable_name = step_def.get('variable_name')
        element_ref = step_def.get('element')
        config_key = step_def.get('configKey')
        attribute = step_def.get('attribute')
        step_id = step_def.get('id', 'extract_attribute')
        
        element = None
        if element_ref:
            element = self.context['elements'].get(element_ref)
        
        if not element and config_key:
            # Try to get xpath from config
            platform = getattr(self.action, 'source', 'INSTAGRAM').upper()
            action_name, config_context, schema = self._get_config_params()
            
            print(f"🔍 Requesting config: platform={platform}, action={action_name}, context={config_context}")
            config = self.config_manager.get_config(
                social=platform,
                action=action_name,
                config_context=config_context,
                html_content=self.bot.driver.page_source,
                purpose=f"Extract attribute {config_key}",
                schema=schema
            )
            
            if config:
                xpath = ConfigHelper.get_xpath(config, config_key)
                if xpath:
                    # Check if xpath ends with attribute selector (e.g., /@href, /@src)
                    attr_match = re.search(r'/@(\w+)$', xpath)
                    if attr_match:
                        # Extract attribute directly using JavaScript evaluate for better reliability
                        found_attr = attr_match.group(1)
                        xpath_no_attr = xpath[:attr_match.start()]
                        logger.info(f"extract_attribute: Detected attribute XPath: {xpath}")
                        print(f"🔍 extract_attribute: Stripped XPath: {xpath_no_attr}, Attribute: {found_attr}")
                        
                        try:
                            # Try to find element first
                            from selenium.webdriver.common.by import By
                            element = self.bot.driver.find_element(By.XPATH, xpath_no_attr)
                            attribute = found_attr
                            print(f"✅ extract_attribute: Found element using stripped config XPath: {xpath_no_attr}")
                        except Exception as e:
                            print(f"⚠️ extract_attribute: Element not found with stripped XPath: {e}")
                            # If element not found, try direct evaluation via JS
                            try:
                                js_script = f"return document.evaluate(\"{xpath}\", document, null, XPathResult.STRING_TYPE, null).stringValue;"
                                value = self.bot.driver.execute_script(js_script)
                                if value:
                                    print(f"✅ extract_attribute: Evaluated XPath directly via JS: {value}")
                                    # Resolve relative URLs
                                    if value and value.startswith('/') and not value.startswith('//'):
                                        value = f"https://www.instagram.com{value}"
                                    
                                    self.context['data'][step_id] = value
                                    self.context['variables'][f'{step_id}.data'] = value
                                    return {'success': True, 'data': value}
                                else:
                                    print(f"❌ extract_attribute: JS evaluation returned empty/null")
                            except Exception as js_err:
                                logger.warning(f"JS evaluation failed: {js_err}")
                                print(f"❌ extract_attribute: JS Error: {js_err}")
                    else:
                        try:
                            from selenium.webdriver.common.by import By
                            element = self.bot.driver.find_element(By.XPATH, xpath)
                            print(f"✅ extract_attribute: Found element using raw config XPath: {xpath}")
                        except Exception as e:
                            logger.warning(f"XPath '{xpath}' failed: {e}")
                            print(f"❌ extract_attribute: Raw XPath failure: {e}")


        
        if not element:
            # Fallback to normal find element logic
            find_result = self._step_find_element(step_def)
            if find_result.get('success'):
                element = find_result.get('element')
                print(f"✅ extract_attribute: Found element via fallback _step_find_element")
        
        if not element:
            error_msg = f'Element not found: {element_ref or config_key}'
            print(f"❌ extract_attribute: {error_msg}")
            # Save page source for debugging
            try:
                debug_path = os.path.join(os.getcwd(), f"debug_extract_fail_{step_id}.html")
                with open(debug_path, "w", encoding="utf-8") as f:
                    f.write(self.bot.driver.page_source)
                print(f"📄 Saved page source for debugging to: {debug_path}")
                
                # Also print a small part of the HTML to the terminal for immediate feedback
                header_html = self.bot.driver.execute_script("return document.querySelector('header') ? document.querySelector('header').outerHTML : 'Header not found';")
                print(f"📄 Header HTML snippet: {header_html[:500]}...")
            except Exception as save_err:
                print(f"⚠️ Failed to save debug page source or get header snippet: {save_err}")
            
            self.context['data'][step_id] = ''
            return {'success': False, 'error': error_msg, 'data': ''}
        
        try:
            print(f"🔍 extract_attribute: Found element, extracting '{attribute}'")
            value = element.get_attribute(attribute)
            
            # Fallback to text if attribute is missing (especially useful for websites in buttons)
            if not value and (attribute == 'href' or attribute == 'src'):
                try:
                    text_fallback = element.text
                    if text_fallback:
                        print(f"ℹ️ extract_attribute: Attribute '{attribute}' empty, falling back to text: '{text_fallback}'")
                        value = text_fallback
                except:
                    pass
            
            # Resolve relative URLs
            if value and value.startswith('/') and not value.startswith('//'):
                base_url = "https://www.instagram.com"
                value = f"{base_url}{value}"
                print(f"🔗 extract_attribute: Resolved relative URL to: {value}")
            
            print(f"✅ extract_attribute: Extracted value: '{value}'")
            self.context['data'][step_id] = value or ''
            self.context['variables'][f'{step_id}.data'] = value or ''
            if variable_name:
                self.context['variables'][variable_name] = value or ''
            return {'success': True, 'data': value or ''}
        except Exception as e:
            print(f"❌ extract_attribute: Error: {e}")
            self.context['data'][step_id] = ''
            if variable_name:
                self.context['variables'][variable_name] = ''
            return {'success': False, 'error': str(e), 'data': ''}
    
    def _step_extract_multiple(self, step_def: Dict[str, Any]) -> Dict[str, Any]:
        """Extract multiple values."""
        config_key = step_def.get('configKey')
        xpath = step_def.get('xpath')
        attribute = step_def.get('attribute')
        timeout = step_def.get('timeout', 10)
        step_id = step_def.get('id', 'extract_multiple')
        alternatives = step_def.get('alternatives', [])

        try:
            # If xpath is provided, use it directly
            if xpath:
                # Try to find elements - if timeout is specified, wait a bit, but don't fail if none found
                elements = []
                if timeout > 0:
                    try:
                        # Wait for at least one element to appear
                        WebDriverWait(self.bot.driver, min(timeout, 5)).until(
                            lambda d: len(d.find_elements(By.XPATH, xpath)) > 0
                        )
                    except TimeoutException:
                        # If no elements found, that's okay - return empty list
                        logger.info(f"No elements found with xpath {xpath} after waiting, continuing with empty list")
                
                elements = self.bot.driver.find_elements(By.XPATH, xpath)
            elif config_key:
                  # Get platform from action object
                platform = getattr(self.action, 'source', 'INSTAGRAM').upper()
        
                # Determine action name and context based on action type
                action_name, config_context, schema = self._get_config_params()

                # Skip config lookup for HOME_PAGE context - use alternatives directly
                if config_context and 'HOME_PAGE' in config_context.upper():
                    print(f"⚠️  Skipping config lookup for HOME_PAGE context, using alternatives")
                    config = None
                else:
                    print(f"🔍 Requesting config: platform={platform}, action={action_name}, context={config_context}")
                    config = self.config_manager.get_config(
                        social=platform,
                        action=action_name,
                        config_context=config_context,
                        html_content=self.bot.driver.page_source,
                        purpose=f"Extract {config_key}",
                        schema=schema
                    )

                if config:
                    print(f"✅ Config loaded successfully")
                    xpath = ConfigHelper.get_xpath(config, config_key)
                    if xpath:
                        # Check if xpath ends with attribute selector (e.g., /@href, /@src)
                        import re
                        attr_match = re.search(r'/@(\w+)$', xpath)
                        if attr_match:
                            # Strip attribute selector and use it for extraction
                            attribute = attr_match.group(1)
                            xpath = xpath[:attr_match.start()]
                        
                        try:
                            elements = self.bot.driver.find_elements(By.XPATH, xpath)
                        except Exception as e:
                            xpath = None  # Mark as failed to trigger alternatives
                            elements = []
                    else:
                        logger.warning(f'XPath not found for {config_key}, trying alternatives')
                        xpath = None  # Will try alternatives below
                else:
                    logger.warning(f'Config not found for {config_key}, trying alternatives')
                    xpath = None  # Will try alternatives below

            # Try alternatives if config-based xpath didn't work
            if not xpath and alternatives:
                logger.info(f"Trying {len(alternatives)} alternative XPaths")
                for alt_xpath in alternatives:
                    try:
                        print(f"🔍 Trying alternative XPath: {alt_xpath}")
                        elements = self.bot.driver.find_elements(By.XPATH, alt_xpath)
                        if elements:
                            xpath = alt_xpath
                            logger.info(f"Alternative XPath worked: {alt_xpath}, found {len(elements)} elements")
                            print(f"✅ Alternative XPath successful! Found {len(elements)} elements")
                            break
                    except Exception as e:
                        logger.debug(f"Alternative XPath {alt_xpath} failed: {e}")
                        continue

            if not xpath and not elements:
                return {'success': False, 'error': 'No xpath or configKey provided or alternatives failed'}

            # If we don't have elements yet (alternatives didn't run), return empty
            if not elements:
                logger.warning("No elements found, returning empty list")
                self.context['data'][step_id] = []
                self.context['variables'][f'{step_id}.count'] = 0
                self.context['variables'][f'{step_id}.data'] = []
                return {'success': True, 'data': [], 'count': 0}

            # Extract data from elements
            extracted_data = []
            seen_values = set()  # Deduplicate
            for element in elements:
                try:
                    if attribute:
                        value = element.get_attribute(attribute)
                    else:
                        value = element.text
                    if value and value not in seen_values:
                        extracted_data.append(value)
                        seen_values.add(value)
                except Exception:
                    continue
            
            # Store in context
            self.context['data'][step_id] = extracted_data

            # Also store in variables for condition evaluation
            self.context['variables'][f'{step_id}.count'] = len(extracted_data)
            self.context['variables'][f'{step_id}.data'] = extracted_data

            logger.info(f"✅ Extracted {len(extracted_data)} unique items from {len(elements)} elements (step: {step_id})")

            # Print progress for user visibility
            if step_id == 'extract_post_urls':
                print(f"📊 Collected {len(extracted_data)} post URLs so far...")

            return {'success': True, 'data': extracted_data, 'count': len(extracted_data)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _step_condition(self, step_def: Dict[str, Any]) -> Dict[str, Any]:
        """Conditional branching."""
        step_id = step_def.get('id', 'unknown_condition')
        condition = step_def.get('condition', '')
        then_steps = step_def.get('then', [])
        else_steps = step_def.get('else', [])

        # Check for recursion limit (to prevent infinite loops)
        recursion_count = self.context['recursion_counts'].get(step_id, 0)
        if recursion_count >= self.MAX_RECURSION_DEPTH:
            logger.warning(f"⚠️  RECURSION LIMIT REACHED for step '{step_id}' (depth: {recursion_count})")
            logger.warning(f"   Condition was: '{condition}'")
            logger.warning(f"   Breaking recursion to prevent infinite loop")
            print(f"⚠️  RECURSION LIMIT: Step '{step_id}' hit max depth of {recursion_count}. Stopping to prevent infinite loop.")
            return {'success': True, 'recursion_limited': True}

        # Increment recursion counter
        self.context['recursion_counts'][step_id] = recursion_count + 1

        # Evaluate condition (simplified - would need proper expression evaluator)
        condition_result = self._evaluate_condition(condition)

        # Log condition evaluation for debugging
        if recursion_count > 0:  # Only log recursive calls
            logger.info(f"🔄 Recursive condition '{step_id}' (iteration {recursion_count + 1}): '{condition}' = {condition_result}")
            if recursion_count % 5 == 0:  # Print progress every 5 iterations
                print(f"🔄 Scrolling to collect more posts... (attempt {recursion_count + 1}/{self.MAX_RECURSION_DEPTH})")

        steps_to_execute = then_steps if condition_result else else_steps
        if not steps_to_execute:
            # Reset recursion counter when exiting
            self.context['recursion_counts'][step_id] = 0
            return {'success': True}

        step_defs = self._get_steps_by_ids(steps_to_execute)

        result = self._execute_steps(step_defs)

        # Reset recursion counter after successful execution
        if not any(step_id in step.get('id', '') for step in step_defs if isinstance(step, dict)):
            # Only reset if we're not recursing
            self.context['recursion_counts'][step_id] = 0

        return result
    
    def _step_update_progress(self, step_def: Dict[str, Any]) -> Dict[str, Any]:
        """Update action progress."""
        increment = step_def.get('increment')
        set_vars = step_def.get('set', {})

        # Update context variables
        if increment:
            current = self.context['variables'].get(increment, 0)
            self.context['variables'][increment] = current + 1

        # Sync resolver context with executor variables before resolving
        # This ensures the resolver can access variables stored in self.context['variables']
        # Merge executor variables into resolver context
        resolver_vars = self.resolver.context.get('variables', {})
        resolver_vars.update(self.context['variables'])
        self.resolver.set_context({
            **self.resolver.context,
            'variables': resolver_vars
        })
        
        # Resolve variables in set_vars before storing
        for key, value in set_vars.items():
            # Resolve value if it's a string with variables
            if isinstance(value, str):
                # Check if the entire string is a single variable reference (e.g., "{{variable}}")
                # If so, preserve the original type instead of converting to string
                single_var_pattern = re.compile(r'^\{\{([^}]+)\}\}$')
                match = single_var_pattern.match(value)
                
                logger.info(f"update_progress: Processing key '{key}', value='{value}', match={match is not None}")

                if match:
                    # It's a single variable reference - get the original value
                    var_path = match.group(1).strip()
                    resolved_value = self.resolver._resolve_path(var_path)
                    logger.info(f"update_progress: Setting '{key}' = {type(resolved_value).__name__} (from variable path '{var_path}')")
                    if isinstance(resolved_value, list):
                        logger.info(f"  List contains {len(resolved_value)} items")
                        print(f"✅ Storing '{key}' as list with {len(resolved_value)} items")
                    elif resolved_value is None:
                        logger.warning(f"  Variable path '{var_path}' resolved to None")
                        print(f"⚠️  Variable path '{var_path}' resolved to None")
                    else:
                        logger.info(f"  Value type: {type(resolved_value).__name__}, value preview: {str(resolved_value)[:100]}")
                        print(f"⚠️  Storing '{key}' as {type(resolved_value).__name__}: {str(resolved_value)[:100]}")
                    self.context['variables'][key] = resolved_value
                    # Update resolver context with the new variable
                    self.resolver.add_to_context(key, resolved_value)
                else:
                    # It's a template with text or multiple variables - resolve as string
                    resolved_value = self.resolver.resolve(value)
                    logger.debug(f"update_progress: Setting '{key}' = str (from template '{value[:50]}...')")
                    self.context['variables'][key] = resolved_value
                    # Update resolver context with the new variable
                    self.resolver.add_to_context(key, resolved_value)
            elif isinstance(value, dict):
                # Recursively resolve dict values
                resolved_dict = self.resolver.resolve_dict(value)
                self.context['variables'][key] = resolved_dict
            else:
                self.context['variables'][key] = value
        
        # Also store the resolved variables in self.context['data'] for the current step
        # This allows other steps to use this step as a dataSource (e.g., in save_data)
        step_id = step_def.get('id', 'update_progress')
        self.context['data'][step_id] = self.context['variables'].copy()
        
        return {'success': True}
    
    def _step_save_data(self, step_def: Dict[str, Any]) -> Dict[str, Any]:
        """Save extracted data."""
        try:
            # #region agent log
            # #endregion
            
            # Get data source - could be from a specific step or all context data
            data_source = step_def.get('dataSource')  # Optional: specific step ID
            batch_size = step_def.get('batchSize', 10)  # Default batch size
            
            # Use provided api_client or fallback to RestAPI
            api_client = self.api_client
            if not api_client:
                from newAgent.src.api.APIs import RestAPI
                api_client = RestAPI

            # Get data from specific data source if provided
            if data_source:
                data_to_save = self.context.get('data', {}).get(data_source, [])
                # If it's a single dictionary (not a list), wrap it in a list
                if isinstance(data_to_save, dict):
                    data_to_save = [data_to_save]
                logger.info(f"_step_save_data: Got data from dataSource '{data_source}': {len(data_to_save) if isinstance(data_to_save, list) else 1} items")
            else:
                # Collect all extracted data from current iteration
                all_data = self.context.get('data', {})
                # Find the most recent extraction (usually the last non-empty data)
                data_to_save = []
                for key, value in all_data.items():
                    if isinstance(value, list) and value:
                        data_to_save = value
                        break
                    elif value and not isinstance(value, (dict, list)):
                        # Single value, convert to list format
                        data_to_save = [value]
            
            # Also check variables for profile data
            if not data_to_save:
                profile_data = self.context.get('variables', {}).get('profileData')
                if profile_data:
                    data_to_save = [profile_data]
            
            # #region agent log
            # #endregion
            
            # Format data for API (platform-specific formatting)
            if data_to_save:
                formatted_data = self._format_data_for_api(data_to_save)
                
                # Save to context for batch saving
                self.context['extracted_items'].extend(formatted_data)
                
                # Flush as many batches as possible
                while len(self.context['extracted_items']) >= batch_size and api_client:
                    try:
                        batch = self.context['extracted_items'][:batch_size]
                        # #region agent log
                        # #endregion
                        response = api_client.create_people(batch)
                        
                        # Check for success
                        is_success = False
                        status_code = getattr(response, 'status_code', 200)
                        
                        if hasattr(response, 'status_code'):
                            is_success = response.status_code < 400
                        elif isinstance(response, dict):
                            is_success = response.get('success', True)
                        else:
                            is_success = True
                            
                        if is_success:
                            self.context['extracted_items'] = self.context['extracted_items'][batch_size:]
                            logger.info(f"✅ Successfully saved batch of {len(batch)} items via API (Status: {status_code})")
                        else:
                            logger.error(f"❌ Failed to save batch of {len(batch)} items. API returned status {status_code}. Keeping remaining {len(self.context['extracted_items'])} items for retry.")
                            break # Stop flushing on failure
                    except Exception as api_err:
                        logger.error(f"❌ Error saving data via API: {api_err}. Keeping items for retry.")
                        break # Stop flushing on error
            
            return {'success': True, 'saved_count': len(self.context.get('extracted_items', []))}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _format_data_for_api(self, data: List[Any]) -> List[Dict[str, Any]]:
        """Format extracted data for API submission."""
        formatted = []
        platform = getattr(self.action, 'source', '').upper()
        
        def sanitize(val):
            """Sanitize values for JSON serialization."""
            if hasattr(val, 'id') and hasattr(val, 'tag_name'): # Likely a WebElement
                return True
            if isinstance(val, dict):
                return {k: sanitize(v) for k, v in val.items()}
            if isinstance(val, list):
                return [sanitize(v) for v in val]
            return val

        for item in data:
            if isinstance(item, dict):
                # Check if it's already a well-formed profile dict
                if 'platform' in item and ('url' in item or 'platform_username' in item):
                    formatted.append(sanitize(item))
                else:
                    # It's a dict with data, but maybe needs structure
                    # If it contains 'profileData', it's likely the actual data wrapped
                    if 'profileData' in item and isinstance(item['profileData'], dict):
                        data_fields = item['profileData']
                    else:
                        # Use the item itself, but filter out control keys
                        data_fields = {k: v for k, v in item.items() if k not in ['configContext']}
                    
                    formatted.append({
                        'platform': platform or 'INSTAGRAM',
                        **sanitize(data_fields)
                    })
            elif isinstance(item, str):
                # URL or simple string - create basic structure
                formatted.append({
                    'platform': platform or 'INSTAGRAM',
                    'url': item if item.startswith('http') else '',
                    'platform_username': item if not item.startswith('http') else ''
                })
            else:
                # Try to extract useful info
                formatted.append({
                    'platform': platform or 'INSTAGRAM',
                    'data': sanitize(item)
                })
        
        return formatted
    
    def _step_mark_failed(self, step_def: Dict[str, Any]) -> Dict[str, Any]:
        """Mark item as failed."""
        # This would update action state
        # For now, just return success
        return {'success': True}
    
    def _step_log(self, step_def: Dict[str, Any]) -> Dict[str, Any]:
        """Log a message."""
        description = step_def.get('description', '')
        value = step_def.get('value', '')
        
        # Resolve variables in log message
        if value:
            message = self.resolver.resolve(str(value))
        elif description:
            message = description
        else:
            message = "Log step executed"
        
        logger.info(f"[Action Executor] {message}")
        
        # Also log to bot logger if available
        if hasattr(self.bot, 'logger'):
            try:
                if isinstance(self.bot.logger, str):
                    self.bot.logger += f"{message}\n"
                else:
                    self.bot.logger.info(message)
            except Exception:
                pass
        
        return {'success': True}
    
    def _step_call_bot_method(self, step_def: Dict[str, Any]) -> Dict[str, Any]:
        """Call a method on the bot instance."""
        method_name = step_def.get('method', '')
        method_args = step_def.get('args', [])
        method_kwargs = step_def.get('kwargs', {})
        variable_name = step_def.get('variable_name', '')
        
        # #region agent log
        import json
        from datetime import datetime
        with open('/Users/morteza/Desktop/monoes/mono-agent/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"timestamp": datetime.now().timestamp() * 1000, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "E", "location": "action_executor.py:858", "message": f"_step_call_bot_method: Calling {method_name}", "data": {"method": method_name, "args": method_args, "variable_name": variable_name}}) + '\n')
        # #endregion
        
        if not method_name:
            return {'success': False, 'error': 'No method name provided'}
        
        try:
            # Resolve arguments
            resolved_args = []
            for arg in method_args:
                if isinstance(arg, str):
                    resolved_args.append(self.resolver.resolve(arg))
                else:
                    resolved_args.append(arg)
            
            resolved_kwargs = {}
            for k, v in method_kwargs.items():
                if isinstance(v, str):
                    resolved_kwargs[k] = self.resolver.resolve(v)
                else:
                    resolved_kwargs[k] = v
            
            # #region agent log
            with open('/Users/morteza/Desktop/monoes/mono-agent/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"timestamp": datetime.now().timestamp() * 1000, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "F", "location": "action_executor.py:880", "message": f"_step_call_bot_method: Resolved args", "data": {"resolved_args": [str(a)[:100] for a in resolved_args]}}) + '\n')
            # #endregion
            
            # Call bot method
            if hasattr(self.bot, method_name):
                method = getattr(self.bot, method_name)
                result = method(*resolved_args, **resolved_kwargs)
                
                # #region agent log
                with open('/Users/morteza/Desktop/monoes/mono-agent/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"timestamp": datetime.now().timestamp() * 1000, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "G", "location": "action_executor.py:888", "message": f"_step_call_bot_method: Method returned", "data": {"method": method_name, "result": str(result)[:200] if result else None, "variable_name": variable_name}}) + '\n')
                # #endregion
                
                # Store result if variable_name is provided
                if variable_name:
                    self.context['variables'][variable_name] = result
                
                return {'success': True, 'data': result}
            else:
                # #region agent log
                with open('/Users/morteza/Desktop/monoes/mono-agent/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"timestamp": datetime.now().timestamp() * 1000, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "H", "location": "action_executor.py:896", "message": f"_step_call_bot_method: Method not found", "data": {"method": method_name}}) + '\n')
                # #endregion
                return {'success': False, 'error': f'Method {method_name} not found on bot'}
        except Exception as e:
            logger.error(f"Error calling bot method {method_name}: {e}", exc_info=True)
            # #region agent log
            with open('/Users/morteza/Desktop/monoes/mono-agent/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"timestamp": datetime.now().timestamp() * 1000, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "I", "location": "action_executor.py:900", "message": f"_step_call_bot_method: Exception", "data": {"method": method_name, "error": str(e), "type": type(e).__name__}}) + '\n')
            # #endregion
            return {'success': False, 'error': str(e)}
    
    # Helper methods
    
    def _get_element(self, element_ref: str):
        """Get element from context or find it."""
        # Check if element is in context
        if element_ref in self.context['elements']:
            return self.context['elements'][element_ref]
        
        # Try to find step that created this element
        for step in self.action_def.get('steps', []):
            if step.get('id') == element_ref:
                result = self._step_find_element(step)
                if result.get('success'):
                    return result.get('element')
        
        return None
    
    def _get_action_name_for_config(self) -> str:
        """Get action name for config manager (DEPRECATED - use _get_config_params)."""
        action_type = getattr(self.action, 'type', '').lower()
        # Map action types to config names
        mapping = {
            'bulk_messaging': 'send_message',
            'keyword_search': 'keyword_search',
            'profile_search': 'profile_info',
        }
        return mapping.get(action_type, action_type)

    def _get_config_params(self) -> tuple[str, Optional[str], Dict]:
        """
        Get config parameters based on current execution context.

        Returns context-aware config name, context, and schema for multi-page actions.
        Supports both single-page actions (no context) and multi-page actions (with context).

        Returns:
            Tuple of (action_name, config_context, schema)
            - action_name: Base action name for logging
            - config_context: Page context for multi-page actions (e.g., "POST_PAGE")
            - schema: Extraction schema for the current page context
        """
        platform = getattr(self.action, 'source', '').upper()
        action_type = getattr(self.action, 'type', '').upper()

        # Get configContext from variables (set by update_progress steps in JSON)
        config_context = self.context.get('variables', {}).get('configContext')

        # Build schema key based on context
        if config_context:
            # Multi-page action: use context-specific schema
            # e.g., INSTAGRAM_POST_PAGE_SCHEMA
            schema_key = f"{platform}_{config_context}_SCHEMA"
            action_name = action_type  # Keep original action for logging
        else:
            # Single-page action: use action-based schema
            # e.g., INSTAGRAM_PROFILE_INFO_SCHEMA
            schema_key = f"{platform}_{action_type}_SCHEMA"
            action_name = action_type
            config_context = None

        # Import schema from schemas module
        try:
            from newAgent.src.services import schemas
            schema = getattr(schemas, schema_key, {})
            if not schema:
                logger.warning(f"Schema not found: {schema_key}, using empty schema")
        except Exception as e:
            logger.error(f"Error loading schema {schema_key}: {e}")
            schema = {}

        logger.debug(f"Config params: action={action_name}, context={config_context}, schema={schema_key}")

        return action_name, config_context, schema
    
    def _evaluate_condition(self, condition: str) -> bool:
        """Evaluate condition expression (supports AND)."""
        condition = condition.strip()
        
        # Update current_url before evaluation
        try:
            current_url = self.bot.driver.current_url
            self.resolver.add_to_context('current_url', current_url)
        except:
            pass
        
        # Handle "and" expressions
        if ' and ' in condition:
            parts = [p.strip() for p in condition.split(' and ')]
            return all(self._evaluate_condition(p) for p in parts)
        
        # Handle "or" expressions
        if ' or ' in condition:
            parts = [p.strip() for p in condition.split(' or ')]
            return any(self._evaluate_condition(p) for p in parts)

        # Check for "contains" operator (with or without quotes)
        if ' contains ' in condition or " in " in condition:
            if ' contains ' in condition:
                parts = condition.split(' contains ', 1)
            else:
                parts = condition.split(" in ", 1)
            var_name = parts[0].strip()
            search_text = parts[1].strip().strip("'\"")
            value = self._get_condition_value(var_name)
            if value is None:
                return False
            return search_text.lower() in str(value).lower()
        
        # Check for "==" operator
        if ' == ' in condition:
            parts = condition.split(' == ', 1)
            var_name = parts[0].strip()
            raw_expected = parts[1].strip().strip("'\"")
            
            # Type conversion for common literals
            if raw_expected == 'True': expected = True
            elif raw_expected == 'False': expected = False
            elif raw_expected == 'None': expected = None
            else: expected = raw_expected
            
            value = self._get_condition_value(var_name)
            # If expected is boolean, compare boolean; otherwise string
            if isinstance(expected, bool) or expected is None:
                return value == expected
            return str(value) == expected
        
        # Check for "!=" operator
        if ' != ' in condition:
            parts = condition.split(' != ', 1)
            var_name = parts[0].strip()
            raw_expected = parts[1].strip().strip("'\"")

            # Type conversion for common literals
            if raw_expected == 'True': expected = True
            elif raw_expected == 'False': expected = False
            elif raw_expected == 'None': expected = None
            else: expected = raw_expected

            value = self._get_condition_value(var_name)
            if isinstance(expected, bool) or expected is None:
                return value != expected
            return str(value) != expected
        
        # Check for comparison operators
        for op in [' < ', ' > ', ' <= ', ' >= ']:
            if op in condition:
                parts = condition.split(op, 1)
                var_name = parts[0].strip()
                try:
                    expected = float(parts[1].strip())
                    value = self._get_condition_value(var_name)
                    if value is None:
                        return False
                    value_num = float(value) if isinstance(value, (int, float, str)) else 0
                    if op == ' < ':
                        return value_num < expected
                    elif op == ' > ':
                        return value_num > expected
                    elif op == ' <= ':
                        return value_num <= expected
                    elif op == ' >= ':
                        return value_num >= expected
                except:
                    return False
        
        # Simple variable check
        value = self._get_condition_value(condition)
        return bool(value)
    
    def _get_condition_value(self, var_name: str) -> Any:
        """Get value for condition evaluation."""
        # Check special variables first
        if var_name == 'current_url':
            try:
                url = self.bot.driver.current_url
                self.resolver.add_to_context('current_url', url)
                return url
            except:
                return ''
        
        # Check context variables (highest priority for executor-managed vars)
        if var_name in self.context.get('variables', {}):
            return self.context['variables'][var_name]
        
        # Check step results (e.g., "find_message_button.success")
        if '.' in var_name:
            parts = var_name.split('.', 1)
            step_id = parts[0]
            property_name = parts[1]
            
            if property_name == 'success':
                # Check if step was successful from step_results
                step_result = self.context.get('step_results', {}).get(step_id)
                if step_result:
                    return step_result.get('success', False)
                # Fallback: check if element or data exists
                return step_id in self.context.get('elements', {}) or step_id in self.context.get('data', {})
            
            # Check if it's an element property
            if step_id in self.context.get('elements', {}):
                element = self.context['elements'][step_id]
                if property_name == 'text':
                    try:
                        return element.text
                    except:
                        return ''
                elif property_name == 'visible':
                    try:
                        return element.is_displayed()
                    except:
                        return False
            
            # Check if it's data property (e.g., "extract_post_urls.data")
            if step_id in self.context.get('data', {}):
                data = self.context['data'][step_id]
                if property_name == 'data':
                    return data
                elif property_name == 'count' or property_name == 'length':
                    return len(data) if isinstance(data, (list, dict)) else 0
        
        # Try resolver (for action/saved_item/campaign properties)
        value = self.resolver._resolve_path(var_name)
        if value is not None:
            return value
        
        # Check context data
        if var_name in self.context.get('data', {}):
            return self.context['data'][var_name]
        
        # Check action properties directly
        if hasattr(self.action, var_name):
            return getattr(self.action, var_name)
        
        # Try accessing with getattr for nested paths
        if '.' in var_name:
            parts = var_name.split('.')
            if hasattr(self.action, parts[0]):
                obj = getattr(self.action, parts[0])
                for part in parts[1:]:
                    if hasattr(obj, part):
                        obj = getattr(obj, part)
                    else:
                        return None
                return obj
        
        return None
    
    def _handle_success_action(self, success_handler: Dict[str, Any]):
        """Handle success action."""
        action_type = success_handler.get('action')
        if action_type == 'update_progress':
            increment = success_handler.get('increment')
            if increment:
                current = self.context['variables'].get(increment, 0)
                self.context['variables'][increment] = current + 1
    
    def _handle_completion_action(self, action: str):
        """Handle completion action."""
        # This would integrate with API to update action state
        if action == 'update_action_state':
            # Save any remaining extracted items
            if self.context.get('extracted_items') and self.api_client:
                try:
                    remaining = self.context['extracted_items']
                    if remaining:
                        response = self.api_client.create_people(remaining)
                        
                        is_success = False
                        status_code = getattr(response, 'status_code', 200)
                        
                        if hasattr(response, 'status_code'):
                            is_success = response.status_code < 400
                        elif isinstance(response, dict):
                            is_success = response.get('success', True)
                        else:
                            is_success = True
                            
                        if is_success:
                            logger.info(f"✅ Successfully saved final batch of {len(remaining)} items")
                            self.context['extracted_items'] = []
                        else:
                            logger.error(f"❌ Failed to save final batch of {len(remaining)} items (Status: {status_code})")
                except Exception as api_err:
                    logger.error(f"❌ Error saving final batch: {api_err}")
            
            # Update action progress
            reached_index = self.context.get('variables', {}).get('reachedIndex', 0)
            results_count = len(self.context.get('extracted_items', []))
            
            # Update action object if possible
            if hasattr(self.action, 'reachedIndex'):
                self.action.reachedIndex = reached_index
            if hasattr(self.action, 'resultsCount'):
                self.action.resultsCount = results_count

