#!/usr/bin/env python3
"""
Test script for Instagram keyword search process.
Runs the full flow: Search -> Extract -> Save.
"""

import sys
import os
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from main import run_action

def main():
    parser = argparse.ArgumentParser(description='Test Instagram Keyword Search')
    parser.add_argument('keyword', help='Keyword to search for')
    parser.add_argument('--max_results', type=int, default=2, help='Maximum number of results to extract (default: 2)')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    
    args = parser.parse_args()
    
    # Configure arguments for run_action
    kwargs = {
        'keyword': args.keyword,
        'max_results': args.max_results,
        'headless': args.headless
    }
    
    print(f"🚀 Starting Instagram Keyword Search test for keyword: '{args.keyword}'")
    print(f"📊 Target results: {args.max_results}")
    print("-" * 60)
    
    try:
        # main.py's run_action function handles the full flow
        run_action('instagram', 'KEYWORD_SEARCH', kwargs)
        print("\n✅ Test execution completed.")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
