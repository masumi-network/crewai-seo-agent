from crewai.tools import BaseTool
from typing import Type, Optional, Dict, List
from pydantic import BaseModel, Field
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET
from collections import defaultdict
import re
import time
import os

class SubpageAnalyzerInput(BaseModel):
    """Input parameters for subpage analysis"""
    website_url: str = Field(..., description="The URL of the website to analyze")
    max_pages: int = Field(default=50, description="Maximum number of subpages to analyze")
    min_content_length: int = Field(default=500, description="Minimum content length to consider")

class SubpageAnalyzer(BaseTool):
    name: str = "Subpage Analyzer"
    description: str = """
    Analyzes website subpages by:
    - Finding all accessible pages
    - Analyzing content quality
    - Measuring user engagement signals
    - Ranking pages by importance
    """
    args_schema: Type[BaseModel] = SubpageAnalyzerInput

    def _run(self, website_url: str, max_pages: int = 50, min_content_length: int = 500) -> str:
        try:
            # Get base domain
            parsed_url = urlparse(website_url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Collect subpages
            subpages = self._find_subpages(base_url, max_pages)
            
            # Analyze each subpage
            analyzed_pages = self._analyze_subpages(subpages, min_content_length)
            
            # Rank and format results
            return self._format_results(analyzed_pages)
            
        except Exception as e:
            return f"Error analyzing subpages: {str(e)}"

    def _find_subpages(self, base_url: str, max_pages: int) -> List[str]:
        """Finds subpages through sitemap and crawling"""
        subpages = set()
        
        try:
            # Try sitemap first
            sitemap_urls = [
                f"{base_url}/sitemap.xml",
                f"{base_url}/sitemap_index.xml",
                f"{base_url}/sitemap/sitemap.xml"
            ]
            
            for sitemap_url in sitemap_urls:
                try:
                    response = requests.get(sitemap_url, timeout=10)
                    if response.status_code == 200:
                        root = ET.fromstring(response.content)
                        for url in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
                            subpages.add(url.text)
                            if len(subpages) >= max_pages:
                                return list(subpages)
                except:
                    continue
            
            # If sitemap didn't provide enough pages, crawl the website
            if len(subpages) < max_pages:
                subpages.update(self._crawl_pages(base_url, max_pages - len(subpages)))
            
            return list(subpages)[:max_pages]
            
        except Exception as e:
            return []

    def _crawl_pages(self, base_url: str, max_pages: int) -> List[str]:
        """Crawls website to find subpages using browserless"""
        found_pages = set()
        to_crawl = {base_url}
        crawled = set()
        
        browserless_api_key = os.getenv('BROWSERLESS_API_KEY')
        scrape_url = f'https://chrome.browserless.io/content?token={browserless_api_key}'
        
        # Add error handling for rate limits
        retry_count = 0
        max_retries = 3
        
        while to_crawl and len(found_pages) < max_pages and retry_count < max_retries:
            try:
                url = to_crawl.pop()
                if url in crawled:
                    continue
                
                payload = {
                    'url': url,
                    'gotoOptions': {
                        'waitUntil': 'domcontentloaded',
                        'timeout': 20000
                    }
                }
                
                response = requests.post(
                    scrape_url,
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=25
                )
                
                if response.status_code == 429:  # Rate limit
                    print("Rate limit hit, waiting...")
                    time.sleep(2)
                    to_crawl.add(url)  # Put URL back in queue
                    retry_count += 1
                    continue
                    
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find all links
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        full_url = urljoin(base_url, href)
                        
                        # Only include URLs from same domain
                        if (urlparse(full_url).netloc == urlparse(base_url).netloc and
                            not full_url.endswith(('.pdf', '.jpg', '.png', '.gif'))):
                            found_pages.add(full_url)
                            if full_url not in crawled:
                                to_crawl.add(full_url)
                                
                    crawled.add(url)
                    time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"Error crawling {url}: {str(e)}")
                retry_count += 1
                continue
                
        return list(found_pages)[:max_pages]  # Ensure we don't exceed max_pages

    def _calculate_authority_score(self, domains: set) -> float:
        """Calculates domain authority score"""
        try:
            if not domains:  # If no domains found
                return 0.0
            edu_gov_org = sum(1 for d in domains if any(ext in d for ext in ['.edu', '.gov', '.org']))
            return min(100, (edu_gov_org / len(domains)) * 100)
        except ZeroDivisionError:
            return 0.0

    def _analyze_subpages(self, urls: List[str], min_content_length: int) -> List[Dict]:
        """Analyzes each subpage using browserless"""
        analyzed_pages = []
        browserless_api_key = os.getenv('BROWSERLESS_API_KEY')
        scrape_url = f'https://chrome.browserless.io/content?token={browserless_api_key}'
        
        for url in urls:
            try:
                payload = {
                    'url': url,
                    'gotoOptions': {
                        'waitUntil': 'networkidle0',
                        'timeout': 30000
                    }
                }
                
                response = requests.post(
                    scrape_url,
                    json=payload,
                    headers={
                        'Content-Type': 'application/json',
                        'Cache-Control': 'no-cache'
                    },
                    timeout=45
                )
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    content = self._extract_main_content(soup)
                    
                    if len(content) < min_content_length:
                        continue
                    
                    page_metrics = {
                        'url': url,
                        'title': soup.title.string if soup.title else 'No title',
                        'content_length': len(content),
                        'headings': len(soup.find_all(['h1', 'h2', 'h3'])),
                        'images': len(soup.find_all('img')),
                        'internal_links': len([l for l in soup.find_all('a', href=True) 
                                            if not l['href'].startswith(('http', 'https'))]),
                        'external_links': len([l for l in soup.find_all('a', href=True) 
                                            if l['href'].startswith(('http', 'https'))]),
                        'importance_score': 0
                    }
                    
                    page_metrics['importance_score'] = self._calculate_importance(page_metrics)
                    analyzed_pages.append(page_metrics)
                
            except Exception as e:
                continue
        
        return analyzed_pages

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extracts main content from page, excluding navigation, footer, etc."""
        # Remove unwanted elements
        for element in soup.find_all(['nav', 'footer', 'header', 'aside']):
            element.decompose()
        
        # Try to find main content area
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main|article'))
        
        if main_content:
            return main_content.get_text()
        return soup.get_text()

    def _calculate_importance(self, metrics: Dict) -> float:
        """Calculates page importance based on various metrics"""
        score = 0.0
        
        # Content length (up to 20 points)
        score += min(metrics['content_length'] / 1000, 20)
        
        # Headings (up to 10 points)
        score += min(metrics['headings'] * 2, 10)
        
        # Images (up to 5 points)
        score += min(metrics['images'], 5)
        
        # Internal links (up to 5 points)
        score += min(metrics['internal_links'] / 2, 5)
        
        # External links (up to 5 points)
        score += min(metrics['external_links'], 5)
        
        # URL depth penalty (deeper pages get lower scores)
        depth = metrics['url'].count('/') - 3  # Subtract http://domain.com/
        score -= depth if depth > 0 else 0
        
        return max(score, 0)  # Ensure non-negative score

    def _format_results(self, analyzed_pages: List[Dict]) -> str:
        """Formats analysis results into a readable report"""
        if not analyzed_pages:
            return "No subpages found or analysis failed"
            
        # Sort pages by importance score
        sorted_pages = sorted(analyzed_pages, key=lambda x: x['importance_score'], reverse=True)
        
        report = ["=== Top Subpages Analysis ===\n"]
        
        if sorted_pages[0]['url'] in ['No subpages found', 'Analysis failed']:
            report.append("No accessible subpages found or analysis failed")
            return "\n".join(report)
        
        for i, page in enumerate(sorted_pages[:10], 1):
            report.append(f"{i}. {page['title']}")
            report.append(f"   URL: {page['url']}")
            report.append(f"   Metrics:")
            report.append(f"   - Content Length: {page['content_length']} characters")
            report.append(f"   - Headings: {page['headings']}")
            report.append(f"   - Images: {page['images']}")
            report.append(f"   - Internal Links: {page['internal_links']}")
            report.append(f"   - External Links: {page['external_links']}")
            report.append(f"   - Importance Score: {page['importance_score']:.2f}\n")
        
        # Add summary statistics
        if len(analyzed_pages) > 0:
            avg_score = sum(p['importance_score'] for p in analyzed_pages) / len(analyzed_pages)
            report.append(f"\nAnalysis Summary:")
            report.append(f"- Total Pages Analyzed: {len(analyzed_pages)}")
            report.append(f"- Average Importance Score: {avg_score:.2f}")
        
        return "\n".join(report) 