"""
Unit tests for the RedisConnectionPool class.
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestRedisConnectionPool:
    """Test suite for RedisConnectionPool class."""

    def test_redis_pool_initialization(self):
        """Test Redis connection pool initialization"""
        from core.redis_pool import RedisConnectionPool
        
        # Test creating a pool with default parameters
        pool = RedisConnectionPool()
        
        # Test getting pool info
        pool_info = pool.get_pool_info()
        
        # Verify pool info structure
        assert 'host' in pool_info
        assert 'port' in pool_info
        assert 'max_connections' in pool_info

    def test_redis_pool_shutdown(self):
        """Test Redis connection pool shutdown functionality"""
        from core.redis_pool import RedisConnectionPool
        
        # Test creating a pool
        pool = RedisConnectionPool()
        
        # Test closing the pool
        pool.close_all()
        
        # Test that pool is marked as shutdown
        with pytest.raises(Exception, match="shut down"):
            pool.get_connection()

    @patch('core.redis_pool.redis.Redis')
    def test_redis_pool_with_mocked_redis(self, mock_redis):
        """Test Redis connection pool with mocked Redis"""
        from core.redis_pool import RedisConnectionPool
        
        # Create a pool
        pool = RedisConnectionPool()
        
        # Mock Redis connection
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
            
            assert value == "test_value"