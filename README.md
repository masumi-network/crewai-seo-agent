# SEO Analysis Agent with Queue System

A powerful, distributed SEO analysis system powered by AI agents that provides comprehensive website analysis and optimization recommendations. Built with crewAI, this system uses browserless.io for reliable web scraping and includes a RabbitMQ queue system for handling multiple concurrent analysis requests.

## Key Features

### Intelligent Multi-Agent System
- **SEO Technical Auditor**: Collects and analyzes technical SEO metrics
- **Analytics Specialist**: Processes data and uncovers optimization opportunities
- **Strategy Expert**: Develops actionable improvement recommendations

### Comprehensive Analysis
- **Technical SEO**
  - Meta tag analysis and optimization
  - Site structure evaluation
  - Mobile responsiveness testing
  - Page load speed analysis
  - JavaScript rendering assessment

- **Content Analysis**
  - Keyword density and relevance
  - Content structure and readability
  - Heading hierarchy analysis
  - Image optimization check
  - Internal/external link analysis

- **Performance Metrics**
  - Loading time measurements
  - Mobile compatibility scoring
  - User experience factors
  - Resource optimization checks

### Advanced Architecture
- Distributed task processing with RabbitMQ
- Containerized microservices with Docker
- PostgreSQL for persistent storage
- FastAPI for RESTful endpoints
- Automated health monitoring

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Browserless.io API key
- OpenAI API key (GPT-4 recommended)
- Python 3.10-3.13

### Installation

1. Clone and setup:
```bash
git clone <repository-url>
cd seo-analysis-agent
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

3. Launch services:
```bash
docker-compose up -d
```

### API Endpoints

- `POST /analyze`
  ```json
  {
    "website_url": "https://example.com"
  }
  ```
  Returns: `job_id` for tracking analysis progress

- `GET /result/{job_id}`
  Returns analysis results including:
  - Technical metrics
  - Content analysis
  - Optimization recommendations

- `GET /health`
  System health check endpoint

## Architecture Details

### Components
- **Web Service**: FastAPI application handling API requests
- **Worker Pool**: Distributed analysis workers
- **Message Queue**: RabbitMQ for task distribution
- **Database**: PostgreSQL for results storage
- **Analysis Tools**:
  - BrowserlessScraper
  - LoadingTimeTracker
  - MobileOptimizationTool
  - SubpageAnalyzer

### Data Flow
1. Client submits analysis request
2. Request queued in RabbitMQ
3. Available worker picks up task
4. Multiple AI agents perform analysis
5. Results stored in PostgreSQL
6. Client retrieves formatted results

## Monitoring & Management

### RabbitMQ Dashboard
- URL: http://localhost:15672
- Credentials: user/password
- Monitor queue status
- Track worker performance

### Logging
```bash
# View service logs
docker-compose logs -f web

# View worker logs
docker-compose logs -f worker
```

### Scaling
```bash
# Scale up workers
docker-compose up -d --scale worker=3
```

## Troubleshooting

### Common Issues
1. Connection Errors
   - Verify RabbitMQ is running
   - Check network connectivity
   - Validate API credentials

2. Analysis Failures
   - Check worker logs
   - Verify target site accessibility
   - Validate API rate limits

3. Performance Issues
   - Monitor queue length
   - Check resource usage
   - Scale workers as needed

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Submit pull request

## License

MIT License - See LICENSE file for details

## Acknowledgments
- Built with [crewAI](https://github.com/joaomdmoura/crewAI)
- Uses OpenAI's GPT-4
- Powered by [browserless.io](https://browserless.io)
- Queue system by [RabbitMQ](https://www.rabbitmq.com/)

## API Documentation

This service implements the Masumi Agentic Service API Standard (MIP-003).

### Endpoints

#### 1. Start Job
- **URL**: `/start_job`
- **Method**: `POST`
- **Body**:
```json
{
    "input_data": {
        "website_url": "https://example.com",
        "max_pages": 50,
        "analysis_depth": "standard"
    }
}
```
- **Response**:
```json
{
    "status": "success",
    "job_id": "string",
    "payment_id": "string"
}
```

#### 2. Check Job Status
- **URL**: `/status?job_id=<job_id>`
- **Method**: `GET`
- **Response**:
```json
{
    "job_id": "string",
    "status": "string",
    "result": {
        "recommendations": {
            "priority_fixes": [],
            "impact_forecast": {},
            "key_statistics": {}
        }
    }
}
```

#### 3. Check Availability
- **URL**: `/availability`
- **Method**: `GET`
- **Response**:
```json
{
    "status": "available",
    "message": "Service is operational"
}
```

#### 4. Get Input Schema
- **URL**: `/input_schema`
- **Method**: `GET`
- **Response**: Returns the expected input format for the service