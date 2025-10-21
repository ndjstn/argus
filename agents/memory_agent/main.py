from typing import Dict, Any
import logging
from sentence_transformers import SentenceTransformer
from tools.obsidian_conn.main import ObsidianConnector
from tools.faiss_store.main import FAISSStore

class MemoryAgent:
    """Memory agent for interacting with Obsidian and FAISS"""
    
    def __init__(self, vault_path: str = "/path/to/obsidian/vault", index_path: str = "/path/to/faiss/index"):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Memory Agent")
        self.obsidian_conn = ObsidianConnector(vault_path)
        self.faiss_store = FAISSStore(index_path)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
    def execute_task(self, task_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a memory-related task"""
        self.logger.info(f"Executing task: {task_spec}")
        
        # Extract parameters
        operation = task_spec.get("operation")
        query = task_spec.get("query")
        
        if not operation:
            return {
                "status": "error",
                "task_id": task_spec.get("id", "unknown"),
                "error": "No operation provided in task specification"
            }
        
        try:
            if operation == "search_notes":
                if not query:
                    return {
                        "status": "error",
                        "task_id": task_spec.get("id", "unknown"),
                        "error": "No query provided for search_notes operation"
                    }
                
                # Search Obsidian notes
                results = self.obsidian_conn.search_notes(query)
                result_str = f"Found {len(results)} notes for query: {query}"
                
            elif operation == "search_vectors":
                if not query:
                    return {
                        "status": "error",
                        "task_id": task_spec.get("id", "unknown"),
                        "error": "No query provided for search_vectors operation"
                    }
                
                # Convert query to vector
                query_vector = self.embedding_model.encode([query])
                
                # Search FAISS store
                results = self.faiss_store.search(query_vector, k=5)
                result_str = f"Found {len(results)} similar vectors for query: {query}"
                
            else:
                result_str = f"Unknown operation: {operation}"
            
            return {
                "status": "completed",
                "task_id": task_spec.get("id", "unknown"),
                "result": result_str
            }
        except Exception as e:
            self.logger.error(f"Error executing memory task: {e}")
            return {
                "status": "error",
                "task_id": task_spec.get("id", "unknown"),
                "error": str(e)
            }

if __name__ == "__main__":
    # For testing purposes
    agent = MemoryAgent()
    result = agent.execute_task({
        "id": 1,
        "operation": "search_notes",
        "query": "sample memory query"
    })
    print(result)