from fastapi import FastAPI, HTTPException, Response, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
import pika
import json
import threading
import time
import asyncio
from datetime import datetime
from typing import Optional
from pika.exceptions import AMQPConnectionError
import ssl
import os

# Update these imports to use relative imports since we're inside the src package
from .db.database import Database
from .crew import SEOAnalyseCrew

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()
db = Database()

class InputData(BaseModel):
    """Schema for input data"""
    website_url: str
    max_pages: int = 50

def get_rabbitmq_connection() -> Optional[pika.BlockingConnection]:
    """Create RabbitMQ connection with retry logic"""
    try:
        # Get RabbitMQ URL from environment
        rabbitmq_url = os.getenv('RABBITMQ_URL')
        
        if rabbitmq_url:
            # Use CloudAMQP URL directly
            parameters = pika.URLParameters(rabbitmq_url)
        else:
            # Fallback for local development
            credentials = pika.PlainCredentials(
                os.getenv('RABBITMQ_USER', 'user'),
                os.getenv('RABBITMQ_PASS', 'password')
            )
            parameters = pika.ConnectionParameters(
                host=os.getenv('RABBITMQ_HOST', 'rabbitmq'),
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            
        return pika.BlockingConnection(parameters)
    except Exception as e:
        logger.error(f"RabbitMQ connection error: {str(e)}")
        return None

async def process_seo_analysis(job_id: int, website_url: str):
    """Process SEO analysis"""
    try:
        logger.info(f"Starting analysis for job {job_id}")
        db.update_job_status(job_id, 'processing', None)
        
        # Create crew instance
        crew = SEOAnalyseCrew(website_url)
        
        try:
            # Run analysis and get results - no need to await since run() handles it
            results = await crew.run()
            
            if results:
                # Store results in database
                db.store_results(job_id, results)
                logger.info(f"Analysis completed for job {job_id}")
            else:
                error_msg = "No results returned from analysis"
                logger.error(f"Analysis failed for job {job_id}: {error_msg}")
                db.update_job_status(job_id, 'failed', error_msg)
                
        except Exception as e:
            error_msg = f"Analysis error: {str(e)}"
            logger.error(f"Job {job_id} failed: {error_msg}")
            db.update_job_status(job_id, 'failed', error_msg)
            raise
            
    except Exception as e:
        error_msg = f"Process error: {str(e)}"
        logger.error(f"Job {job_id} failed: {error_msg}")
        db.update_job_status(job_id, 'failed', error_msg)
        raise

def process_message(ch, method, properties, body):
    """Process message from RabbitMQ queue"""
    try:
        data = json.loads(body)
        job_id = data['job_id']
        website_url = data['website_url']
        
        # Update job status to running
        db.update_job_status(job_id, 'running')
        
        # Create and run crew
        crew = SEOAnalyseCrew(website_url)
        results = asyncio.run(crew.run())
        
        if results:
            # Store results in database
            db.store_results(job_id, results)
            # Update status to completed
            db.update_job_status(job_id, 'completed')
        else:
            db.update_job_status(job_id, 'error', 'No results returned')
            
        # Acknowledge message
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        if 'job_id' in locals():
            db.update_job_status(job_id, 'error', str(e))
        if 'method' in locals():
            ch.basic_ack(delivery_tag=method.delivery_tag)

@app.post("/start_job")
async def start_job(input_data: InputData):
    """Start a new analysis job (MIP-003 compliant)"""
    try:
        # Create job in database
        job_id = db.create_job(input_data.website_url)
        
        # Queue the job
        connection = get_rabbitmq_connection()
        if not connection:
            raise HTTPException(status_code=503, detail="Queue service unavailable")
            
        channel = connection.channel()
        channel.queue_declare(queue='seo_analysis', durable=True)
        
        # Queue the message
        channel.basic_publish(
            exchange='',
            routing_key='seo_analysis',
            body=json.dumps({
                'job_id': job_id,
                'website_url': input_data.website_url,
                'max_pages': input_data.max_pages
            }),
            properties=pika.BasicProperties(
                delivery_mode=2  # make message persistent
            )
        )
        
        return {
            "status": "success",
            "job_id": str(job_id),
            "payment_id": f"pay_{job_id}"  # placeholder for payment integration
        }
        
    except Exception as e:
        logger.error(f"Error starting job: {str(e)}")
        raise HTTPException(status_code=500, detail="Error starting analysis job")

@app.get("/status")
async def get_status(job_id: int):
    """Get job status and results"""
    try:
        # Get job status
        job = db.get_job_status(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Create base response
        response = {
            "job_id": job_id,
            "status": job['status']
        }

        # Add results if job is completed
        if job['status'] == 'completed':
            results = db.get_job_results(job_id)
            if results:
                try:
                    # Parse recommendations from JSON string if it exists
                    recommendations = json.loads(results['recommendations']) if results['recommendations'] else {}
                    response["result"] = {"recommendations": recommendations}
                except (json.JSONDecodeError, TypeError) as e:
                    logger.error(f"Error parsing recommendations for job {job_id}: {str(e)}")
                    response["result"] = {"recommendations": {}}

        return response

    except Exception as e:
        logger.error(f"Error checking status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/availability")
async def check_availability():
    """Check service availability (MIP-003 compliant)"""
    try:
        # Check database connection
        db.get_cursor()
        
        # Check RabbitMQ connection
        connection = get_rabbitmq_connection()
        if not connection:
            return {
                "status": "unavailable",
                "message": "Queue service is not responding"
            }
            
        return {
            "status": "available",
            "message": "Service is operational"
        }
        
    except Exception as e:
        return {
            "status": "unavailable",
            "message": str(e)
        }

@app.get("/input_schema")
async def get_input_schema():
    """Get expected input schema (MIP-003 compliant)"""
    return {
        "type": "object",
        "properties": {
            "input_data": {
                "type": "object",
                "properties": {
                    "website_url": {
                        "type": "string",
                        "description": "URL of the website to analyze"
                    },
                    "max_pages": {
                        "type": "integer",
                        "description": "Maximum number of pages to analyze",
                        "default": 50
                    },
                    "analysis_depth": {
                        "type": "string",
                        "description": "Depth of analysis (standard/deep)",
                        "default": "standard",
                        "enum": ["standard", "deep"]
                    }
                },
                "required": ["website_url"]
            }
        }
    }

@app.get("/health")
@app.head("/health")
async def health_check():
    """Health check endpoint for monitoring and container orchestration"""
    return JSONResponse(
        content={"status": "healthy"},
        headers={"Cache-Control": "no-cache"}
    )

def start_worker():
    """Worker process to consume RabbitMQ messages"""
    while True:
        try:
            connection = get_rabbitmq_connection()
            if not connection:
                logger.error("RabbitMQ connection failed, retrying in 5s...")
                time.sleep(5)
                continue
                
            channel = connection.channel()
            channel.queue_declare(queue='seo_analysis', durable=True)
            channel.basic_qos(prefetch_count=1)
            
            logger.info("Worker started, waiting for messages...")
            channel.basic_consume(
                queue='seo_analysis',
                on_message_callback=process_message
            )
            
            channel.start_consuming()
            
        except Exception as e:
            logger.error(f"Worker error: {str(e)}")
            time.sleep(5)

# Start worker thread when app starts
@app.on_event("startup")
async def startup_event():
    """Start worker thread on startup"""
    if os.getenv('DYNO'):  # Check if running on cloud platform
        # Configure SSL context for CloudAMQP
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
    worker_thread = threading.Thread(target=start_worker, daemon=True)
    worker_thread.start()
    logger.info("Worker thread started")

# Add shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logging.info("Shutting down worker...") 