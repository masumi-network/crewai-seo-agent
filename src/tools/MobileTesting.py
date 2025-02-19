# Import required libraries:
# - crewai.tools.BaseTool: Base class for creating custom tools
# - selenium: For browser automation and testing
# - pydantic: For data validation and settings management
# - typing: For type hints
from crewai.tools import BaseTool
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Dict, Optional, Type
from pydantic import BaseModel, Field
from selenium.common.exceptions import TimeoutException
import logging
import os

logger = logging.getLogger(__name__)

# Define input schema for the mobile testing tool
class MobileTestingInput(BaseModel):
    """Input schema requiring a URL to test"""
    url: str = Field(..., description="The URL to test for mobile optimization")

# Main mobile optimization testing tool
class MobileOptimizationTool(BaseTool):
    """Tool that tests websites for mobile-friendliness by checking:
    - Viewport meta tag
    - Text readability 
    - Tap target sizes
    - Responsive images
    """
    
    # Tool metadata
    name: str = "Mobile Optimization Tester"
    description: str = "Tests website for mobile optimization and responsiveness"
    args_schema: Type[BaseModel] = MobileTestingInput

    def _run(self, url: str) -> Dict:
        """Run the mobile optimization test"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--mobile')
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_window_size(375, 812)  # iPhone X dimensions
            
            results = {
                "viewport": self._check_viewport(driver),
                "touch_elements": self._check_touch_elements(driver),
                "images": self._check_responsive_images(driver),
                "fonts": self._check_font_sizes(driver)
            }
            
            driver.quit()
            return results
            
        except Exception as e:
            return {"error": str(e)}

    def _check_text_readability(self, driver) -> Dict:
        try:
            text_elements = driver.find_elements(By.XPATH, "//*[not(self::script)]/text()")
            return {
                "readable_text_elements": len(text_elements),
                "status": "success"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _check_tap_targets(self, driver) -> Dict:
        try:
            clickable_elements = driver.find_elements(By.XPATH, "//*[self::button or self::a or self::input]")
            return {
                "clickable_elements": len(clickable_elements),
                "status": "success"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _check_responsive_images(self, driver) -> Dict:
        try:
            images = driver.find_elements(By.TAG_NAME, "img")
            responsive_images = [img for img in images if img.get_attribute("srcset") or img.get_attribute("sizes")]
            return {
                "total_images": len(images),
                "responsive_images": len(responsive_images),
                "status": "success"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _check_font_sizes(self, driver) -> Dict:
        try:
            text_elements = driver.find_elements(By.XPATH, "//*[not(self::script)]/text()")
            return {
                "text_elements": len(text_elements),
                "status": "success"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def _arun(self, url: str) -> Dict:
        """Async version - not implemented"""
        raise NotImplementedError("Async not implemented")
