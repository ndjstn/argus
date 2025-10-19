from typing import Dict, Any
import logging
from playwright.sync_api import sync_playwright
import time

class PlaywrightController:
    """Controller for Playwright browser automation with proper resource management"""
    
    def __init__(self, headless: bool = True):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Playwright Controller")
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.page = None
        self.context = None
        
    def __enter__(self):
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        
    def start(self):
        """Start the browser with proper error handling"""
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-extensions",
                    "--disable-background-timer-throttling",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-renderer-backgrounding"
                ]
            )
            self.context = self.browser.new_context(
                viewport={"width": 1920, "height": 1080}
            )
            self.page = self.context.new_page()
            self.logger.info("Browser started successfully", extra={
                "event": "playwright_browser_started",
                "headless": self.headless
            })
        except Exception as e:
            self.logger.error("Failed to start browser", extra={
                "event": "playwright_browser_start_failed",
                "headless": self.headless,
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise
            
    def stop(self):
        """Stop the browser with proper cleanup"""
        try:
            # Close page first
            if self.page:
                try:
                    self.page.close()
                    self.logger.debug("Page closed successfully", extra={
                        "event": "playwright_page_closed"
                    })
                except Exception as e:
                    self.logger.warning("Error closing page", extra={
                        "event": "playwright_page_close_error",
                        "error": str(e),
                        "error_type": type(e).__name__
                    })
                finally:
                    self.page = None
            
            # Close context
            if self.context:
                try:
                    self.context.close()
                    self.logger.debug("Context closed successfully", extra={
                        "event": "playwright_context_closed"
                    })
                except Exception as e:
                    self.logger.warning("Error closing context", extra={
                        "event": "playwright_context_close_error",
                        "error": str(e),
                        "error_type": type(e).__name__
                    })
                finally:
                    self.context = None
            
            # Close browser
            if self.browser:
                try:
                    self.browser.close()
                    self.logger.debug("Browser closed successfully", extra={
                        "event": "playwright_browser_closed"
                    })
                except Exception as e:
                    self.logger.warning("Error closing browser", extra={
                        "event": "playwright_browser_close_error",
                        "error": str(e),
                        "error_type": type(e).__name__
                    })
                finally:
                    self.browser = None
            
            # Stop Playwright
            if self.playwright:
                try:
                    self.playwright.stop()
                    self.logger.debug("Playwright stopped successfully", extra={
                        "event": "playwright_stopped"
                    })
                except Exception as e:
                    self.logger.warning("Error stopping Playwright", extra={
                        "event": "playwright_stop_error",
                        "error": str(e),
                        "error_type": type(e).__name__
                    })
                finally:
                    self.playwright = None
            
            self.logger.info("Browser stopped successfully", extra={
                "event": "playwright_browser_stopped"
            })
        except Exception as e:
            self.logger.error("Error during browser cleanup", extra={
                "event": "playwright_cleanup_error",
                "error": str(e),
                "error_type": type(e).__name__
            })
        
    def navigate(self, url: str) -> bool:
        """Navigate to a URL"""
        self.logger.info(f"Navigating to: {url}")
        
        try:
            if not self.page:
                self.start()
            self.page.goto(url)
            return True
        except Exception as e:
            self.logger.error(f"Failed to navigate to {url}: {e}")
            return False
        
    def click_element(self, selector: str) -> bool:
        """Click an element by selector"""
        self.logger.info(f"Clicking element: {selector}")
        
        try:
            if not self.page:
                self.start()
            self.page.click(selector)
            return True
        except Exception as e:
            self.logger.error(f"Failed to click element {selector}: {e}")
            return False
        
    def fill_form(self, selector: str, value: str) -> bool:
        """Fill a form field"""
        self.logger.info(f"Filling {selector} with {value}")
        
        try:
            if not self.page:
                self.start()
            self.page.fill(selector, value)
            return True
        except Exception as e:
            self.logger.error(f"Failed to fill {selector} with {value}: {e}")
            return False

if __name__ == "__main__":
    # For testing purposes
    with PlaywrightController() as controller:
        controller.navigate("https://example.com")
        controller.click_element("#sample-button")
        controller.fill_form("#sample-input", "test value")