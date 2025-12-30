"""
JSON Schema validation for action definitions.
Defines the schema structure for action JSON files.
"""
import json
import os
import logging
from typing import Dict, Any, Optional

try:
    import jsonschema
    from jsonschema import validate, ValidationError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    logging.warning("jsonschema not available - validation will be limited")
    # Create dummy classes to avoid import errors
    class ValidationError(Exception):
        pass
    def validate(*args, **kwargs):
        pass

# JSON Schema for action definitions
ACTION_SCHEMA = {
    "type": "object",
    "required": ["actionType", "platform", "version", "steps"],
    "properties": {
        "actionType": {
            "type": "string",
            "description": "Type of action (e.g., BULK_MESSAGING, KEYWORD_SEARCH)"
        },
        "platform": {
            "type": "string",
            "enum": ["LINKEDIN", "INSTAGRAM", "TIKTOK", "X", "TELEGRAM", "EMAIL", "FLATLAY"],
            "description": "Target platform for the action"
        },
        "version": {
            "type": "string",
            "description": "Version of the action definition"
        },
        "description": {
            "type": "string",
            "description": "Human-readable description of the action"
        },
        "metadata": {
            "type": "object",
            "properties": {
                "requiresAuth": {"type": "boolean"},
                "supportsPagination": {"type": "boolean"},
                "supportsRetry": {"type": "boolean"}
            }
        },
        "inputs": {
            "type": "object",
            "properties": {
                "required": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "optional": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        },
        "outputs": {
            "type": "object",
            "properties": {
                "success": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "failure": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        },
        "steps": {
            "type": "array",
            "items": {"$ref": "#/definitions/step"}
        },
        "loops": {
            "type": "array",
            "items": {"$ref": "#/definitions/loop"}
        },
        "errorHandling": {
            "type": "object",
            "properties": {
                "globalRetries": {"type": "integer"},
                "retryDelay": {"type": "integer"},
                "onFinalFailure": {"type": "string"}
            }
        }
    },
    "definitions": {
        "step": {
            "type": "object",
            "required": ["id", "type"],
            "properties": {
                "id": {"type": "string"},
                "type": {
                    "type": "string",
                    "enum": [
                        "navigate", "wait", "refresh",
                        "find_element", "click", "type", "scroll", "hover",
                        "extract_text", "extract_attribute", "extract_multiple",
                        "condition", "loop", "call_action",
                        "update_progress", "save_data", "mark_failed", "call_bot_method", "log"
                    ]
                },
                "url": {"type": "string"},
                "configKey": {"type": "string"},
                "elementRef": {"type": "string"},
                "text": {"type": "string"},
                "attribute": {"type": "string"},
                "waitFor": {"type": "string"},
                "timeout": {"type": "number"},
                "humanLike": {"type": "boolean"},
                "onError": {"$ref": "#/definitions/errorHandler"},
                "onSuccess": {"$ref": "#/definitions/successHandler"},
                "condition": {"type": "string"},
                "then": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "else": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "alternatives": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        },
        "loop": {
            "type": "object",
            "required": ["id", "iterator", "steps"],
            "properties": {
                "id": {"type": "string"},
                "iterator": {"type": "string"},
                "indexVar": {"type": "string"},
                "steps": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "onComplete": {"type": "string"}
            }
        },
        "errorHandler": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["retry", "try_alternative", "mark_failed", "skip", "abort", "continue"]
                },
                "maxRetries": {"type": "integer"},
                "onFailure": {"type": "string"},
                "alternatives": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        },
        "successHandler": {
            "type": "object",
            "properties": {
                "action": {"type": "string"},
                "increment": {"type": "string"},
                "set": {"type": "object"}
            }
        }
    }
}


class ActionSchemaValidator:
    """Validates action definition JSON files against the schema."""
    
    def __init__(self):
        self.schema = ACTION_SCHEMA
        if JSONSCHEMA_AVAILABLE:
            self.validator = jsonschema.Draft7Validator(self.schema)
        else:
            self.validator = None
    
    def validate(self, action_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate action data against schema.
        
        Args:
            action_data: Dictionary containing action definition
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not JSONSCHEMA_AVAILABLE or not self.validator:
            # Basic validation without jsonschema
            required_fields = ["actionType", "platform", "steps"]
            missing = [f for f in required_fields if f not in action_data]
            if missing:
                return False, f"Missing required fields: {missing}"
            if not isinstance(action_data.get("steps"), list):
                return False, "steps must be a list"
            return True, None
        
        try:
            self.validator.validate(action_data)
            return True, None
        except ValidationError as e:
            error_path = " -> ".join(str(p) for p in e.path)
            error_message = f"Validation error at {error_path}: {e.message}"
            return False, error_message
        except Exception as e:
            return False, f"Unexpected validation error: {str(e)}"
    
    def validate_file(self, file_path: str) -> tuple[bool, Optional[str]]:
        """
        Validate action definition from JSON file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not os.path.exists(file_path):
                return False, f"File not found: {file_path}"
            
            with open(file_path, 'r', encoding='utf-8') as f:
                action_data = json.load(f)
            
            return self.validate(action_data)
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {str(e)}"
        except Exception as e:
            return False, f"Error reading file: {str(e)}"


def validate_action(action_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Convenience function to validate action data.
    
    Args:
        action_data: Dictionary containing action definition
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    validator = ActionSchemaValidator()
    return validator.validate(action_data)


def validate_action_file(file_path: str) -> tuple[bool, Optional[str]]:
    """
    Convenience function to validate action file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    validator = ActionSchemaValidator()
    return validator.validate_file(file_path)

