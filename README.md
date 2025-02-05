# SEO Analysis Agent

An intelligent SEO analysis tool powered by crewAI that helps analyze and optimize website content using browserless.io for reliable web scraping.

## Overview

This project uses AI agents via crewAI to perform comprehensive SEO analysis and provide optimization recommendations. The agents work together to analyze technical SEO, content quality, keyword optimization, and mobile compatibility using browserless.io for reliable web scraping.

## Features

### Data Collection
- Meta tags analysis and extraction
- Content structure analysis (headings, word count)
- Link analysis (internal/external)
- Image optimization check
- Loading time measurements
- Mobile optimization metrics
- JavaScript-rendered content analysis

### Analysis
- Technical SEO evaluation
- Content quality assessment
- Link profile analysis
- Mobile compatibility scoring
- Performance metrics
- Keyword density analysis
- Readability scoring

### Optimization
- Prioritized improvement recommendations
- Implementation timeline
- Expected impact projections
- ROI estimates

## Installation

### Requirements
- Python 3.10-3.13
- Browserless.io API key
- OpenAI API key

### Dependencies
Required packages:

pip install -r requirements.txt

Required packages:
- crewai>=0.79.4
- beautifulsoup4
- requests
- python-dotenv
- pydantic
- openai
- PyYAML
- mdpdf

### Environment Setup
1. Create a `.env` file in the root directory
2. Add your API keys:

env
OPENAI_API_KEY=your_openai_api_key_here
BROWSERLESS_API_KEY=your_browserless_api_key_here


## Tools Description

### BrowserlessScraper
- Extracts meta tags, headings, links, and images
- Analyzes content structure
- Counts keywords and calculates density
- Handles JavaScript-rendered content
- Provides readability metrics

### LoadingTimeTracker
- Measures page load times using browserless
- Takes multiple samples
- Calculates average, min, and max load times
- Measures page size
- Provides performance ratings

### OffPageSEOAnalyzer
- Analyzes external link profile
- Checks social media presence
- Measures brand visibility
- Evaluates content distribution
- Uses browserless for reliable data collection

### SubpageAnalyzer
- Crawls website subpages
- Analyzes content quality
- Measures user engagement signals
- Ranks pages by importance
- Uses browserless for JavaScript support

## Output

The analysis generates a detailed report in `seo_report-{domain}` containing:

1. Technical Analysis
   - Meta tag inventory
   - Content structure
   - Link profile
   - Performance metrics
   - Mobile optimization scores
   - JavaScript-rendered content analysis

2. Content Analysis
   - Keyword density
   - Readability scores
   - Content structure
   - Media optimization

3. Off-Page Analysis
   - External link profile
   - Social media presence
   - Brand visibility
   - Content distribution

4. Recommendations
   - Priority fixes
   - Expected improvements
   - Implementation timeline

## Benefits of Browserless Integration
- Reliable JavaScript rendering
- Better handling of modern web apps
- Consistent performance
- Scalable solution
- Proxy management
- Better error handling

## Acknowledgments

- Built with [crewAI](https://github.com/joaomdmoura/crewAI)
- Uses OpenAI's GPT-4 for analysis
- Powered by [browserless.io](https://browserless.io) for web scraping