from crewai.tools import BaseTool
from typing import Type, Optional, Dict, Union
from pydantic import BaseModel, Field
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from collections import Counter
import re
import time

# This class defines the expected input parameters for the scraper
class SeleniumScraperInput(BaseModel):
    """Input for SeleniumScraper"""
    website_url: str = Field(..., description="The URL of the website to scrape")  # Required URL parameter
    css_element: str = Field(default="body", description="CSS selector to target specific elements")  # Optional CSS selector, defaults to body
    wait_time: int = Field(default=5, description="Time to wait for elements to load")  # Optional wait time, defaults to 5 seconds
    cookie: Optional[Dict] = Field(default=None, description="Cookie information for authentication")  # Optional cookie data

# Main scraper class that inherits from BaseTool
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
            # Clean up the URL
            website_url = website_url.strip('"')
            if not website_url.startswith(('http://', 'https://')):
                website_url = 'https://' + website_url

            # Configure Chrome browser options for headless operation
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')  # Run browser in background
            options.add_argument('--no-sandbox')  # Bypass OS security model
            options.add_argument('--disable-dev-shm-usage')  # Overcome limited resource problems
            options.add_argument('--disable-gpu')  # Disable GPU hardware acceleration
            options.add_argument('--ignore-certificate-errors')  # Ignore SSL/TLS errors
            options.add_argument('--disable-extensions')  # Disable browser extensions
            options.add_argument('--disable-web-security')  # Disable web security
            options.add_argument('--allow-running-insecure-content')  # Allow mixed content
            options.add_argument('--window-size=1920,1080')  # Set window size
            options.page_load_strategy = 'eager'  # Don't wait for all resources to load
            
            # Set a realistic user agent to avoid detection
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

            # Initialize Chrome driver
            service = webdriver.ChromeService()
            driver = webdriver.Chrome(service=service, options=options)
            
            try:
                # Set timeouts for page load and script execution
                driver.set_page_load_timeout(wait_time)
                driver.set_script_timeout(wait_time)
                
                # Load the webpage
                driver.get(website_url)
                
                # Add cookies if provided
                if cookie and isinstance(cookie, dict):
                    for name, value in cookie.items():
                        driver.add_cookie({'name': name, 'value': value})
                    driver.refresh()  # Refresh page with new cookies
                
                # Wait for the body element to be present
                WebDriverWait(driver, wait_time).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Get and parse the page HTML
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                results = []
                
                # Enhanced meta tag analysis
                meta_tags = soup.find_all('meta')
                meta_analysis = {}
                for tag in meta_tags:
                    tag_type = tag.get('name', tag.get('property', 'other'))
                    meta_analysis[tag_type] = meta_analysis.get(tag_type, 0) + 1
                
                results.append("=== Meta Tag Analysis ===")
                for tag_type, count in meta_analysis.items():
                    results.append(f"Meta tag '{tag_type}': {count}")
                
                # Word frequency analysis
                text_content = soup.get_text()
                words = re.findall(r'\b\w+\b', text_content.lower())
                word_freq = Counter(words).most_common(20)  # Get top 20 words
                
                results.append("\n=== Word Frequency Analysis ===")
                results.append("Most frequent words (excluding common stop words):")
                stop_words = {'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at'}
                for word, count in word_freq:
                    if word not in stop_words and len(word) > 2:
                        results.append(f"'{word}': {count} occurrences")
                
                # Extract all heading levels (h1-h6) and their text
                for level in range(1, 7):
                    headings = soup.find_all(f'h{level}')
                    for heading in headings:
                        results.append(f"h{level}: {heading.text.strip()}")
                
                # Extract links with their text and href attributes
                links = soup.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    text = link.text.strip()
                    results.append(f"Link: {text} -> {href}")
                
                # Extract images with their src and alt attributes
                images = soup.find_all('img')
                for img in images:
                    src = img.get('src', '')
                    alt = img.get('alt', '')
                    results.append(f"Image: {src} (alt: {alt})")
                
                return "\n".join(filter(None, results))
                
            except Exception as e:
                return f"Error processing page: {str(e)}"
            
            finally:
                # Always close the browser
                driver.quit()

        except Exception as e:
            return f"Error initializing scraper: {str(e)}" 