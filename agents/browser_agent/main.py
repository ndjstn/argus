from typing import Dict, Any
import logging
from tools.playwright_ctrl.main import PlaywrightController

class BrowserAgent:
    """Browser automation agent using Playwright"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Browser Agent")
        self.controller = PlaywrightController()
        
    def execute_task(self, task_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task using browser automation"""
        self.logger.info(f"Executing task: {task_spec}")
        
        # Extract parameters
        url = task_spec.get("url")
        actions = task_spec.get("actions", [])
        
        if not url:
            return {
                "status": "error",
                "task_id": task_spec.get("id", "unknown"),
                "error": "No URL provided in task specification"
            }
        
        try:
            # Navigate to the URL
            if not self.controller.navigate(url):
                return {
                    "status": "error",
                    "task_id": task_spec.get("id", "unknown"),
                    "error": f"Failed to navigate to {url}"
                }
            
            # Execute actions
            for action in actions:
                action_type = action.get("type")
                selector = action.get("selector")
                value = action.get("value")
                
                if action_type == "click" and selector:
                    if not self.controller.click_element(selector):
                        self.logger.warning(f"Failed to click element: {selector}")
                elif action_type == "fill" and selector and value:
                    if not self.controller.fill_form(selector, value):
                        self.logger.warning(f"Failed to fill form: {selector}")
            
            return {
                "status": "completed",
                "task_id": task_spec.get("id", "unknown"),
                "result": f"Successfully executed browser automation task on {url}"
            }
        except Exception as e:
            self.logger.error(f"Error executing browser task: {e}")
            return {
                "status": "error",
                "task_id": task_spec.get("id", "unknown"),
                "error": str(e)
            }

if __name__ == "__main__":
    # For testing purposes
    agent = BrowserAgent()
    result = agent.execute_task({
        "id": 1,
        "url": "https://example.com",
        "actions": [
            {"type": "click", "selector": "#sample-button"},
            {"type": "fill", "selector": "#sample-input", "value": "test value"}
        ]
    })
    print(result)