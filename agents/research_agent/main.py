from typing import Dict, Any
import logging
from tools.searcher.main import Searcher

class ResearchAgent:
    """Research agent for web searching and information gathering"""
    
    def __init__(self, search_url: str = None, max_retries: int = None,
                 pool_connections: int = None, pool_maxsize: int = None):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Research Agent")
        self.searcher = Searcher(search_url, max_retries, pool_connections, pool_maxsize)
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        
    def execute_task(self, task_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a research task"""
        self.logger.info(f"Executing task: {task_spec}")
        
        # Extract parameters
        query = task_spec.get("query")
        
        if not query:
            return {
                "status": "error",
                "task_id": task_spec.get("id", "unknown"),
                "error": "No query provided in task specification"
            }
        
        try:
            # Perform search
            results = self.searcher.search(query)
            
            # Extract relevant information
            if results:
                # In a real implementation, we would process the results more thoroughly
                result_str = f"Found {len(results)} results for query: {query}"
            else:
                result_str = f"No results found for query: {query}"
            
            return {
                "status": "completed",
                "task_id": task_spec.get("id", "unknown"),
                "result": result_str
            }
        except Exception as e:
            self.logger.error(f"Error executing research task: {e}")
            return {
                "status": "error",
                "task_id": task_spec.get("id", "unknown"),
                "error": str(e)
            }
            
    def close(self):
        """Close the searcher session"""
        if hasattr(self.searcher, 'close'):
            self.searcher.close()

if __name__ == "__main__":
    # For testing purposes
    with ResearchAgent() as agent:
        result = agent.execute_task({"id": 1, "query": "sample research query"})
        print(result)