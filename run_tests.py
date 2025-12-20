#!/usr/bin/env python3
import unittest
import sys
import os

def run_tests():
    # Add project root to path so imports work correctly
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), 'tests')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        return 0
    else:
        return 1

if __name__ == '__main__':
    sys.exit(run_tests())
