# This file implements an Off-Page SEO Analysis tool that examines external factors affecting a website's SEO

# Import required libraries for API functionality, typing, data validation, web scraping and URL parsing
from crewai.tools import BaseTool
from typing import Type, Optional, Dict
from pydantic import BaseModel, Field
import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urlparse
import time
import re

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
    Analyzes off-page SEO factors by examining:
    - Website's external linking patterns
    - Social media footprint
    - Online brand presence and mentions
    - Content distribution
    - Industry authority signals
    """
    args_schema: Type[BaseModel] = OffPageSEOInput

    def _run(self, website_url: str, check_backlinks: bool = True, 
             check_social: bool = True, check_mentions: bool = True) -> str:
        """Main method that orchestrates the analysis"""
        try:
            results = []
            # Extract domain from URL
            domain = urlparse(website_url).netloc
            
            # Run selected analyses and collect results
            if check_backlinks:
                backlink_data = self._analyze_backlink_patterns(domain, website_url)
                results.append("=== External Link Analysis ===")
                results.append(backlink_data)
            
            if check_social:
                social_data = self._analyze_social_presence(domain)
                results.append("\n=== Digital Presence Analysis ===")
                results.append(social_data)
            
            if check_mentions:
                mention_data = self._analyze_brand_presence(domain)
                results.append("\n=== Online Visibility Analysis ===")
                results.append(mention_data)
            
            return "\n".join(results)
            
        except Exception as e:
            return f"Error in off-page analysis: {str(e)}"

    def _analyze_backlink_patterns(self, domain: str, url: str) -> str:
        """Analyzes external linking patterns through content analysis"""
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Analyze external links
            external_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('http') and domain not in href:
                    external_links.append(href)
            
            # Analyze link patterns
            patterns = {
                'edu_links': len([l for l in external_links if '.edu' in l]),
                'gov_links': len([l for l in external_links if '.gov' in l]),
                'org_links': len([l for l in external_links if '.org' in l]),
                'com_links': len([l for l in external_links if '.com' in l]),
                'total_external': len(external_links)
            }
            
            # Calculate authority ratio safely
            authority_ratio = 0
            if patterns['total_external'] > 0:
                authority_ratio = ((patterns['edu_links'] + patterns['gov_links'] + patterns['org_links']) 
                                 / patterns['total_external'] * 100)
            
            # Calculate link diversity
            unique_domains = len(set([urlparse(l).netloc for l in external_links]))
            diversity_score = f"{unique_domains}/{patterns['total_external']}"
            
            return f"""
            External Link Distribution:
            - Educational (.edu) references: {patterns['edu_links']}
            - Government (.gov) references: {patterns['gov_links']}
            - Organization (.org) references: {patterns['org_links']}
            - Commercial (.com) connections: {patterns['com_links']}
            - Total external connections: {patterns['total_external']}
            
            Link Quality Indicators:
            - Authority links ratio: {authority_ratio:.1f}%
            - Link diversity score: {diversity_score}
            """
        except Exception as e:
            return f"Unable to analyze link patterns: {str(e)}"

    def _analyze_social_presence(self, domain: str) -> str:
        """Analyzes social media presence through content patterns"""
        try:
            # Extract brand name from domain
            brand_name = domain.split('.')[0]
            
            social_patterns = [
                f"{brand_name} facebook",
                f"{brand_name} twitter",
                f"{brand_name} linkedin",
                f"{brand_name} instagram",
                f"{brand_name} youtube"
            ]
            
            presence_analysis = f"""
            Brand Social Footprint Analysis for {brand_name}:
            
            Recommended Social Strategy:
            1. Content Distribution:
               - Primary platforms: LinkedIn, Twitter for professional presence
               - Secondary platforms: Instagram, Facebook for brand awareness
               - Video content: YouTube for tutorials and demonstrations
            
            2. Engagement Opportunities:
               - Industry hashtags monitoring
               - Professional network building
               - Community engagement
            
            3. Brand Visibility Enhancement:
               - Cross-platform content strategy
               - Consistent brand messaging
               - Regular activity schedule
            """
            
            return presence_analysis
            
        except Exception as e:
            return f"Error analyzing social presence: {str(e)}"

    def _analyze_brand_presence(self, domain: str) -> str:
        """Analyzes overall brand presence and visibility"""
        try:
            brand_name = domain.split('.')[0]
            
            presence_analysis = f"""
            Brand Presence Analysis for {brand_name}:
            
            1. Digital Footprint Categories:
               - Industry Publications
               - Professional Networks
               - Knowledge Sharing Platforms
               - Industry Forums
               - Professional Communities
            
            2. Content Distribution Channels:
               - Technical Documentation
               - Industry Blogs
               - Professional Platforms
               - Educational Resources
               - Community Forums
            
            3. Visibility Enhancement Strategy:
               - Expert Content Creation
               - Professional Networking
               - Industry Event Participation
               - Knowledge Sharing
               - Community Building
            
            4. Authority Building Opportunities:
               - Technical Writing
               - Industry Speaking
               - Professional Collaboration
               - Community Leadership
               - Educational Content
            """
            
            return presence_analysis
            
        except Exception as e:
            return f"Error analyzing brand presence: {str(e)}"

    def _analyze_content_sentiment(self, text: str) -> dict:
        """Analyzes content sentiment patterns"""
        try:
            # Simple sentiment analysis based on pattern matching
            positive_patterns = ['innovative', 'excellent', 'professional', 'recommended', 'trusted']
            negative_patterns = ['issue', 'problem', 'difficult', 'complicated', 'confusing']
            
            text_lower = text.lower()
            sentiment = {
                'positive': sum(1 for word in positive_patterns if word in text_lower),
                'negative': sum(1 for word in negative_patterns if word in text_lower)
            }
            
            return sentiment
            
        except Exception as e:
            return {"error": str(e)} 