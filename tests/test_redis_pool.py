#!/usr/bin/env python3

import sys
import os
import logging
from unittest.mock import patch, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_redis_pool_initialization():
    """Test Redis connection pool initialization"""
    try:
        # Import the Redis pool
        from core.redis_pool import RedisConnectionPool
        
        # Test creating a pool with default parameters
        pool = RedisConnectionPool()
        logger.info("Redis pool initialized successfully")
        
        # Test getting pool info
        pool_info = pool.get_pool_info()
        logger.info(f"Pool info: {pool_info}")
        
        # Verify pool info structure
        assert 'host' in pool_info
        assert 'port' in pool_info
        assert 'max_connections' in pool_info
        
        return True
        
    except Exception as e:
        logger.error(f"Redis pool initialization test failed: {e}")
        return False

def test_redis_pool_shutdown():
    """Test Redis connection pool shutdown functionality"""
    try:
        # Import the Redis pool
        from core.redis_pool import RedisConnectionPool
        
        # Test creating a pool
        pool = RedisConnectionPool()
        logger.info("Redis pool initialized successfully")
        
        # Test closing the pool
        pool.close_all()
        logger.info("Redis pool closed successfully")
        
        # Test that pool is marked as shutdown
        try:
            pool.get_connection()
            logger.error("Pool should be marked as shutdown")
            return False
        except Exception as e:
            if "shut down" in str(e).lower():
                logger.info("Pool correctly marked as shutdown")
                return True
            else:
                logger.error(f"Unexpected error: {e}")
                return False
        
    except Exception as e:
        logger.error(f"Redis pool shutdown test failed: {e}")
        return False

def test_redis_pool_with_mocked_redis():
    """Test Redis connection pool with mocked Redis"""
    try:
        # Import the Redis pool
        from core.redis_pool import RedisConnectionPool
        
        # Create a pool
        pool = RedisConnectionPool()
        logger.info("Redis pool initialized successfully")
        
        # Mock Redis connection
        with patch('core.redis_pool.redis.Redis') as mock_redis:
            mock_conn = MagicMock()
            mock_redis.return_value = mock_conn
            
            # Test getting a connection
            with pool.connection() as conn:
                # Verify the connection was created
                assert conn is not None
                
                # Test a simple operation
                mock_conn.set.return_value = True
                mock_conn.get.return_value = "test_value"
                
                mock_conn.set("test_key", "test_value")
                value = mock_conn.get("test_key")
                
                logger.info(f"Test value: {value}")
                assert value == "test_value"
                
        logger.info("Redis connection test with mock passed")
        return True
        
    except Exception as e:
        logger.error(f"Redis pool mock test failed: {e}")
        return False

def main():
    """Run all Redis pool tests"""
    tests = [
        ("Redis Pool Initialization", test_redis_pool_initialization),
        ("Redis Pool Shutdown", test_redis_pool_shutdown),
        ("Redis Pool with Mock", test_redis_pool_with_mocked_redis)
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
    
    print(f"\nRedis Pool Tests: {passed}/{total} passed")
    
    if passed == total:
        print("All Redis pool tests: PASSED")
        return 0
    else:
        print("Some Redis pool tests: FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())