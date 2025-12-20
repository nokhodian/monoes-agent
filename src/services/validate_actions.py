"""
Script to validate all action JSON definitions.
Run this to check if all action definitions are valid.
"""
import os
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from newAgent.src.services.action_schema import validate_action_file
    from newAgent.src.services.action_loader import get_action_loader
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


def validate_all_actions():
    """Validate all action definitions in the actions directory."""
    loader = get_action_loader()
    base_dir = loader.actions_dir
    
    if not base_dir.exists():
        print(f"Actions directory not found: {base_dir}")
        return False
    
    all_valid = True
    validated_count = 0
    error_count = 0
    warnings = []
    
    print("Validating action definitions...")
    print("=" * 60)
    
    # Get all actions using loader
    all_actions = loader.list_actions()
    
    if not all_actions:
        print("No action definitions found!")
        return False
    
    # Iterate through all platforms
    for platform, action_types in sorted(all_actions.items()):
        print(f"\nPlatform: {platform}")
        print("-" * 60)
        
        # Validate each action
        for action_type in action_types:
            print(f"  Validating {action_type}...", end=" ")
            
            # Load and validate
            action_def = loader.load_action(platform, action_type, use_cache=False)
            
            if action_def:
                # Check file path
                file_path = base_dir / platform.lower() / f"{action_type}.json"
                is_valid, error = validate_action_file(str(file_path))
                
                if is_valid:
                    # Additional checks
                    if action_def.get('platform', '').upper() != platform.upper():
                        warnings.append(f"{platform}/{action_type}: Platform mismatch")
                    if action_def.get('actionType', '').upper() != action_type.upper():
                        warnings.append(f"{platform}/{action_type}: ActionType mismatch")
                    
                    print("✓ Valid")
                    validated_count += 1
                else:
                    print(f"✗ Invalid: {error}")
                    error_count += 1
                    all_valid = False
            else:
                print("✗ Could not load")
                error_count += 1
                all_valid = False
    
    print("\n" + "=" * 60)
    print(f"Summary: {validated_count} valid, {error_count} errors")
    
    if warnings:
        print(f"\nWarnings ({len(warnings)}):")
        for warning in warnings:
            print(f"  ⚠ {warning}")
    
    return all_valid


if __name__ == "__main__":
    success = validate_all_actions()
    sys.exit(0 if success else 1)

