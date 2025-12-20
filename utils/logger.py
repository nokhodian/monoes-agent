import logging

def setup_enhanced_logging():
    """Add custom logging hooks to show step progress prominently."""
    action_logger = logging.getLogger('newAgent.src.services.action_executor')
    original_info = action_logger.info
    original_warning = action_logger.warning
    original_error = action_logger.error
    
    def enhanced_info(msg, *args, **kwargs):
        msg_str = str(msg) % args if args else str(msg)
        
        if 'Executing step:' in msg_str:
            parts = msg_str.split('Executing step:')
            if len(parts) > 1:
                step_info = parts[1].strip()
                print(f"\n{'='*60}")
                print(f"📍 STEP: {step_info}")
                print(f"{'='*60}")
        elif 'result: success' in msg_str:
            success = 'True' in msg_str or 'success=True' in msg_str
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"   {status}")
        elif 'Processing item' in msg_str:
            print(f"\n{msg_str}")
        elif 'Found' in msg_str and 'items to iterate' in msg_str:
            print(f"\n{msg_str}")
        elif 'Starting to process' in msg_str:
            print(f"\n{msg_str}")
        
        original_info(msg, *args, **kwargs)
    
    def enhanced_warning(msg, *args, **kwargs):
        msg_str = str(msg) % args if args else str(msg)
        if 'ERROR' in msg_str or 'Invalid iterator' in msg_str:
            print(f"\n⚠️  WARNING: {msg_str}")
        original_warning(msg, *args, **kwargs)
    
    def enhanced_error(msg, *args, **kwargs):
        msg_str = str(msg) % args if args else str(msg)
        print(f"\n❌ ERROR: {msg_str}")
        original_error(msg, *args, **kwargs)
    
    action_logger.info = enhanced_info
    action_logger.warning = enhanced_warning
    action_logger.error = enhanced_error
