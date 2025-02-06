from crewai.tools import BaseTool
from typing import Type, Optional, Dict
from pydantic import BaseModel, Field
from bs4 import BeautifulSoup
from collections import Counter, defaultdict
import requests
import json
import os
import re
from urllib.parse import urlparse

class BrowserlessScraperInput(BaseModel):
    """Input for BrowserlessScraper"""
    website_url: str = Field(..., description="The URL of the website to scrape")
    wait_time: int = Field(default=5, description="Time to wait for elements to load in seconds")

class BrowserlessScraper(BaseTool):
    name: str = "Browserless Web Scraper"
    description: str = """
    Scrapes website content using browserless.io API. Analyzes:
    - Meta tags and SEO elements
    - Content structure (headings, paragraphs)
    - Links (internal and external)
    - Images and media
    - Keyword frequency and density
    """
    args_schema: Type[BaseModel] = BrowserlessScraperInput

    def _run(self, website_url: str, wait_time: int = 5) -> str:
        """Runs the scraper with the given parameters"""
        try:
            # Clean up URL
            website_url = website_url.strip('"')
            if not website_url.startswith(('http://', 'https://')):
                website_url = 'https://' + website_url

            # Configure scraping request with shorter timeout
            scrape_url = f'https://chrome.browserless.io/content?token={os.getenv("BROWSERLESS_API_KEY")}'
            
            payload = {
                'url': website_url,
                'gotoOptions': {
                    'waitUntil': 'domcontentloaded',  # Changed from networkidle0 for faster loading
                    'timeout': 15000  # Reduced from 30000
                }
            }

            response = requests.post(
                scrape_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=20  # Reduced from 45
            )

            if response.status_code != 200:
                return f"Error: Browserless returned status code {response.status_code}. Response: {response.text}"

            # Parse HTML content directly from response
            html_content = response.text
            if not html_content or len(html_content) < 100:  # Basic validation
                return "Error: Received empty or invalid response from browserless"

            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Verify we got actual HTML content
            if not soup.find('html'):
                return "Error: No HTML content found in response"

            # Analyze page elements
            analysis = {
                'meta_tags': self._analyze_meta_tags(soup),
                'headings': self._analyze_headings(soup),
                'keywords': self._analyze_keywords(soup),
                'links': self._analyze_links(soup, website_url),
                'images': self._analyze_images(soup),
                'content_stats': self._analyze_content(soup)
            }

            return self._format_results(analysis)

        except requests.Timeout:
            return "Error: Request to browserless timed out. The server might be busy, please try again."
        except requests.ConnectionError:
            return "Error: Could not connect to browserless. Please check your internet connection."
        except Exception as e:
            return f"Error scraping website: {str(e)}"

    def _analyze_meta_tags(self, soup: BeautifulSoup) -> Dict:
        """Analyzes meta tags and their content"""
        meta_tags = soup.find_all('meta')
        meta_analysis = defaultdict(list)
        
        for tag in meta_tags:
            name = tag.get('name', tag.get('property', ''))
            content = tag.get('content', '')
            if name and content:
                meta_analysis[name].append(content)
        
        return dict(meta_analysis)

    def _analyze_headings(self, soup: BeautifulSoup) -> Dict:
        """Analyzes heading structure and content"""
        headings = {}
        for level in range(1, 7):
            h_tags = soup.find_all(f'h{level}')
            if h_tags:
                headings[f'h{level}'] = [h.get_text().strip() for h in h_tags]
        return headings

    def _analyze_keywords(self, soup: BeautifulSoup) -> Dict:
        """Analyzes keyword frequency and density"""
        # Get text content
        text = soup.get_text()
        
        # Clean and tokenize
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Remove common stop words
        stop_words = {'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 
                     'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at'}
        words = [word for word in words if word not in stop_words and len(word) > 2]
        
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
            'total_words': total_words,
            'unique_words': len(set(words))
        }

    def _analyze_links(self, soup: BeautifulSoup, base_url: str) -> Dict:
        """Analyzes internal and external links"""
        base_domain = urlparse(base_url).netloc
        internal_links = []
        external_links = []
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').strip()
            text = link.get_text().strip()
            
            if href.startswith(('http://', 'https://')):
                domain = urlparse(href).netloc
                if domain == base_domain:
                    internal_links.append({'url': href, 'text': text})
                else:
                    external_links.append({'url': href, 'text': text})
            elif href.startswith('/'):
                internal_links.append({'url': f"{base_url.rstrip('/')}{href}", 'text': text})
        
        return {
            'internal_links': internal_links,
            'external_links': external_links,
            'total_internal': len(internal_links),
            'total_external': len(external_links)
        }

    def _analyze_images(self, soup: BeautifulSoup) -> Dict:
        """Analyzes images and their attributes"""
        images = []
        missing_alt = 0
        
        for img in soup.find_all('img'):
            src = img.get('src', '')
            alt = img.get('alt', '')
            if not alt:
                missing_alt += 1
            images.append({
                'src': src,
                'alt': alt,
                'width': img.get('width', ''),
                'height': img.get('height', '')
            })
        
        return {
            'total_images': len(images),
            'missing_alt': missing_alt,
            'images': images
        }

    def _analyze_content(self, soup: BeautifulSoup) -> Dict:
        """Analyzes overall content structure and statistics"""
        paragraphs = soup.find_all('p')
        text_content = ' '.join(p.get_text().strip() for p in paragraphs)
        
        return {
            'paragraph_count': len(paragraphs),
            'total_length': len(text_content),
            'average_paragraph_length': len(text_content) / len(paragraphs) if paragraphs else 0,
            'readability_score': self._calculate_readability(text_content)
        }

    def _calculate_readability(self, text: str) -> float:
        """Calculates a basic readability score"""
        sentences = len(re.split(r'[.!?]+', text))
        words = len(re.findall(r'\b\w+\b', text))
        syllables = len(re.findall(r'[aeiou]+', text.lower()))
        
        if sentences == 0 or words == 0:
            return 0
            
        # Simple Flesch Reading Ease score
        return 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)

    def _format_results(self, analysis: Dict) -> str:
        """Formats the analysis results into a readable report"""
        report = ["=== Website Content Analysis ===\n"]
        
        # Meta Tags
        report.append("1. Meta Tags:")
        for name, content in analysis['meta_tags'].items():
            report.append(f"   - {name}: {content}")
        
        # Headings Structure
        report.append("\n2. Heading Structure:")
        for level, headings in analysis['headings'].items():
            report.append(f"   - {level} ({len(headings)}):")
            for h in headings:
                report.append(f"     * {h}")
        
        # Keyword Analysis
        report.append("\n3. Keyword Analysis:")
        report.append(f"   - Total Words: {analysis['keywords']['total_words']}")
        report.append(f"   - Unique Words: {analysis['keywords']['unique_words']}")
        report.append("   - Top Keywords (with density):")
        for word, density in analysis['keywords']['density'].items():
            freq = analysis['keywords']['frequencies'][word]
            report.append(f"     * {word}: {freq} occurrences ({density:.2f}%)")
        
        # Links Analysis
        report.append("\n4. Links Analysis:")
        report.append(f"   - Internal Links: {analysis['links']['total_internal']}")
        report.append(f"   - External Links: {analysis['links']['total_external']}")
        
        # Images Analysis
        report.append("\n5. Images Analysis:")
        report.append(f"   - Total Images: {analysis['images']['total_images']}")
        report.append(f"   - Missing Alt Text: {analysis['images']['missing_alt']}")
        
        # Content Statistics
        report.append("\n6. Content Statistics:")
        report.append(f"   - Paragraphs: {analysis['content_stats']['paragraph_count']}")
        report.append(f"   - Total Content Length: {analysis['content_stats']['total_length']} characters")
        report.append(f"   - Average Paragraph Length: {analysis['content_stats']['average_paragraph_length']:.1f} characters")
        report.append(f"   - Readability Score: {analysis['content_stats']['readability_score']:.1f}")
        
        return "\n".join(report) 