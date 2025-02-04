from crewai.tools import BaseTool
from typing import Type, Optional, Dict, Union
from pydantic import BaseModel, Field
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from collections import Counter, defaultdict
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
        """
        Runs the scraper with the given parameters
        """
        try:
            # Clean up URL
            website_url = website_url.strip('"')
            if not website_url.startswith(('http://', 'https://')):
                website_url = 'https://' + website_url

            # Configure Chrome options
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            # Initialize driver
            driver = webdriver.Chrome(options=options)
            
            try:
                # Set page load timeout
                driver.set_page_load_timeout(wait_time)
                
                # Load the page
                driver.get(website_url)
                
                # Wait for elements to load
                WebDriverWait(driver, wait_time).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, css_element))
                )
                
                # Get page source and parse
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                # Analyze different elements
                analysis = {
                    'meta_tags': self._analyze_meta_tags(soup),
                    'headings': self._analyze_headings(soup),
                    'keywords': self._analyze_keywords(soup),
                    'links': self._analyze_links(soup, website_url),
                    'images': self._analyze_images(soup)
                }
                
                return self._format_results(analysis)
                
            finally:
                driver.quit()
                
        except Exception as e:
            return f"Error scraping website: {str(e)}"

    def _analyze_meta_tags(self, soup: BeautifulSoup) -> Dict:
        """Analyzes meta tags"""
        meta_tags = soup.find_all('meta')
        meta_analysis = defaultdict(int)
        meta_descriptions = []
        
        for tag in meta_tags:
            tag_type = tag.get('name', tag.get('property', 'other'))
            meta_analysis[tag_type] += 1
            if tag_type == 'description':
                meta_descriptions.append(tag.get('content', ''))
                
        return {
            'counts': dict(meta_analysis),
            'descriptions': meta_descriptions
        }

    def _analyze_keywords(self, soup: BeautifulSoup) -> Dict:
        """Analyzes keyword frequency and density"""
        # Get text content
        text = soup.get_text()
        
        # Clean and tokenize
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Count frequencies
        word_freq = Counter(words)
        total_words = len(words)
        
        # Calculate density
        keyword_density = {
            word: (count / total_words) * 100 
            for word, count in word_freq.most_common(20)
        }
        
        return {
            'frequencies': dict(word_freq.most_common(20)),
            'density': keyword_density,
            'total_words': total_words
        }

    def _analyze_headings(self, soup: BeautifulSoup) -> Dict:
        """Analyzes headings"""
        headings = {}
        for level in range(1, 7):
            headings[f'h{level}'] = [heading.text.strip() for heading in soup.find_all(f'h{level}')]
        return headings

    def _analyze_links(self, soup: BeautifulSoup, website_url: str) -> Dict:
        """Analyzes links"""
        links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.text.strip()
            links.append(f"{text} -> {href}")
        return links

    def _analyze_images(self, soup: BeautifulSoup) -> Dict:
        """Analyzes images"""
        images = []
        for img in soup.find_all('img'):
            src = img.get('src', '')
            alt = img.get('alt', '')
            images.append(f"Image: {src} (alt: {alt})")
        return images

    def _format_results(self, analysis: Dict) -> str:
        """Formats the results"""
        results = []
        for element, data in analysis.items():
            if isinstance(data, dict):
                results.append(f"=== {element.replace('_', ' ').capitalize()} ===")
                for key, value in data.items():
                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            results.append(f"{key.capitalize()}: {sub_key} - {sub_value}")
                    else:
                        results.append(f"{key.capitalize()}: {value}")
            else:
                results.append(f"=== {element.replace('_', ' ').capitalize()} ===")
                results.append(str(data))
        return "\n".join(results) 