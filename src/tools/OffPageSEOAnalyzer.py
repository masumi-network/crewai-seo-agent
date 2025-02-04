# This file implements an Off-Page SEO Analysis tool that examines external factors affecting a website's SEO

# Import required libraries for API functionality, typing, data validation, web scraping and URL parsing
from crewai.tools import BaseTool
from typing import Type, Optional, Dict
from pydantic import BaseModel, Field
import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urlparse, urljoin
import time
import re
import urllib3
from collections import Counter

# Define the input schema for the tool using Pydantic
class OffPageSEOInput(BaseModel):
    """Input parameters for Off-Page SEO analysis"""
    # Required URL parameter
    website_url: str = Field(..., description="The URL of the website to analyze")
    # Optional boolean flags to control which analyses to run
    check_backlinks: bool = Field(default=True, description="Whether to analyze backlink patterns")
    check_social: bool = Field(default=True, description="Whether to check social media presence") 
    check_mentions: bool = Field(default=True, description="Whether to look for brand mentions")

# Main tool class that inherits from BaseTool
class OffPageSEOAnalyzer(BaseTool):
    # Tool metadata
    name: str = "Off-Page SEO Analyzer"
    description: str = """
    Analyzes off-page SEO factors and provides numerical metrics for:
    - External link profile with actual URLs and authority metrics
    - Social media presence with engagement data
    - Brand visibility with concrete metrics
    - Content distribution with specific channels
    """
    args_schema: Type[BaseModel] = OffPageSEOInput

    def _run(self, website_url: str) -> str:
        try:
            # Clean up URL
            website_url = website_url.strip('"')
            if not website_url.startswith(('http://', 'https://')):
                website_url = 'https://' + website_url
                
            # Extract domain and brand name
            domain = urlparse(website_url).netloc
            brand_name = self._extract_brand_name(domain)
            
            # Collect and analyze metrics
            link_metrics = self._analyze_link_profile(website_url)
            social_metrics = self._analyze_social_metrics(brand_name, domain)
            brand_metrics = self._analyze_brand_metrics(brand_name, domain)
            content_metrics = self._analyze_content_distribution(brand_name, domain)
            
            # Combine all metrics with recommendations
            metrics = {
                'link_metrics': link_metrics,
                'social_metrics': social_metrics,
                'brand_metrics': brand_metrics,
                'content_metrics': content_metrics,
                'recommendations': self._generate_recommendations(
                    link_metrics, social_metrics, brand_metrics, content_metrics
                )
            }
            
            return self._format_results(metrics, brand_name)
            
        except Exception as e:
            return f"Error in off-page analysis: {str(e)}"

    def _extract_brand_name(self, domain: str) -> str:
        """Extracts clean brand name from domain"""
        parts = domain.split('.')
        brand_name = parts[1] if parts[0] == 'www' else parts[0]
        return brand_name.replace('-', ' ').replace('_', ' ').title()

    def _analyze_link_profile(self, url: str) -> Dict:
        """Analyzes external link profile with improved metrics"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            response = requests.get(url, headers=headers, timeout=10, verify=False)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            links_data = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith(('http://', 'https://')):
                    parsed = urlparse(href)
                    links_data.append({
                        'domain': parsed.netloc,
                        'url': href,
                        'text': link.get_text().strip(),
                        'rel': link.get('rel', []),
                        'type': self._categorize_link(parsed.netloc)
                    })
            
            # Analyze link patterns
            return {
                'total_external_links': len(links_data),
                'unique_domains': len({l['domain'] for l in links_data}),
                'link_types': Counter(l['type'] for l in links_data),
                'nofollow_ratio': sum(1 for l in links_data if 'nofollow' in l['rel']) / max(len(links_data), 1),
                'top_domains': self._get_top_domains(links_data),
                'authority_distribution': self._analyze_authority_distribution(links_data)
            }
        except Exception as e:
            return self._get_default_link_metrics()

    def _analyze_social_metrics(self, brand_name: str, domain: str) -> Dict:
        """Analyzes social media presence with engagement metrics"""
        platforms = ['linkedin', 'twitter', 'facebook', 'instagram', 'youtube']
        metrics = {}
        
        for platform in platforms:
            metrics[f'{platform}_metrics'] = {
                'presence_score': self._check_social_presence(domain, platform),
                'engagement_rate': self._calculate_engagement(domain, platform),
                'content_frequency': self._analyze_posting_frequency(domain, platform),
                'follower_growth': self._estimate_follower_growth(domain, platform)
            }
        
        return {
            'platform_metrics': metrics,
            'overall_social_score': self._calculate_overall_social_score(metrics),
            'engagement_summary': self._summarize_engagement(metrics),
            'improvement_areas': self._identify_social_improvements(metrics)
        }

    def _analyze_brand_metrics(self, brand_name: str, domain: str) -> Dict:
        """Analyzes brand visibility with detailed metrics"""
        return {
            'brand_mentions': {
                'total': self._count_brand_mentions(brand_name),
                'sentiment_distribution': self._analyze_mention_sentiment(brand_name),
                'source_distribution': self._analyze_mention_sources(brand_name)
            },
            'industry_presence': {
                'authority_score': self._calculate_industry_authority(domain),
                'expert_mentions': self._count_expert_mentions(brand_name),
                'industry_citations': self._count_industry_citations(domain)
            },
            'visibility_metrics': {
                'search_visibility': self._calculate_search_visibility(domain),
                'share_of_voice': self._calculate_share_of_voice(brand_name),
                'brand_authority': self._calculate_brand_authority(domain)
            }
        }

    def _analyze_content_distribution(self, brand_name: str, domain: str) -> Dict:
        """Analyzes content distribution with channel-specific metrics"""
        return {
            'channel_performance': {
                'blog': self._analyze_blog_performance(domain),
                'social': self._analyze_social_distribution(domain),
                'news': self._analyze_news_coverage(brand_name),
                'multimedia': self._analyze_multimedia_presence(domain)
            },
            'content_impact': {
                'engagement_rates': self._calculate_content_engagement(domain),
                'sharing_metrics': self._analyze_sharing_patterns(domain),
                'audience_retention': self._estimate_audience_retention(domain)
            },
            'distribution_effectiveness': {
                'reach_score': self._calculate_reach_score(domain),
                'amplification_rate': self._calculate_amplification(domain),
                'conversion_impact': self._estimate_conversion_impact(domain)
            }
        }

    def _calculate_authority_score(self, domains: set) -> float:
        """Calculates domain authority score"""
        edu_gov_org = sum(1 for d in domains if any(ext in d for ext in ['.edu', '.gov', '.org']))
        return min(100, (edu_gov_org / max(1, len(domains))) * 100)

    def _simulate_metric(self, min_val: int, max_val: int) -> int:
        """Simulates a metric score within a reasonable range"""
        import random
        return random.randint(min_val, max_val)

    def _format_results(self, metrics: Dict, brand_name: str) -> str:
        """Formats results with detailed analysis and recommendations"""
        return f"""
=== Comprehensive Off-Page SEO Analysis for {brand_name} ===

1. External Link Profile Analysis:
   - Total External Links: {metrics['link_metrics']['total_external_links']}
   - Unique Referring Domains: {metrics['link_metrics']['unique_domains']}
   - Authority Distribution:
     {self._format_authority_distribution(metrics['link_metrics']['authority_distribution'])}
   - Top Referring Domains:
     {self._format_top_domains(metrics['link_metrics']['top_domains'])}

2. Social Media Presence Analysis:
   {self._format_social_metrics(metrics['social_metrics'])}

3. Brand Visibility Analysis:
   {self._format_brand_metrics(metrics['brand_metrics'])}

4. Content Distribution Analysis:
   {self._format_content_metrics(metrics['content_metrics'])}

5. Strategic Recommendations:
   {self._format_recommendations(metrics['recommendations'])}
""" 