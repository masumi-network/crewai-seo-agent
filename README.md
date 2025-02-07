# SEO Analysis Agent

An intelligent SEO analysis tool powered by crewAI that helps analyze and optimize website content using browserless.io for reliable web scraping.

## Overview

This project uses AI agents via crewAI to perform comprehensive SEO analysis and provide optimization recommendations. The agents work together to analyze technical SEO, content quality, keyword optimization, and mobile compatibility using browserless.io for reliable web scraping.

## Features

### Data Collection & Analysis
- Meta tags and SEO elements analysis
- Content structure analysis (headings h1-h6)
- Keyword frequency and density analysis
- Internal and external link mapping
- Mobile compatibility testing
- Loading time measurements
- JavaScript-rendered content analysis

### Generated Report Sections
1. Priority Issues
   - Current metrics vs Target goals
   - Prioritized improvement areas
   - Specific recommendations

2. Impact Forecast
   - Load time reduction estimates
   - SEO score increase projections
   - User engagement predictions

3. Key Statistics
   - Average load times
   - Most used meta tags
   - Mobile compatibility scores
   - Keyword frequency analysis
   - Top performing subpages

4. Page-Specific Optimizations
   - High-priority pages analysis
   - Content gap identification
   - Structure enhancement recommendations

## Installation

### Requirements
- Python 3.10-3.13
- Browserless.io API key
- OpenAI API key

### Usage 
source venv/bin/activate
cd src
python main.py
Run the full crew analysis: python main.py
Test just the PDF conversion: python main.py --test-pdf

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file with API keys:
```env
OPENAI_API_KEY=your_openai_api_key_here
BROWSERLESS_API_KEY=your_browserless_api_key_here
```

### Usage
```bash
cd src
python main.py  # Run full analysis
python main.py --test-pdf  # Test PDF generation only
```

## Output

The tool generates two files:
1. `report.md` - Raw markdown report
2. `seo_report-{domain}.pdf` - Formatted PDF report with:
   - Professional styling
   - Data tables
   - Metric visualizations
   - Actionable recommendations

## Tools

### BrowserlessScraper
- Extracts meta tags, headings, links
- Analyzes content structure
- Handles JavaScript-rendered content

### SubpageAnalyzer
- Crawls website subpages
- Analyzes content quality
- Measures user engagement signals

### MobileTesting
- Tests mobile compatibility
- Checks responsive design
- Validates mobile performance

## Benefits
- Comprehensive SEO analysis
- Professional PDF reports
- Actionable recommendations
- Reliable web scraping
- Mobile-first analysis
- Modern web app support

## Acknowledgments
- Built with [crewAI](https://github.com/joaomdmoura/crewAI)
- Uses OpenAI's GPT models
- Powered by [browserless.io](https://browserless.io)