from typing import Dict, Any
import logging
from tools.opencv_ops.main import OpenCVOps

class VisionAgent:
    """Vision processing agent using OpenCV"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Vision Agent")
        self.opencv_ops = OpenCVOps()
        
    def execute_task(self, task_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task using vision processing"""
        self.logger.info(f"Executing task: {task_spec}")
        
        # Extract parameters
        image_path = task_spec.get("image_path")
        operation = task_spec.get("operation", "detect_objects")
        
        if not image_path:
            return {
                "status": "error",
                "task_id": task_spec.get("id", "unknown"),
                "error": "No image path provided in task specification"
            }
        
        try:
            # Load image
            image = self.opencv_ops.load_image(image_path)
            if image is None:
                return {
                    "status": "error",
                    "task_id": task_spec.get("id", "unknown"),
                    "error": f"Failed to load image from {image_path}"
                }
            
            # Execute operation
            if operation == "detect_objects":
                result = self.opencv_ops.detect_objects(image)
                result_str = f"Detected {len(result)} objects"
            elif operation == "extract_text":
                result = self.opencv_ops.extract_text(image)
                result_str = f"Extracted text: {result}"
            else:
                result_str = "Unknown operation"
            
            return {
                "status": "completed",
                "task_id": task_spec.get("id", "unknown"),
                "result": result_str
            }
        except Exception as e:
            self.logger.error(f"Error executing vision task: {e}")
            return {
                "status": "error",
                "task_id": task_spec.get("id", "unknown"),
                "error": str(e)
            }

if __name__ == "__main__":
    # For testing purposes
    agent = VisionAgent()
    result = agent.execute_task({
        "id": 1,
        "image_path": "/path/to/image.png",
        "operation": "detect_objects"
    })
    print(result)