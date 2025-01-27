from crewai.tools import BaseTool
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Dict, Optional, Type
from pydantic import BaseModel, Field
from selenium.common.exceptions import TimeoutException

class MobileTestingInput(BaseModel):
    """Input for MobileOptimizationTool"""
    url: str = Field(..., description="The URL to test for mobile optimization")

class MobileOptimizationTool(BaseTool):
    """Tool for testing mobile optimization of websites"""
    
    name: str = Field(default="Mobile Optimization Tester", description="Name of the tool")
    description: str = Field(
        default="Tests website for mobile optimization including viewport, text readability, tap targets, and responsive images",
        description="Description of what the tool does"
    )
    args_schema: Type[BaseModel] = Field(default=MobileTestingInput, description="Schema for the tool's arguments")

    def __init__(self):
        super().__init__()

    def _run(self, url: str) -> str:
        """
        Run the mobile optimization test
        Args:
            url: The URL to test
        Returns:
            str: Analysis results
        """
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        try:
            # Setup Chrome options for mobile emulation
            mobile_emulation = {
                "deviceMetrics": { "width": 375, "height": 812, "pixelRatio": 3.0 },
                "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"
            }
            
            options = webdriver.ChromeOptions()
            options.add_experimental_option("mobileEmulation", mobile_emulation)
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')

            # Initialize the driver
            driver = webdriver.Chrome(options=options)
            driver.get(url)

            try:
                # Wait for page to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )

                # Check viewport meta tag
                viewport_meta = driver.find_elements(By.CSS_SELECTOR, 'meta[name="viewport"]')
                has_viewport = len(viewport_meta) > 0
                viewport_score = 100 if has_viewport else 0

                # Check text readability (font sizes)
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

                # Check tap targets
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

                # Check responsive images
                images = driver.find_elements(By.TAG_NAME, 'img')
                non_responsive = 0
                for img in images:
                    if not (img.get_attribute('srcset') or img.get_attribute('sizes')):
                        non_responsive += 1
                image_score = 100 - (non_responsive / max(len(images), 1) * 100)

                # Calculate overall score
                overall_score = (viewport_score + text_score + tap_target_score + image_score) / 4

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
                driver.quit()

        except Exception as e:
            return f"Error analyzing mobile optimization for {url}: {str(e)}"

    async def _arun(self, url: str) -> Dict:
        """Async implementation"""
        raise NotImplementedError("Async not implemented")
