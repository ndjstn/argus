from typing import Dict, Any, List
import logging
from taskw import TaskWarrior
from taskw.exceptions import TaskwarriorError
import os
import time
from .exceptions import FileIOError

class TaskwarriorAdapter:
    """Adapter for interacting with Taskwarrior"""
    
    def __init__(self, taskrc_path: str = None):
        self.logger = logging.getLogger(__name__)
        self.operation_count = 0
        self.logger.info("Initializing Taskwarrior Adapter")
        
        # Initialize TaskWarrior client
        if taskrc_path:
            try:
                self.tw = TaskWarrior(config_filename=taskrc_path)
            except Exception as e:
                self.logger.error("Error initializing TaskWarrior with specified taskrc path", extra={
                    "event": "taskwarrior_init_error",
                    "taskrc_path": taskrc_path,
                    "error": str(e)
                })
                raise FileIOError(f"Failed to initialize TaskWarrior with taskrc path: {taskrc_path}") from e
        else:
            # Look for taskrc in standard locations
            taskrc_locations = [
                os.path.expanduser("~/.taskrc"),
                "/etc/taskrc"
            ]
            
            found_taskrc = None
            for location in taskrc_locations:
                try:
                    if os.path.exists(location):
                        found_taskrc = location
                        break
                except Exception as e:
                    self.logger.warning("Error checking taskrc location", extra={
                        "event": "taskwarrior_taskrc_check_error",
                        "location": location,
                        "error": str(e)
                    })
                    continue
            
            if found_taskrc:
                try:
                    self.tw = TaskWarrior(config_filename=found_taskrc)
                except Exception as e:
                    self.logger.error("Error initializing TaskWarrior with found taskrc", extra={
                        "event": "taskwarrior_init_error",
                        "taskrc_path": found_taskrc,
                        "error": str(e)
                    })
                    raise FileIOError(f"Failed to initialize TaskWarrior with found taskrc: {found_taskrc}") from e
            else:
                # Use default configuration
                try:
                    self.tw = TaskWarrior()
                except Exception as e:
                    self.logger.error("Error initializing TaskWarrior with default configuration", extra={
                        "event": "taskwarrior_init_error",
                        "error": str(e)
                    })
                    raise FileIOError("Failed to initialize TaskWarrior with default configuration") from e
        
    def get_tasks(self, filter: str = None) -> List[Dict[str, Any]]:
        """Get tasks from Taskwarrior"""
        start_time = time.time()
        self.operation_count += 1
        
        self.logger.debug("Fetching tasks from Taskwarrior", extra={
            "event": "taskwarrior_get_tasks_start",
            "filter": filter,
            "operation_count": self.operation_count
        })
        
        try:
            if filter:
                tasks = self.tw.filter_tasks({"status": "pending", "description.contains": filter})
            else:
                tasks = self.tw.load_tasks()
            
            # Extract pending tasks
            pending_tasks = tasks.get("pending", [])
            task_count = len(pending_tasks)
            
            # Convert to our internal format
            converted_tasks = []
            for task in pending_tasks:
                converted_task = {
                    "id": task.get("id"),
                    "tw_uuid": task.get("uuid"),
                    "description": task.get("description"),
                    "project": task.get("project"),
                    "tags": task.get("tags", []),
                    "priority": task.get("priority"),
                    "urgency": task.get("urgency"),
                    "status": task.get("status", "pending"),
                    "created_ts": self._parse_date(task.get("entry")),
                    "due_ts": self._parse_date(task.get("due")),
                    "updated_ts": self._parse_date(task.get("modified"))
                }
                converted_tasks.append(converted_task)
            
            operation_time = time.time() - start_time
            self.logger.info("Tasks fetched successfully from Taskwarrior", extra={
                "event": "taskwarrior_get_tasks_success",
                "task_count": task_count,
                "filter": filter,
                "operation_time_ms": round(operation_time * 1000, 2),
                "operation_count": self.operation_count
            })
            
            return converted_tasks
        except TaskwarriorError as e:
            operation_time = time.time() - start_time
            # Use the string representation provided by the taskw library
            error_msg = f"TaskwarriorError: {str(e)}"
            self.logger.error("Error fetching tasks from Taskwarrior", extra={
                "event": "taskwarrior_get_tasks_error",
                "filter": filter,
                "error": error_msg,
                "operation_time_ms": round(operation_time * 1000, 2),
                "operation_count": self.operation_count
            })
            return []
        except Exception as e:
            operation_time = time.time() - start_time
            # Handle other exceptions
            error_msg = str(e)
            if isinstance(error_msg, bytes):
                error_msg = error_msg.decode('utf-8', errors='replace')
            self.logger.error("Error fetching tasks from Taskwarrior", extra={
                "event": "taskwarrior_get_tasks_error",
                "filter": filter,
                "error": error_msg,
                "operation_time_ms": round(operation_time * 1000, 2),
                "operation_count": self.operation_count
            })
            return []
    
    def create_task(self, description: str, project: str = None, tags: List[str] = None, due: str = None) -> Dict[str, Any]:
        """Create a new task in Taskwarrior"""
        start_time = time.time()
        self.operation_count += 1
        
        self.logger.debug("Creating new task in Taskwarrior", extra={
            "event": "taskwarrior_create_task_start",
            "description": description,
            "project": project,
            "tags": tags,
            "due": due,
            "operation_count": self.operation_count
        })
        
        try:
            # Prepare task data
            task_data = {
                "description": description
            }
            
            if project:
                task_data["project"] = project
                
            if tags:
                task_data["tags"] = tags
                
            if due:
                task_data["due"] = due
            
            # Create task
            task = self.tw.task_add(**task_data)
            
            # Convert to our internal format
            converted_task = {
                "id": task.get("id"),
                "tw_uuid": task.get("uuid"),
                "description": task.get("description"),
                "project": task.get("project"),
                "tags": task.get("tags", []),
                "priority": task.get("priority"),
                "urgency": task.get("urgency"),
                "status": task.get("status", "pending"),
                "created_ts": self._parse_date(task.get("entry")),
                "due_ts": self._parse_date(task.get("due")),
                "updated_ts": self._parse_date(task.get("modified"))
            }
            
            operation_time = time.time() - start_time
            self.logger.info("Task created successfully in Taskwarrior", extra={
                "event": "taskwarrior_create_task_success",
                "task_id": converted_task.get("id"),
                "task_uuid": converted_task.get("tw_uuid"),
                "description": description,
                "project": project,
                "tags_count": len(tags) if tags else 0,
                "operation_time_ms": round(operation_time * 1000, 2),
                "operation_count": self.operation_count
            })
            
            return converted_task
        except TaskwarriorError as e:
            operation_time = time.time() - start_time
            # Use the string representation provided by the taskw library
            error_msg = f"TaskwarriorError: {e.stderr.decode('utf-8') if isinstance(e.stderr, bytes) else e.stderr}"
            self.logger.error("Error creating task in Taskwarrior", extra={
                "event": "taskwarrior_create_task_error",
                "description": description,
                "project": project,
                "error": error_msg,
                "operation_time_ms": round(operation_time * 1000, 2),
                "operation_count": self.operation_count
            })
            return {}
        except Exception as e:
            operation_time = time.time() - start_time
            # Handle other exceptions
            error_msg = str(e)
            if isinstance(error_msg, bytes):
                error_msg = error_msg.decode('utf-8', errors='replace')
            self.logger.error("Error creating task in Taskwarrior", extra={
                "event": "taskwarrior_create_task_error",
                "description": description,
                "project": project,
                "error": error_msg,
                "operation_time_ms": round(operation_time * 1000, 2),
                "operation_count": self.operation_count
            })
            return {}
    
    def update_task(self, uuid: str, status: str = None, annotations: List[str] = None) -> Dict[str, Any]:
        """Update a task in Taskwarrior"""
        start_time = time.time()
        self.operation_count += 1
        
        self.logger.debug("Updating task in Taskwarrior", extra={
            "event": "taskwarrior_update_task_start",
            "uuid": uuid,
            "status": status,
            "annotations_count": len(annotations) if annotations else 0,
            "operation_count": self.operation_count
        })
        
        try:
            # Prepare update data
            update_data = {}
            
            if status:
                update_data["status"] = status
                
            # Update task
            self.tw.task_update(uuid, **update_data)
            
            # Add annotations if provided
            annotation_count = 0
            if annotations:
                task = self.tw.get_task(uuid)[1]
                for annotation in annotations:
                    self.tw.task_annotate(task, annotation)
                    annotation_count += 1
            
            # Fetch updated task
            _, task = self.tw.get_task(uuid)
            
            # Convert to our internal format
            converted_task = {
                "id": task.get("id"),
                "tw_uuid": task.get("uuid"),
                "description": task.get("description"),
                "project": task.get("project"),
                "tags": task.get("tags", []),
                "priority": task.get("priority"),
                "urgency": task.get("urgency"),
                "status": task.get("status", "pending"),
                "created_ts": self._parse_date(task.get("entry")),
                "due_ts": self._parse_date(task.get("due")),
                "updated_ts": self._parse_date(task.get("modified"))
            }
            
            operation_time = time.time() - start_time
            self.logger.info("Task updated successfully in Taskwarrior", extra={
                "event": "taskwarrior_update_task_success",
                "task_id": converted_task.get("id"),
                "task_uuid": converted_task.get("tw_uuid"),
                "status": status,
                "annotations_count": annotation_count,
                "operation_time_ms": round(operation_time * 1000, 2),
                "operation_count": self.operation_count
            })
            
            return converted_task
        except TaskwarriorError as e:
            operation_time = time.time() - start_time
            # Use the string representation provided by the taskw library
            error_msg = f"TaskwarriorError: {str(e)}"
            self.logger.error("Error updating task in Taskwarrior", extra={
                "event": "taskwarrior_update_task_error",
                "uuid": uuid,
                "status": status,
                "error": error_msg,
                "operation_time_ms": round(operation_time * 1000, 2),
                "operation_count": self.operation_count
            })
            return {}
        except Exception as e:
            operation_time = time.time() - start_time
            # Handle other exceptions
            error_msg = str(e)
            if isinstance(error_msg, bytes):
                error_msg = error_msg.decode('utf-8', errors='replace')
            self.logger.error("Error updating task in Taskwarrior", extra={
                "event": "taskwarrior_update_task_error",
                "uuid": uuid,
                "status": status,
                "error": error_msg,
                "operation_time_ms": round(operation_time * 1000, 2),
                "operation_count": self.operation_count
            })
            return {}
    
    def _parse_date(self, date_str: str) -> int:
        """Parse a date string into a timestamp"""
        if not date_str:
            return None
            
        try:
            from datetime import datetime
            dt = datetime.strptime(date_str, "%Y%m%dT%H%M%SZ")
            return int(dt.timestamp())
        except Exception as e:
            self.logger.warning("Error parsing date", extra={
                "event": "taskwarrior_date_parse_warning",
                "date_str": date_str,
                "error": str(e)
            })
            return None
            
    def get_adapter_info(self) -> Dict[str, Any]:
        """Get information about the Taskwarrior adapter for monitoring"""
        return {
            "operation_count": self.operation_count
        }

if __name__ == "__main__":
    # For testing purposes
    adapter = TaskwarriorAdapter()
    
    # Get tasks
    tasks = adapter.get_tasks()
    print(f"Found {len(tasks)} tasks")
    
    # Create a test task
    new_task = adapter.create_task("Test task from adapter", project="test", tags=["test", "adapter"])
    print(f"Created task: {new_task}")
    
    # Update the task
    if new_task and "tw_uuid" in new_task:
        updated_task = adapter.update_task(new_task["tw_uuid"], status="completed")
        print(f"Updated task: {updated_task}")