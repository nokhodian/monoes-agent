# NewAgent CLI

A unified command-line interface for running automation actions, managing sessions, and testing bots across different platforms.

## Installation

1. Install Python 3.9+
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the tool from the project root:

```bash
python3 newAgent/main.py run <platform> <action_type> [args...]
```

### Examples

**Instagram Keyword Search:**
```bash
python3 newAgent/main.py run instagram KEYWORD_SEARCH keyword="python" max_results=5
```

**LinkedIn Keyword Search:**
```bash
python3 newAgent/main.py run linkedin KEYWORD_SEARCH keyword="software engineer" max_results=5
```

## Features

- **Automatic Cookie Management:** Automatically loads cookies from the database. If not logged in, it waits for manual login and saves the new session.
- **Enhanced Logging:** Clear, step-by-step progress output.
- **Cross-Platform Support:** Works with Instagram, LinkedIn, X, and TikTok.
- **Direct Action Execution:** Runs actions defined in `src/data/actions`.

## Directory Structure

- `main.py`: CLI entry point.
- `core/`: Core logic for bots, authentication, and execution.
- `utils/`: Helper utilities like logging.
