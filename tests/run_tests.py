#!/usr/bin/env python3
"""
Test runner for all variable mapping and alias functionality tests
"""

import os
from pathlib import Path
import subprocess
import sys

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_test_file(test_file):
    """Run a single test file and capture results"""
    print(f"\n{'=' * 60}")
    print(f"Running: {test_file}")
    print(f"{'=' * 60}")

    try:
        # Change to the tests directory
        test_dir = Path(__file__).parent
        os.chdir(test_dir)

        # Run the test file
        result = subprocess.run(
            [sys.executable, test_file], capture_output=True, text=True, timeout=30
        )

        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print(f"✗ Test {test_file} timed out")
        return False
    except Exception as e:
        print(f"✗ Error running {test_file}: {e}")
        return False


def main():
    """Run all tests in the tests directory"""
    print("FastAPI Templr - Variable Mapping Test Suite")
    print("=" * 60)

    # Get the tests directory
    tests_dir = Path(__file__).parent

    # List of test files to run
    test_files = [
        "test_json_serialization.py",
        "test_variable_mapping.py",
        "test_comprehensive.py",
        "check_database.py",
    ]

    results = {}

    # Run each test file
    for test_file in test_files:
        test_path = tests_dir / test_file
        if test_path.exists():
            success = run_test_file(test_file)
            results[test_file] = success
        else:
            print(f"Warning: Test file {test_file} not found")
            results[test_file] = False

    # Print summary
    print(f"\n{'=' * 60}")
    print("TEST SUMMARY")
    print(f"{'=' * 60}")

    total_tests = len(results)
    passed_tests = sum(1 for success in results.values() if success)

    for test_file, success in results.items():
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{test_file:<30} {status}")

    print(
        f"\nTotal: {total_tests}, Passed: {passed_tests}, Failed: {total_tests - passed_tests}"
    )

    if passed_tests == total_tests:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
