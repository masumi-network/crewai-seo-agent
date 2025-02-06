# SEO Analysis Agent with Queue System

An intelligent SEO analysis tool powered by crewAI that helps analyze and optimize website content using browserless.io for reliable web scraping. This version includes a RabbitMQ queue system for handling multiple analysis requests.

## Architecture

- FastAPI web server for handling requests
- RabbitMQ for message queuing
- Worker processes for handling SEO analysis
- Containerized with Docker
- Deployable to Digital Ocean

## Features

### SEO Analysis
- Meta tags analysis and extraction
- Content structure analysis
- Link analysis (internal/external)
- Image optimization check
- Loading time measurements
- Mobile optimization metrics
- JavaScript-rendered content analysis

### System Features
- Queue-based processing
- Scalable worker architecture
- Containerized deployment
- Health check endpoint
- Error handling and retry logic

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Browserless.io API key
- OpenAI API key

## Local Development Setup

1. Clone the repository:
bash
git clone [repository-url]
cd SEO-Agent



2. Create a `.env` file in the root directory:
env
OPENAI_API_KEY=your_openai_api_key_here
BROWSERLESS_API_KEY=your_browserless_api_key_here


3. Build and run with Docker Compose:
bash
docker-compose up --build

This will start:
- Web server on port 8000
- RabbitMQ on port 5672 (management interface on 15672)
- Worker process(s)

## API Usage

### Request SEO Analysis
bash
curl -X POST http://localhost:8000/analyze \
-H "Content-Type: application/json" \
-d '{"website_url": "https://example.com"}'



### Check Health

bash
curl http://localhost:8000/health


## Digital Ocean Deployment

1. Fork this repository to your GitHub account

2. Create a new app on Digital Ocean:
   - Go to Digital Ocean dashboard
   - Click "Create" → "Apps"
   - Select your GitHub repository
   - Configure environment variables:
     - `OPENAI_API_KEY`
     - `BROWSERLESS_API_KEY`

3. Deploy the application:
   - Digital Ocean will automatically deploy the web service and worker
   - RabbitMQ will be provisioned as a managed database


## Monitoring

### RabbitMQ Management Interface
- Local: http://localhost:15672
- Credentials: user/password

### Worker Logs

docker-compose logs -f worker


On Digital Ocean:
- Adjust the number of worker instances in the app dashboard

## Troubleshooting

1. If the web server fails to start:
   - Check if RabbitMQ is running
   - Verify environment variables

2. If analysis fails:
   - Check worker logs
   - Verify API keys
   - Ensure website is accessible

3. If queue builds up:
   - Scale up workers
   - Check for worker errors
   - Monitor RabbitMQ dashboard

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License

## Acknowledgments

- Built with [crewAI](https://github.com/joaomdmoura/crewAI)
- Uses OpenAI's GPT-4 for analysis
- Powered by [browserless.io](https://browserless.io) for web scraping
- Queue system using [RabbitMQ](https://www.rabbitmq.com/)