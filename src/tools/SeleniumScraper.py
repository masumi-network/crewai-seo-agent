from crewai.tools import BaseTool
from typing import Type, Optional, Dict
from pydantic import BaseModel, Field
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup

class SeleniumScraperInput(BaseModel):
    """Input for SeleniumScraper"""
    website_url: str = Field(..., description="The URL of the website to scrape")
    css_element: str = Field(default="body", description="CSS selector to target specific elements")
    wait_time: int = Field(default=5, description="Time to wait for elements to load")
    cookie: Optional[Dict] = Field(default=None, description="Cookie information for authentication")

class SeleniumScraper(BaseTool):
    name: str = "Selenium Web Scraper"
    description: str = """
    Scrapes website content using Selenium. Can target specific elements using CSS selectors.
    Examples:
    - Use css_element='meta' for meta tags
    - Use css_element='h1, h2, h3, h4, h5, h6' for headings
    - Use css_element='a' for links
    - Use css_element='img' for images
    - Use css_element='body' for full content
    """
    args_schema: Type[BaseModel] = SeleniumScraperInput

    def _run(self, website_url: str, css_element: str = "body", wait_time: int = 5, cookie: Optional[Dict] = None) -> str:
        try:
            # Setup Chrome options
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')

            # Initialize the driver
            driver = webdriver.Chrome(options=options)
            
            # Set cookie if provided
            if cookie:
                driver.get(website_url)
                driver.add_cookie(cookie)

            # Navigate to the URL
            driver.get(website_url)

            try:
                # Wait for elements to be present
                elements = WebDriverWait(driver, wait_time).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_element))
                )

                # Get the page source after JavaScript execution
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # Find all elements matching the CSS selector
                elements = soup.select(css_element)
                
                results = []
                for element in elements:
                    if element.name == 'meta':
                        attrs = {
                            'name': element.get('name', ''),
                            'content': element.get('content', ''),
                            'property': element.get('property', '')
                        }
                        results.append(f"Meta: {attrs}")
                    
                    elif element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        results.append(f"{element.name}: {element.text.strip()}")
                    
                    elif element.name == 'a':
                        href = element.get('href', '')
                        text = element.text.strip()
                        results.append(f"Link: {text} -> {href}")
                    
                    elif element.name == 'img':
                        src = element.get('src', '')
                        alt = element.get('alt', '')
                        results.append(f"Image: {src} (alt: {alt})")
                    
                    else:
                        results.append(element.text.strip())

                return "\n".join(filter(None, results))

            except TimeoutException:
                return f"Timeout waiting for elements matching selector: {css_element}"
            
            finally:
                driver.quit()

        except Exception as e:
            return f"Error scraping {website_url}: {str(e)}" 