# JSON Action Definitions

This directory contains JSON-based action definitions for all supported platforms and action types.

## Structure

```
actions/
├── linkedin/
│   ├── BULK_MESSAGING.json
│   ├── KEYWORD_SEARCH.json
│   ├── PROFILE_SEARCH.json
│   └── PROFILE_FETCH.json
├── instagram/
│   ├── BULK_MESSAGING.json
│   ├── KEYWORD_SEARCH.json
│   └── PROFILE_SEARCH.json
├── tiktok/
│   ├── BULK_MESSAGING.json
│   └── KEYWORD_SEARCH.json
└── x/
    ├── BULK_MESSAGING.json
    └── KEYWORD_SEARCH.json
```

## JSON Schema

Each action definition follows this structure:

```json
{
  "actionType": "ACTION_TYPE",
  "platform": "PLATFORM_NAME",
  "version": "1.0.0",
  "description": "Human-readable description",
  "metadata": {
    "requiresAuth": true,
    "supportsPagination": false,
    "supportsRetry": true
  },
  "inputs": {
    "required": ["field1", "field2"],
    "optional": ["field3"]
  },
  "outputs": {
    "success": ["output1", "output2"],
    "failure": ["error1"]
  },
  "steps": [...],
  "loops": [...],
  "errorHandling": {...}
}
```

## Step Types

### Navigation Steps
- `navigate`: Navigate to a URL
- `wait`: Wait for a condition or duration
- `refresh`: Refresh the current page

### Element Interaction Steps
- `find_element`: Locate an element using XPath or config key
- `click`: Click an element
- `type`: Type text into an element
- `scroll`: Scroll to an element
- `hover`: Hover over an element

### Data Extraction Steps
- `extract_text`: Extract text content from an element
- `extract_attribute`: Extract an attribute value from an element
- `extract_multiple`: Extract multiple values (e.g., list of items)

### Control Flow Steps
- `condition`: Conditional branching based on conditions

### State Management Steps
- `update_progress`: Update action progress variables
- `save_data`: Save extracted data
- `mark_failed`: Mark an item as failed

## Variables

Variables can be used in step definitions using `{{variable}}` syntax:

- `{{item.url}}`: URL of current item in loop
- `{{messageText}}`: Message text from action
- `{{current_url}}`: Current page URL
- `{{step_id.success}}`: Success status of a previous step

## Error Handling

Each step can define error handling:

```json
{
  "onError": {
    "action": "retry",
    "maxRetries": 3,
    "onFailure": "mark_failed"
  }
}
```

Error actions:
- `retry`: Retry the step
- `try_alternative`: Try alternative XPaths/config keys
- `mark_failed`: Mark item as failed and continue
- `skip`: Skip this step
- `abort`: Abort the entire action

## Loops

Loops iterate over collections and execute steps for each item:

```json
{
  "loops": [{
    "id": "process_items",
    "iterator": "selectedListItems",
    "indexVar": "reachedIndex",
    "steps": ["step1", "step2", "step3"],
    "onComplete": "update_action_state"
  }]
}
```

## Adding New Actions

1. Create a new JSON file in the appropriate platform directory
2. Follow the schema defined in `src/services/action_schema.py`
3. Test the action definition
4. Update worker threads to use the executor

## Migration from Code

To migrate an existing action from code to JSON:

1. Identify all steps in the current implementation
2. Map each step to a JSON step definition
3. Extract XPaths to config keys or include directly
4. Define error handling for each step
5. Test thoroughly before replacing code implementation




