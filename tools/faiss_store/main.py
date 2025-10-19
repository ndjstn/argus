from typing import Dict, Any, List
import logging
import numpy as np
import faiss
import os
import json
from core.exceptions import FileIOError

class FAISSStore:
    """FAISS vector store for similarity search with proper resource management"""
    
    def __init__(self, index_path: str):
        self.index_path = index_path
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initializing FAISS Store with index: {index_path}")
        
        # Initialize FAISS index
        self.dimension = 128  # Default dimension
        self.index = faiss.IndexFlatL2(self.dimension)
        
        # Load existing index if it exists
        if os.path.exists(self.index_path):
            self.load_index()
            
        # Metadata storage
        self.metadata_path = self.index_path + ".metadata"
        self.metadata = self.load_metadata()
        
    def load_index(self):
        """Load FAISS index from disk with proper error handling"""
        self.logger.info("Loading FAISS index", extra={
            "event": "faiss_load_index_start",
            "index_path": self.index_path
        })
        
        try:
            self.index = faiss.read_index(self.index_path)
            self.dimension = self.index.d
            self.logger.info("FAISS index loaded successfully", extra={
                "event": "faiss_load_index_success",
                "index_path": self.index_path,
                "dimension": self.dimension,
                "vector_count": self.index.ntotal
            })
        except FileNotFoundError as e:
            # This is expected if the index doesn't exist yet
            self.logger.info("FAISS index file not found, will create new index", extra={
                "event": "faiss_load_index_not_found",
                "index_path": self.index_path
            })
        except Exception as e:
            error_context = {
                "index_path": self.index_path,
                "operation": "load_index"
            }
            self.logger.error("Error loading FAISS index", extra={
                "event": "faiss_load_index_error",
                "index_path": self.index_path,
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise FileIOError(f"Error loading FAISS index: {e}", context=error_context) from e
            
    def save_index(self):
        """Save FAISS index to disk with proper error handling"""
        self.logger.info("Saving FAISS index", extra={
            "event": "faiss_save_index_start",
            "index_path": self.index_path,
            "vector_count": self.index.ntotal if self.index else 0
        })
        
        try:
            faiss.write_index(self.index, self.index_path)
            self.logger.info("FAISS index saved successfully", extra={
                "event": "faiss_save_index_success",
                "index_path": self.index_path,
                "vector_count": self.index.ntotal
            })
        except Exception as e:
            error_context = {
                "index_path": self.index_path,
                "operation": "save_index"
            }
            self.logger.error("Error saving FAISS index", extra={
                "event": "faiss_save_index_error",
                "index_path": self.index_path,
                "vector_count": self.index.ntotal if self.index else 0,
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise FileIOError(f"Error saving FAISS index: {e}", context=error_context) from e
            
    def load_metadata(self) -> Dict[str, Any]:
        """Load metadata from disk with proper file handle management"""
        self.logger.info("Loading metadata", extra={
            "event": "faiss_load_metadata_start",
            "metadata_path": self.metadata_path
        })
        
        file_handle = None
        try:
            if os.path.exists(self.metadata_path):
                file_handle = open(self.metadata_path, 'r')
                metadata = json.load(file_handle)
                self.logger.info("Metadata loaded successfully", extra={
                    "event": "faiss_load_metadata_success",
                    "metadata_path": self.metadata_path,
                    "metadata_count": len(metadata)
                })
                return metadata
            self.logger.info("Metadata file not found, will create new metadata", extra={
                "event": "faiss_load_metadata_not_found",
                "metadata_path": self.metadata_path
            })
            return {}
        except FileNotFoundError:
            # This is expected if the metadata file doesn't exist yet
            self.logger.info("Metadata file not found, will create new metadata", extra={
                "event": "faiss_load_metadata_not_found",
                "metadata_path": self.metadata_path
            })
            return {}
        except Exception as e:
            error_context = {
                "metadata_path": self.metadata_path,
                "operation": "load_metadata"
            }
            self.logger.error("Error loading metadata", extra={
                "event": "faiss_load_metadata_error",
                "metadata_path": self.metadata_path,
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise FileIOError(f"Error loading metadata: {e}", context=error_context) from e
        finally:
            # Ensure file handle is closed
            if file_handle:
                try:
                    file_handle.close()
                    self.logger.debug("Metadata file handle closed", extra={
                        "event": "faiss_metadata_file_handle_closed",
                        "metadata_path": self.metadata_path
                    })
                except Exception as e:
                    self.logger.warning("Error closing metadata file handle", extra={
                        "event": "faiss_metadata_file_handle_close_error",
                        "metadata_path": self.metadata_path,
                        "error": str(e),
                        "error_type": type(e).__name__
                    })
            
    def save_metadata(self):
        """Save metadata to disk"""
        try:
            with open(self.metadata_path, 'w') as f:
                json.dump(self.metadata, f)
            self.logger.info("Saved metadata to disk")
        except Exception as e:
            error_context = {
                "metadata_path": self.metadata_path,
                "operation": "save_metadata"
            }
            raise FileIOError(f"Error saving metadata: {e}", context=error_context) from e
        
    def add_vectors(self, vectors: List[List[float]], metadata: List[Dict[str, Any]]) -> bool:
        """Add vectors to the store"""
        self.logger.info(f"Adding {len(vectors)} vectors to store")
        
        try:
            # Convert to numpy array
            vectors_np = np.array(vectors).astype('float32')
            
            # Check dimension consistency
            if vectors_np.shape[1] != self.dimension:
                if self.index.ntotal == 0:
                    # If this is the first addition, recreate index with correct dimension
                    self.dimension = vectors_np.shape[1]
                    self.index = faiss.IndexFlatL2(self.dimension)
                else:
                    self.logger.error(f"Vector dimension mismatch: expected {self.dimension}, got {vectors_np.shape[1]}")
                    return False
            
            # Add vectors to index
            start_id = self.index.ntotal
            self.index.add(vectors_np)
            
            # Store metadata
            for i, meta in enumerate(metadata):
                self.metadata[str(start_id + i)] = meta
                
            # Save index and metadata
            self.save_index()
            self.save_metadata()
            
            return True
        except Exception as e:
            error_context = {
                "operation": "add_vectors",
                "vector_count": len(vectors) if vectors else 0
            }
            self.logger.error(f"Error adding vectors: {e}", extra=error_context)
            return False
        
    def search(self, query_vector: List[float], k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar vectors"""
        self.logger.info(f"Searching for similar vectors with k={k}")
        
        try:
            # Convert query to numpy array
            query_np = np.array([query_vector]).astype('float32')
            
            # Check dimension consistency
            if query_np.shape[1] != self.dimension:
                self.logger.error(f"Query dimension mismatch: expected {self.dimension}, got {query_np.shape[1]}")
                return []
            
            # Perform search
            distances, indices = self.index.search(query_np, k)
            
            # Retrieve metadata
            results = []
            for i in range(len(indices[0])):
                idx = indices[0][i]
                if idx != -1:  # -1 indicates no result
                    result = {
                        "id": str(idx),
                        "distance": float(distances[0][i]),
                        "metadata": self.metadata.get(str(idx), {})
                    }
                    results.append(result)
            
            return results
        except Exception as e:
            error_context = {
                "operation": "search",
                "k": k
            }
            self.logger.error(f"Error searching vectors: {e}", extra=error_context)
            return []
        
    def delete_vectors(self, ids: List[str]) -> bool:
        """Delete vectors by IDs"""
        self.logger.info(f"Deleting {len(ids)} vectors from store")
        
        # Note: FAISS doesn't support direct deletion
        # In a real implementation, you would need to:
        # 1. Mark vectors as deleted in metadata
        # 2. Rebuild the index periodically
        # For now, we'll just remove from metadata
        
        try:
            for id in ids:
                if id in self.metadata:
                    del self.metadata[id]
            self.save_metadata()
            return True
        except Exception as e:
            error_context = {
                "operation": "delete_vectors",
                "id_count": len(ids)
            }
            self.logger.error(f"Error deleting vectors: {e}", extra=error_context)
            return False
        
    def cleanup(self):
        """Cleanup FAISS index resources"""
        self.logger.info("Cleaning up FAISS index resources", extra={
            "event": "faiss_cleanup_start",
            "index_path": self.index_path
        })
        
        try:
            # Save index and metadata before cleanup
            self.save_index()
            self.save_metadata()
            
            # Reset index
            if hasattr(self, 'index') and self.index is not None:
                # FAISS indexes don't have an explicit cleanup method
                # We just set the reference to None to allow garbage collection
                self.index = None
                
            # Clear metadata
            if hasattr(self, 'metadata') and self.metadata is not None:
                self.metadata.clear()
                
            self.logger.info("FAISS index resources cleaned up successfully", extra={
                "event": "faiss_cleanup_success",
                "index_path": self.index_path
            })
        except Exception as e:
            self.logger.error("Error cleaning up FAISS index resources", extra={
                "event": "faiss_cleanup_error",
                "index_path": self.index_path,
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise FileIOError(f"Error cleaning up FAISS index resources: {e}") from e

if __name__ == "__main__":
    # For testing purposes
    store = FAISSStore("/tmp/test_index.faiss")
    
    # Add some test vectors
    test_vectors = [
        [0.1, 0.2, 0.3] + [0.0] * 125,  # Pad to 128 dimensions
        [0.4, 0.5, 0.6] + [0.0] * 125,
        [0.7, 0.8, 0.9] + [0.0] * 125
    ]
    
    test_metadata = [
        {"id": "1", "content": "first sample"},
        {"id": "2", "content": "second sample"},
        {"id": "3", "content": "third sample"}
    ]
    
    success = store.add_vectors(test_vectors, test_metadata)
    
    # Search for similar vectors
    query = [0.15, 0.25, 0.35] + [0.0] * 125  # Pad to 128 dimensions
    results = store.search(query, k=3)
    
    # Delete a vector
    deleted = store.delete_vectors(["1"])
    
    print(f"Added: {success}")
    print(f"Search results: {len(results)} found")
    for result in results:
        print(f"  ID: {result['id']}, Distance: {result['distance']}")
    print(f"Deleted: {deleted}")