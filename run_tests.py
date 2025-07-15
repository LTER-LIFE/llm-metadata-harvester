#!/usr/bin/env python3
"""
Test runner script for LLM Metadata Harvester
"""
import subprocess
import sys
import os


def run_tests():
    """Run the test suite"""
    
    # Change to the project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Run pytest with various options
    test_commands = [
        # Run all tests (LLM client and integration tests)
        ["python", "-m", "pytest", "tests/", "-v"],
    ]
    
    for cmd in test_commands:
        print(f"\n{'='*60}")
        print(f"Running: {' '.join(cmd)}")
        print(f"{'='*60}")
        
        result = subprocess.run(cmd, capture_output=False)
        
        if result.returncode != 0:
            print(f"Tests failed with return code: {result.returncode}")
            return False
    
    print(f"\n{'='*60}")
    print("All tests completed successfully!")
    print(f"{'='*60}")
    return True


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1) 