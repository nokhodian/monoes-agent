from newAgent.src.services.action_executor import ActionExecutor
import traceback

class ActionRunner:
    def __init__(self, bot, action):
        self.bot = bot
        self.action = action

    def run(self):
        print("\n[2/3] Executing action...")
        try:
            executor = ActionExecutor(self.bot, self.action)
            result = executor.execute()
            
            print("\n[3/3] Execution complete!")
            print("=" * 60)
            print("RESULT:")
            print(result)
            print("=" * 60)
            return result
            
        except Exception as e:
            print(f"✗ Action execution failed: {e}")
            traceback.print_exc()
            return None
