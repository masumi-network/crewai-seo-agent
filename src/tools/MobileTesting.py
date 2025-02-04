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
    name: str = Field(default="Mobile Optimization Tester", description="Name of the tool")
    description: str = Field(
        default="Tests website for mobile optimization including viewport, text readability, tap targets, and responsive images",
        description="Description of what the tool does"
    )
    args_schema: Type[BaseModel] = Field(default=MobileTestingInput, description="Schema for the tool's arguments")

    def __init__(self):
        """Initialize the tool"""
        super().__init__()

    def _run(self, url: str) -> str:
        """
        Main method that runs the mobile optimization tests
        
        Args:
            url: Website URL to test
            
        Returns:
            str: Detailed analysis report with scores and recommendations
        """
        # Ensure URL has protocol
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        try:
            # Configure Chrome to emulate iPhone X
            mobile_emulation = {
                "deviceName": "iPhone X"
            }
            
            # Set up Chrome options for headless testing
            options = webdriver.ChromeOptions()
            options.add_experimental_option("mobileEmulation", mobile_emulation)
            options.add_argument('--headless')  # Run in background
            options.add_argument('--no-sandbox')  # Bypass OS security
            options.add_argument('--disable-dev-shm-usage')  # Handle limited resources
            options.add_argument('--disable-gpu')
            options.add_argument('--ignore-certificate-errors')
            
            # Initialize Chrome driver
            service = webdriver.ChromeService()
            driver = webdriver.Chrome(service=service, options=options)
            
            # Load the webpage
            driver.get(url)

            try:
                # Wait for page to load (max 10 seconds)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )

                # TEST 1: Check viewport meta tag
                # This tag is crucial for proper mobile scaling
                viewport_meta = driver.find_elements(By.CSS_SELECTOR, 'meta[name="viewport"]')
                has_viewport = len(viewport_meta) > 0
                viewport_score = 100 if has_viewport else 0

                # TEST 2: Check text readability
                # Find text elements and check font sizes (should be >= 12px)
                text_elements = driver.find_elements(By.CSS_SELECTOR, 'p, span, div, a')
                small_text = 0
                for element in text_elements:
                    try:
                        font_size = int(element.value_of_css_property('font-size').replace('px', ''))
                        if font_size < 12:
                            small_text += 1
                    except:
                        continue
                text_score = 100 - (small_text / max(len(text_elements), 1) * 100)

                # TEST 3: Check tap targets
                # Interactive elements should be at least 44x44px
                clickable_elements = driver.find_elements(By.CSS_SELECTOR, 'a, button, input, select, textarea')
                small_targets = 0
                for element in clickable_elements:
                    try:
                        width = int(element.value_of_css_property('width').replace('px', ''))
                        height = int(element.value_of_css_property('height').replace('px', ''))
                        if width < 44 or height < 44:
                            small_targets += 1
                    except:
                        continue
                tap_target_score = 100 - (small_targets / max(len(clickable_elements), 1) * 100)

                # TEST 4: Check responsive images
                # Images should use srcset/sizes for responsiveness
                images = driver.find_elements(By.TAG_NAME, 'img')
                non_responsive = 0
                for img in images:
                    if not (img.get_attribute('srcset') or img.get_attribute('sizes')):
                        non_responsive += 1
                image_score = 100 - (non_responsive / max(len(images), 1) * 100)

                # Calculate overall score (average of all tests)
                overall_score = (viewport_score + text_score + tap_target_score + image_score) / 4

                # Generate detailed report with scores and recommendations
                return f"""
Mobile Optimization Analysis:

1. Viewport Meta Tag: {'Present' if has_viewport else 'Missing'} ({viewport_score}%)
2. Text Readability Score: {text_score:.1f}%
   - Total text elements: {len(text_elements)}
   - Elements with small text: {small_text}

3. Tap Target Spacing Score: {tap_target_score:.1f}%
   - Total clickable elements: {len(clickable_elements)}
   - Elements with small tap targets: {small_targets}

4. Responsive Images Score: {image_score:.1f}%
   - Total images: {len(images)}
   - Non-responsive images: {non_responsive}

5. Overall Mobile Score: {overall_score:.1f}%

Recommendations:
{f'- Add viewport meta tag for proper mobile scaling' if not has_viewport else ''}
{f'- Increase font size for {small_text} elements' if small_text > 0 else ''}
{f'- Increase tap target size for {small_targets} elements' if small_targets > 0 else ''}
{f'- Add responsive image attributes for {non_responsive} images' if non_responsive > 0 else ''}
"""

            except TimeoutException:
                return f"Timeout while analyzing mobile optimization for {url}"
            
            finally:
                # Always close the browser
                driver.quit()

        except Exception as e:
            return f"Error analyzing mobile optimization for {url}: {str(e)}"

    async def _arun(self, url: str) -> Dict:
        """Async version - not implemented"""
        raise NotImplementedError("Async not implemented")
