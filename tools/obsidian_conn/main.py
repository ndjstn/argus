from typing import Dict, Any, List
import logging
import os
import json
from core.exceptions import FileIOError

class ObsidianConnector:
    """Connector for interacting with Obsidian vault with proper file handle management"""
    
    def __init__(self, vault_path: str):
        self.vault_path = vault_path
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initializing Obsidian Connector for vault: {vault_path}")
        
    def read_note(self, note_path: str) -> str:
        """Read a note from the vault with proper file handle management"""
        self.logger.info("Reading note", extra={
            "event": "obsidian_read_note_start",
            "note_path": note_path
        })
        
        file_handle = None
        try:
            full_path = os.path.join(self.vault_path, note_path)
            file_handle = open(full_path, 'r', encoding='utf-8')
            content = file_handle.read()
            self.logger.info("Note read successfully", extra={
                "event": "obsidian_read_note_success",
                "note_path": note_path,
                "content_length": len(content)
            })
            return content
        except FileNotFoundError as e:
            # This is expected if the note doesn't exist
            self.logger.info("Note file not found", extra={
                "event": "obsidian_read_note_not_found",
                "note_path": note_path
            })
            return ""
        except Exception as e:
            error_context = {
                "note_path": note_path,
                "operation": "read_note"
            }
            self.logger.error("Error reading note", extra={
                "event": "obsidian_read_note_error",
                "note_path": note_path,
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise FileIOError(f"Error reading note {note_path}: {e}", context=error_context) from e
        finally:
            # Ensure file handle is closed
            if file_handle:
                try:
                    file_handle.close()
                    self.logger.debug("File handle closed", extra={
                        "event": "obsidian_file_handle_closed",
                        "note_path": note_path
                    })
                except Exception as e:
                    self.logger.warning("Error closing file handle", extra={
                        "event": "obsidian_file_handle_close_error",
                        "note_path": note_path,
                        "error": str(e),
                        "error_type": type(e).__name__
                    })
        
    def write_note(self, note_path: str, content: str) -> bool:
        """Write a note to the vault with proper file handle management"""
        self.logger.info("Writing note", extra={
            "event": "obsidian_write_note_start",
            "note_path": note_path,
            "content_length": len(content)
        })
        
        file_handle = None
        try:
            full_path = os.path.join(self.vault_path, note_path)
            # Ensure directory exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            file_handle = open(full_path, 'w', encoding='utf-8')
            file_handle.write(content)
            file_handle.flush()  # Ensure content is written to disk
            os.fsync(file_handle.fileno())  # Force OS to write to disk
            
            self.logger.info("Note written successfully", extra={
                "event": "obsidian_write_note_success",
                "note_path": note_path,
                "content_length": len(content)
            })
            return True
        except Exception as e:
            error_context = {
                "note_path": note_path,
                "operation": "write_note"
            }
            self.logger.error("Error writing note", extra={
                "event": "obsidian_write_note_error",
                "note_path": note_path,
                "content_length": len(content) if content else 0,
                "error": str(e),
                "error_type": type(e).__name__
            })
            return False
        finally:
            # Ensure file handle is closed
            if file_handle:
                try:
                    file_handle.close()
                    self.logger.debug("File handle closed", extra={
                        "event": "obsidian_file_handle_closed",
                        "note_path": note_path
                    })
                except Exception as e:
                    self.logger.warning("Error closing file handle", extra={
                        "event": "obsidian_file_handle_close_error",
                        "note_path": note_path,
                        "error": str(e),
                        "error_type": type(e).__name__
                    })
        
    def search_notes(self, query: str) -> List[Dict[str, Any]]:
        """Search for notes in the vault"""
        self.logger.info(f"Searching notes for: {query}")
        
        try:
            results = []
            for root, dirs, files in os.walk(self.vault_path):
                for file in files:
                    if file.endswith('.md'):
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, self.vault_path)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                if query.lower() in content.lower():
                                    results.append({
                                        "path": relative_path,
                                        "content": content[:200] + "..." if len(content) > 200 else content
                                    })
                        except FileNotFoundError:
                            # This can happen if the file is deleted between os.walk and open
                            self.logger.info(f"File not found during search: {file_path}")
                        except Exception as e:
                            error_context = {
                                "file_path": file_path,
                                "operation": "search_notes_file_read"
                            }
                            self.logger.warning(f"Could not read file {file_path}: {e}", extra=error_context)
            
            return results
        except Exception as e:
            error_context = {
                "operation": "search_notes",
                "query": query
            }
            self.logger.error(f"Error searching notes: {e}", extra=error_context)
            return []

if __name__ == "__main__":
    # For testing purposes
    connector = ObsidianConnector("/path/to/vault")
    content = connector.read_note("sample_note.md")
    success = connector.write_note("sample_note.md", "# Sample Note\n\nThis is a sample note content.")
    
    if success:
        print("Note written successfully")
    else:
        print("Failed to write note")
    
    results = connector.search_notes("sample")
    print(f"Search results: {len(results)} found")