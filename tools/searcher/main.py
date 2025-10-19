from typing import Dict, Any, List
import logging
import requests
import time
from urllib.parse import urlencode
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
import yaml

# Local imports
from core.exceptions import APIError, FileIOError

class Searcher:
    """Web searcher using Searxng or similar search engine with error handling"""
    
    def __init__(self, search_url: str = None, max_retries: int = None,
                 pool_connections: int = None, pool_maxsize: int = None):
        # Load configuration
        config = self._load_config()
        
        # Use provided values or fall back to config or defaults
        self.search_url = search_url or config.get('search_url') or "http://localhost:8080"
        max_retries = max_retries if max_retries is not None else config.get('max_retries', 3)
        pool_connections = pool_connections if pool_connections is not None else config.get('pool_connections', 10)
        pool_maxsize = pool_maxsize if pool_maxsize is not None else config.get('pool_maxsize', 20)
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initializing Searcher with URL: {self.search_url}")
        
        # Metrics
        self.total_search_calls = 0
        self.total_page_content_calls = 0
        self.total_search_time_ms = 0
        self.total_page_content_time_ms = 0
        self.total_search_results = 0
        self.total_page_content_length = 0
        
        # Create a session with connection pooling
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        # Mount adapter with retry strategy and connection pooling
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
    def search(self, query: str, categories: List[str] = None) -> List[Dict[str, Any]]:
        """Perform a web search"""
        self.logger.info(f"Searching for: {query}")
        start_time = time.time()
        self.total_search_calls += 1
        
        try:
            # Construct search URL
            params = {
                "q": query,
                "format": "json"
            }
            
            if categories:
                params["categories"] = ",".join(categories)
                
            search_url = f"{self.search_url}/search?{urlencode(params)}"
            
            # Perform search using session with connection pooling
            response = self.session.get(search_url, timeout=30)
            search_time = (time.time() - start_time) * 1000
            self.total_search_time_ms += search_time
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                self.total_search_results += len(results)
                return results
            else:
                self.logger.error(f"Search failed with status code: {response.status_code}")
                raise APIError(f"Search API returned status code {response.status_code}", "SEARCH_API_ERROR", {
                    "status_code": response.status_code,
                    "url": search_url
                })
        except requests.exceptions.Timeout as e:
            search_time = (time.time() - start_time) * 1000
            self.total_search_time_ms += search_time
            self.logger.error(f"Search timed out: {e}")
            raise APIError(f"Search timed out: {str(e)}", "SEARCH_TIMEOUT_ERROR")
        except requests.exceptions.ConnectionError as e:
            search_time = (time.time() - start_time) * 1000
            self.total_search_time_ms += search_time
            self.logger.error(f"Search connection error: {e}")
            raise APIError(f"Search connection error: {str(e)}", "SEARCH_CONNECTION_ERROR")
        except requests.exceptions.RequestException as e:
            search_time = (time.time() - start_time) * 1000
            self.total_search_time_ms += search_time
            self.logger.error(f"Search request error: {e}")
            raise APIError(f"Search request error: {str(e)}", "SEARCH_REQUEST_ERROR")
        except Exception as e:
            search_time = (time.time() - start_time) * 1000
            self.total_search_time_ms += search_time
            self.logger.error(f"Unexpected error performing search: {e}")
            raise APIError(f"Unexpected error performing search: {str(e)}", "SEARCH_UNEXPECTED_ERROR")
        
    def get_page_content(self, url: str) -> str:
        """Get the content of a web page"""
        self.logger.info(f"Getting content from: {url}")
        start_time = time.time()
        self.total_page_content_calls += 1
        
        try:
            response = self.session.get(url, timeout=30)
            page_time = (time.time() - start_time) * 1000
            self.total_page_content_time_ms += page_time
            
            if response.status_code == 200:
                content = response.text
                self.total_page_content_length += len(content)
                return content
            else:
                self.logger.error(f"Failed to fetch page content with status code: {response.status_code}")
                raise APIError(f"Page content API returned status code {response.status_code}", "PAGE_CONTENT_API_ERROR", {
                    "status_code": response.status_code,
                    "url": url
                })
        except requests.exceptions.Timeout as e:
            page_time = (time.time() - start_time) * 1000
            self.total_page_content_time_ms += page_time
            self.logger.error(f"Page content fetch timed out: {e}")
            raise APIError(f"Page content fetch timed out: {str(e)}", "PAGE_CONTENT_TIMEOUT_ERROR")
        except requests.exceptions.ConnectionError as e:
            page_time = (time.time() - start_time) * 1000
            self.total_page_content_time_ms += page_time
            self.logger.error(f"Page content connection error: {e}")
            raise APIError(f"Page content connection error: {str(e)}", "PAGE_CONTENT_CONNECTION_ERROR")
        except requests.exceptions.RequestException as e:
            page_time = (time.time() - start_time) * 1000
            self.total_page_content_time_ms += page_time
            self.logger.error(f"Page content request error: {e}")
            raise APIError(f"Page content request error: {str(e)}", "PAGE_CONTENT_REQUEST_ERROR")
        except Exception as e:
            page_time = (time.time() - start_time) * 1000
            self.total_page_content_time_ms += page_time
            self.logger.error(f"Unexpected error fetching page content: {e}")
            raise APIError(f"Unexpected error fetching page content: {str(e)}", "PAGE_CONTENT_UNEXPECTED_ERROR")
            
    def close(self):
        """Close the session and clean up connections"""
        self.session.close()
    
    def get_pool_info(self) -> dict:
        """Get information about the connection pool"""
        return {
            "total_search_calls": self.total_search_calls,
            "total_page_content_calls": self.total_page_content_calls,
            "total_search_time_ms": self.total_search_time_ms,
            "total_page_content_time_ms": self.total_page_content_time_ms,
            "total_search_results": self.total_search_results,
            "total_page_content_length": self.total_page_content_length,
            "average_search_time_ms": self.total_search_time_ms / self.total_search_calls if self.total_search_calls > 0 else 0,
            "average_page_content_time_ms": self.total_page_content_time_ms / self.total_page_content_calls if self.total_page_content_calls > 0 else 0
        }
    
    def _load_config(self) -> dict:
        """Load searcher configuration from config file"""
        config_path = os.path.join(os.path.dirname(__file__), "..", "..", "configs", "policy.yaml")
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config.get('searcher', {})
        except FileNotFoundError as e:
            self.logger.info(f"Searcher config file not found, using defaults: {config_path}")
            return {}
        except Exception as e:
            error_context = {
                "config_path": config_path,
                "operation": "_load_config"
            }
            self.logger.warning(f"Failed to load searcher config, using defaults: {e}", extra=error_context)
            return {}

if __name__ == "__main__":
    # For testing purposes
    searcher = Searcher()
    results = searcher.search("sample query")
    print(f"Search results: {len(results)} found")
    
    if results:
        content = searcher.get_page_content(results[0].get("url", ""))
        print(f"Page content length: {len(content)}")
    
    # Clean up
    searcher.close()