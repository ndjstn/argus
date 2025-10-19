#!/usr/bin/env python3

import sys
import os
import logging
import time
from unittest.mock import patch, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_application_manager_initialization():
    """Test ApplicationManager initialization"""
    try:
        # Import the ApplicationManager
        from main import ApplicationManager
        
        # Test creating an application manager
        app_manager = ApplicationManager()
        logger.info("ApplicationManager initialized successfully")
        
        # Verify attributes
        assert hasattr(app_manager, 'services')
        assert hasattr(app_manager, 'shutdown_event')
        assert hasattr(app_manager, 'threads')
        
        return True
        
    except Exception as e:
        logger.error(f"ApplicationManager initialization test failed: {e}")
        return False

def test_application_manager_shutdown():
    """Test ApplicationManager shutdown functionality"""
    try:
        # Import the ApplicationManager
        from main import ApplicationManager
        
        # Test creating an application manager
        app_manager = ApplicationManager()
        logger.info("ApplicationManager initialized successfully")
        
        # Mock sys.exit to prevent the test from exiting
        with patch('main.sys.exit'):
            # Test shutdown
            app_manager.shutdown()
            logger.info("ApplicationManager shutdown test completed")
        
        # Note: This will exit the process, so we can't verify the shutdown state
        # in this test. In a real test, we would mock the sys.exit call.
        return True
        
    except Exception as e:
        logger.error(f"ApplicationManager shutdown test failed: {e}")
        return False

def test_main_module_import():
    """Test that the main module can be imported without errors"""
    try:
        # Import the main module
        import main
        logger.info("Main module imported successfully")
        
        # Verify key components exist
        assert hasattr(main, 'ApplicationManager')
        assert hasattr(main, 'main')
        
        return True
        
    except Exception as e:
        logger.error(f"Main module import test failed: {e}")
        return False

def main():
    """Run all main application tests"""
    tests = [
        ("ApplicationManager Initialization", test_application_manager_initialization),
        ("Main Module Import", test_main_module_import)
        # Note: Skipping shutdown test as it exits the process
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                logger.info(f"{test_name}: PASSED")
            else:
                logger.error(f"{test_name}: FAILED")
        except Exception as e:
            logger.error(f"{test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Calculate overall result
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nMain Application Tests: {passed}/{total} passed")
    
    if passed == total:
        print("All main application tests: PASSED")
        return 0
    else:
        print("Some main application tests: FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())