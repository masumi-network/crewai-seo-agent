# SEO Analysis Agent

An intelligent SEO analysis tool powered by crewAI that helps analyze and optimize website content.

## Overview

This project uses AI agents via crewAI to perform comprehensive SEO analysis and provide optimization recommendations. The agents work together to analyze technical SEO, content quality, keyword optimization, and mobile compatibility.

## Features

### Data Collection
- Meta tags analysis and extraction
- Content structure analysis (headings, word count)
- Link analysis (internal/external)
- Image optimization check
- Loading time measurements
- Mobile optimization metrics

### Analysis
- Technical SEO evaluation
- Content quality assessment
- Link profile analysis
- Mobile compatibility scoring
- Performance metrics

### Optimization
- Prioritized improvement recommendations
- Implementation timeline
- Expected impact projections
- ROI estimates


## Installation

### Requirements
- Python 3.10-3.13
- Chrome/Chromium browser (for Selenium)
- ChromeDriver matching your Chrome version

### Dependencies
Required packages:
- crewai>=0.79.4
- selenium
- beautifulsoup4
- requests
- python-dotenv
- pydantic
- openai
- PyYAML

### Environment Setup
1. Create a `.env` file in the root directory
2. Add your OpenAI API key:
OPENAI_API_KEY=your_api_key_here


3. The tool will generate a comprehensive report including:
   - Technical SEO metrics
   - Content analysis
   - Mobile optimization scores
   - Performance measurements
   - Optimization recommendations

## Tools Description

### SeleniumScraper
- Extracts meta tags, headings, links, and images
- Analyzes content structure
- Counts keywords and calculates density

### LoadingTimeTracker
- Measures page load times
- Takes multiple samples
- Calculates average, min, and max load times
- Tracks performance history

### MobileOptimizationTool
- Checks viewport meta tag
- Analyzes text readability
- Verifies tap target spacing
- Tests responsive images
- Calculates mobile compatibility score

## Output

The analysis generates a detailed report in `report.md` containing:
1. Technical Analysis
   - Meta tag inventory
   - Content structure
   - Link profile
   - Performance metrics
   - Mobile optimization scores

2. Recommendations
   - Priority fixes
   - Expected improvements
   - Implementation timeline

## Acknowledgments

- Built with [crewAI](https://github.com/joaomdmoura/crewAI)
- Uses OpenAI's GPT-4 for analysis