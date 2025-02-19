# SEO Analysis Agent - Technical Overview

## 1. Core Purpose
The SEO Analysis Agent is an AI-powered system that performs comprehensive website analysis using multiple specialized agents to provide actionable SEO recommendations.

## 2. Key Components

### 2.1 AI Agents
- **Scraper Agent**: Technical auditor that collects raw website data
  - Meta tags analysis
  - Content structure
  - Link mapping
  - Performance metrics
  
- **Analysis Agent**: Processes collected data for insights
  - Keyword analysis
  - Content quality assessment
  - Technical SEO metrics evaluation
  
- **Optimization Agent**: Generates actionable recommendations
  - Priority fixes
  - Impact forecasts
  - Page-specific optimizations

### 2.2 Technical Tools
- **BrowserlessScraper**: Headless browser for content extraction
- **LoadingTimeTracker**: Performance measurement tool
- **MobileTesting**: Mobile compatibility analyzer
- **SubpageAnalyzer**: Deep page analysis tool

## 3. Architecture

### 3.1 Infrastructure
```
[Client] → [FastAPI Service] → [RabbitMQ Queue] → [Worker Pool] → [PostgreSQL]
```

- **FastAPI**: REST API interface (Port 8000)
- **RabbitMQ**: Message queue for job distribution (Ports 5672, 15672)
- **PostgreSQL**: Data persistence
- **Docker**: Containerization for all components

### 3.2 Data Flow
1. Client submits URL for analysis
2. Job created and queued
3. Worker picks up analysis task
4. Multiple AI agents process the site
5. Results stored in database
6. Client retrieves final analysis

## 4. Key Features

### 4.1 Technical Analysis
- Meta tag optimization
- Site structure evaluation
- Mobile responsiveness
- Page load speed
- JavaScript rendering
- Content quality assessment

### 4.2 Performance Metrics
- Loading time measurements
- Mobile compatibility scores
- User experience factors
- Resource optimization

### 4.3 Content Analysis
- Keyword density
- Content structure
- Heading hierarchy
- Image optimization
- Internal/external linking

## 5. API Endpoints

### 5.1 Start Analysis
```bash
POST /start_job
{
    "website_url": "https://example.com",
    "max_pages": 50
}
```

### 5.2 Check Status
```bash
GET /status?job_id=<job_id>
```

### 5.3 Health Check
```bash
GET /health
```

## 6. Deployment

### 6.1 Prerequisites
- Docker and Docker Compose
- Browserless.io API key
- OpenAI API key
- Python 3.10-3.13

### 6.2 Environment Setup
```bash
# Clone repository
git clone <repo>

# Configure environment
cp .env.example .env

# Start services
docker-compose up -d
```

## 7. Monitoring

### 7.1 RabbitMQ Dashboard
- URL: http://localhost:15672
- Credentials: user/password
- Queue monitoring
- Worker status

### 7.2 Logging
```bash
# View service logs
docker-compose logs -f web

# View worker logs
docker-compose logs -f worker
```

## 8. Scaling Capabilities

### 8.1 Horizontal Scaling
```bash
# Scale workers
docker-compose up -d --scale worker=3
```

### 8.2 Queue Management
- Automatic job distribution
- Worker load balancing
- Failed job retry mechanism

## 9. Example Analysis Output
```json
{
    "recommendations": {
        "priority_fixes": [
            "Optimize meta descriptions",
            "Improve mobile responsiveness",
            "Reduce page load time"
        ],
        "impact_forecast": {
            "load_time_reduction": "25%",
            "seo_score_increase": "15%"
        },
        "key_statistics": {
            "average_load_time": "2.3s",
            "mobile_compatibility": "85%"
        }
    }
}
```

## 10. Future Enhancements
1. AI model fine-tuning for industry-specific insights
2. Real-time analysis capabilities
3. Competitor analysis integration
4. Custom reporting templates
5. API rate limiting and authentication

## 11. Common Issues & Solutions

### 11.1 Connection Issues
- Check RabbitMQ status
- Verify database connectivity
- Validate API credentials

### 11.2 Performance Issues
- Monitor queue length
- Check resource usage
- Scale workers as needed

### 11.3 Analysis Failures
- Check worker logs
- Verify site accessibility
- Validate API rate limits

## 12. Testing Commands for NMKR.io

### 12.1 Basic Analysis
```bash
# Start a new analysis job
curl -X POST "http://localhost:8000/start_job" \
     -H "Content-Type: application/json" \
     -d '{
         "website_url": "https://nmkr.io",
         "max_pages": 50
     }'

# Response will look like:
{
    "status": "success",
    "job_id": "123"
}
```

### 12.2 Check Status
```bash
# Check job status using the job_id
curl "http://localhost:8000/status?job_id=123"

# Response progression:
# 1. Initially:
{
    "job_id": "123",
    "status": "pending"
}

# 2. During analysis:
{
    "job_id": "123",
    "status": "running"
}

# 3. After completion:
{
    "job_id": "123",
    "status": "completed",
    "result": {
        "recommendations": {
            "priority_fixes": [...],
            "impact_forecast": {...},
            "key_statistics": {...}
        }
    }
}
```

### 12.3 Docker Commands
```bash
# View logs during analysis
docker-compose logs -f web

# Check RabbitMQ status
docker-compose logs rabbitmq

# Check database status
docker-compose logs postgres

# Restart all services (if needed)
docker-compose restart

# Scale up workers for faster analysis
docker-compose up -d --scale worker=3
```

### 12.4 Monitoring
```bash
# Access RabbitMQ dashboard
open http://localhost:15672
# Login with:
# username: user
# password: password

# Check service health
curl http://localhost:8000/health
```

### 12.5 Common Test Scenarios

1. Full Site Analysis
```bash
# Analyze entire site
curl -X POST "http://localhost:8000/start_job" \
     -H "Content-Type: application/json" \
     -d '{
         "website_url": "https://nmkr.io",
         "max_pages": 100
     }'
```

2. Quick Analysis
```bash
# Quick analysis with fewer pages
curl -X POST "http://localhost:8000/start_job" \
     -H "Content-Type: application/json" \
     -d '{
         "website_url": "https://nmkr.io",
         "max_pages": 10
     }'
```

3. Specific Subpage Analysis
```bash
# Analyze specific subpage
curl -X POST "http://localhost:8000/start_job" \
     -H "Content-Type: application/json" \
     -d '{
         "website_url": "https://nmkr.io/marketplace",
         "max_pages": 1
     }'
```

### 12.6 Expected Results for NMKR.io

The analysis will typically focus on:

1. Technical Aspects
- Loading time of marketplace pages
- Mobile responsiveness of NFT displays
- Meta tag optimization for NFT collections
- JavaScript rendering of dynamic content

2. Content Analysis
- NFT description quality
- Marketplace navigation structure
- Collection page optimization
- Search functionality

3. Performance Metrics
- Image loading speeds
- Transaction response times
- Mobile UI/UX scores
- Page load times

### 12.7 Troubleshooting NMKR.io Analysis

If analysis fails:
```bash
# 1. Check service health
curl http://localhost:8000/health

# 2. Verify RabbitMQ connection
docker-compose logs rabbitmq | grep "error"

# 3. Reset analysis (if needed)
docker-compose restart

# 4. Check for rate limiting
docker-compose logs web | grep "rate limit"
```

### 12.8 Demo Script

Quick demo sequence:
1. Start analysis
2. Show pending status
3. Display running status
4. Present final results
5. Show RabbitMQ dashboard
6. Demonstrate scaling

```bash
# Run these commands in sequence for demo
./demo_nmkr.sh

# Or manually:
# 1. Start analysis
curl -X POST "http://localhost:8000/start_job" -H "Content-Type: application/json" -d '{"website_url": "https://nmkr.io", "max_pages": 20}'

# 2. Check status (run multiple times)
curl "http://localhost:8000/status?job_id=<JOB_ID>"

# 3. Show RabbitMQ dashboard
open http://localhost:15672

# 4. Scale workers
docker-compose up -d --scale worker=3
```