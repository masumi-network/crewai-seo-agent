# SEO Analysis Agent

An AI-powered SEO analysis tool that provides comprehensive website optimization insights using multiple specialized agents.

## Project Overview

This project is an SEO agent designed to analyze and optimize websites for better search engine performance. The agent utilizes various tools to collect and analyze data, providing detailed reports on different aspects of the website's SEO. The primary tools include:

1. **BrowserlessScraper**: Scrapes website content and analyzes meta tags, SEO elements, content structure, keyword frequency, link mapping, and media inventory.
2. **SubpageAnalyzer**: Analyzes page crawl and indexing status, content quality, user engagement metrics, internal linking patterns, page authority, and JavaScript-rendered content.
3. **LoadingTimeTracker**: Performs page load timing analysis, resource loading sequences, performance bottlenecks, network request patterns, page size measurements, and performance ratings.
4. **MobileTesting**: Evaluates viewport configuration, mobile responsiveness, touch element spacing, font size accessibility, content scaling, mobile-friendly images, media query implementation, mobile performance metrics, and user experience factors.

## Tech Stack

1. **Python**: Primary programming language (version 3.10-3.13)
2. **crewai**: AI agent development library (version 0.79.4 or higher, < 1.0.0)
3. **FastAPI**: Web framework for API endpoints
4. **Browserless.io**: Web scraping service
5. **OpenAI**: GPT models for analysis
6. **Docker**: Containerization
7. **YAML**: Configuration files
8. **ReportLab**: PDF report generation
9. **Uvicorn**: ASGI server
10. **RabbitMQ**: Message queue for job processing

## API Endpoints

1. **Start Analysis**:
   ```http
   POST /start_job
   {
       "website_url": "https://example.com"
   }
   ```

2. **Check Status**:
   ```http
   GET /status/{job_id}
   ```

## Project Structure
```
SEO-Agent/
├── src/
│   ├── config/
│   │   ├── agents.yaml    # Agent configurations
│   │   └── tasks.yaml     # Task definitions
│   ├── tools/             # Custom SEO analysis tools
│   ├── utils/
│   │   └── payment_handler.py  # Masumi payment integration
│   ├── crew.py           # Main crew implementation
│   ├── main.py           # Entry point
│   └── worker.py         # Worker implementation
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Monitoring

### RabbitMQ Management Interface
- Access at: http://localhost:15672
- Default credentials: user/password

### Worker Logs
```bash
docker-compose logs -f worker
```

### BrowserlessScraper
- Extracts meta tags, headings, links, and images
- Analyzes content structure
- Counts keywords and calculates density
- Handles JavaScript-rendered content
- Provides readability metrics

1. If services fail to start:
   - Check if RabbitMQ is running
   - Verify environment variables
   - Ensure config files are in the correct location

2. If analysis fails:
   - Check worker logs
   - Verify API keys
   - Ensure website is accessible

3. If queue builds up:
   - Scale up workers
   - Check for worker errors
   - Monitor RabbitMQ dashboard

## Output

The analysis generates a detailed report in PDF format containing:

1. Technical Analysis
   - Meta tag inventory
   - Content structure
   - Link profile
   - Performance metrics

2. Content Analysis
   - Keyword density
   - Readability scores
   - Content structure

## Payment Flow
1. Client submits website URL for analysis
2. System creates payment request through Masumi
3. Client completes payment
4. System verifies payment status
5. SEO analysis begins after payment confirmation
6. Results delivered upon completion

## Tools

### SubpageAnalyzer
- Analyzes page crawl status
- Measures user engagement
- Evaluates content quality

### MobileTesting
- Tests mobile compatibility
- Checks responsive design
- Validates mobile performance

## Error Handling
- Payment verification failures
- API connection issues
- Analysis process errors
- Report generation problems

## Acknowledgments

- Built with [crewAI](https://github.com/joaomdmoura/crewAI)
- Uses OpenAI's GPT-4 for analysis
- Powered by [browserless.io](https://browserless.io) for web scraping
- Queue system using [RabbitMQ](https://www.rabbitmq.com/)
- Payment processing by [Masumi Network](https://masumi.network)