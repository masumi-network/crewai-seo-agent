# SEO Analysis Agent with Masumi Payment Integration

An intelligent SEO analysis tool powered by crewAI that helps analyze and optimize website content using browserless.io for reliable web scraping. This version includes Masumi payment integration for handling service payments.

## Architecture

- RabbitMQ for message queuing
- Worker processes for handling SEO analysis
- Containerized with Docker
- Multiple AI agents working together
- Scalable architecture for handling multiple requests

## Features

### System Features
- Queue-based processing
- Scalable worker architecture
- Containerized deployment
- Error handling and retry logic
- Distributed task processing

### Data Collection
- Meta tags analysis and extraction
- Content structure analysis (headings, word count)
- Link analysis (internal/external)
- Image optimization check
- Loading time measurements
- Mobile optimization metrics
- JavaScript-rendered content analysis

### SEO Analysis
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

### Payment Integration
- Secure payment processing via Masumi Network
- Payment status verification
- Job tracking with unique IDs
- Automated payment flow

### Report Generation
- Detailed PDF reports
- Priority issues identification
- Impact forecasting
- Key statistics compilation
- Page-specific optimizations

## API Endpoints

### Start Analysis Job
```http
POST /start_job
Content-Type: application/json

{
    "website_url": "https://example.com"
}
```

### Check Job Status
```http
GET /status/{job_id}
```

## Installation

### Requirements
- Python 3.10-3.13
- Browserless.io API key
- OpenAI API key
- Masumi Payment API key
- Docker and Docker Compose

### Quick Start
1. Clone the repository:
```bash
git clone <repository-url>
cd SEO-Agent
```

2. Create a `.env` file in the root directory:
```env
OPENAI_API_KEY=your_openai_api_key
BROWSERLESS_API_KEY=your_browserless_api_key
RABBITMQ_USER=user
RABBITMQ_PASS=password
PAYMENT_SERVICE_URL=your_masumi_payment_service_url
PAYMENT_API_KEY=your_masumi_api_key
```

3. Build and run with Docker Compose:
```bash
docker-compose build
docker-compose up
```

This will start:
- RabbitMQ on port 5672 (management interface on 15672)
- Worker process(es)
- Web service

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