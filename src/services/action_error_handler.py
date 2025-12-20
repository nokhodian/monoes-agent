"""
Error handling system for action execution.
Handles retries, alternatives, and error recovery strategies.
"""
import logging
import time
from typing import Dict, Any, Optional
from newAgent.src.data.attributes import Attrs

logger = logging.getLogger(__name__)


class ActionErrorHandler:
    """Handles errors during action execution."""
    
    def __init__(self):
        self.retry_counts: Dict[str, int] = {}  # Track retry counts per step
    
    def handle_step_error(self, error_handler: Dict[str, Any], 
                         step_result: Dict[str, Any],
                         bot: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle error for a step based on error handler configuration.
        
        Args:
            error_handler: Error handler configuration from step definition
            step_result: Result from failed step
            bot: Bot instance
            context: Execution context
            
        Returns:
            Dictionary with handling result (success, abort, skip, etc.)
        """
        action = error_handler.get('action', 'abort')
        step_id = step_result.get('step_id', 'unknown')
        
        if action == 'retry':
            return self._handle_retry(error_handler, step_result, bot, context, step_id)
        elif action == 'try_alternative':
            return self._handle_alternative(error_handler, step_result, bot, context)
        elif action == 'mark_failed':
            return self._handle_mark_failed(error_handler, step_result, context)
        elif action == 'skip' or action == 'continue':
            return {'success': True, 'skip': True}
        elif action == 'abort':
            return {'success': False, 'abort': True}
        else:
            logger.warning(f"Unknown error action: {action}")
            return {'success': False, 'abort': True}
    
    def _handle_retry(self, error_handler: Dict[str, Any], 
                     step_result: Dict[str, Any],
                     bot: Any, context: Dict[str, Any],
                     step_id: str) -> Dict[str, Any]:
        """Handle retry action."""
        max_retries = error_handler.get('maxRetries', 3)
        retry_delay = error_handler.get('retryDelay', Attrs.sleep_config['retry_wait'])
        on_failure = error_handler.get('onFailure', 'abort')
        
        # Get current retry count
        retry_key = f"{step_id}_{id(bot)}"
        current_retries = self.retry_counts.get(retry_key, 0)
        
        if current_retries >= max_retries:
            logger.warning(f"Max retries ({max_retries}) reached for step {step_id}")
            # Handle final failure
            if on_failure == 'mark_failed':
                return self._handle_mark_failed({}, step_result, context)
            elif on_failure == 'skip':
                return {'success': True, 'skip': True}
            else:
                return {'success': False, 'abort': True}
        
        # Increment retry count
        self.retry_counts[retry_key] = current_retries + 1
        
        # Wait before retry
        time.sleep(retry_delay)
        
        logger.info(f"Retrying step {step_id} (attempt {current_retries + 1}/{max_retries})")
        
        # Return indication that step should be retried
        return {'success': False, 'retry': True, 'retry_count': current_retries + 1}
    
    def _handle_alternative(self, error_handler: Dict[str, Any],
                           step_result: Dict[str, Any],
                           bot: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle try_alternative action."""
        alternatives = error_handler.get('alternatives', [])
        
        if not alternatives:
            logger.warning("No alternatives specified for try_alternative")
            return {'success': False, 'abort': True}
        
        # This would be handled by the executor when finding elements
        # The executor already tries alternatives in _step_find_element
        return {'success': False, 'error': 'Alternative not found'}
    
    def _handle_mark_failed(self, error_handler: Dict[str, Any],
                           step_result: Dict[str, Any],
                           context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle mark_failed action."""
        # Mark item as failed in context
        if 'failed_items' not in context:
            context['failed_items'] = []
        
        failed_item = {
            'step_id': step_result.get('step_id'),
            'error': step_result.get('error', 'Unknown error'),
            'timestamp': time.time()
        }
        context['failed_items'].append(failed_item)
        
        logger.info(f"Marked item as failed: {failed_item}")
        
        return {'success': True, 'marked_failed': True}
    
    def reset_retry_count(self, step_id: str, bot: Any):
        """Reset retry count for a step."""
        retry_key = f"{step_id}_{id(bot)}"
        self.retry_counts.pop(retry_key, None)
    
    def get_retry_count(self, step_id: str, bot: Any) -> int:
        """Get current retry count for a step."""
        retry_key = f"{step_id}_{id(bot)}"
        return self.retry_counts.get(retry_key, 0)




