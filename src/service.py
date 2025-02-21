# src/service.py
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

from .db.database import Database
from .crew import SEOAnalyseCrew

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
        rabbitmq_url = os.getenv('RABBITMQ_URL')
        
        if rabbitmq_url:
            parameters = pika.URLParameters(rabbitmq_url)
        else:
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

def process_message(ch, method, properties, body):
    """Process message from RabbitMQ queue"""
    try:
        data = json.loads(body)
        job_id = data['job_id']
        website_url = data['website_url']
        
        db.update_job_status(job_id, 'running')
        
        crew = SEOAnalyseCrew(website_url)
        results = asyncio.run(crew.run())
        
        if results and "error" not in results:
            db.store_results(job_id, results)
            db.update_job_status(job_id, 'completed')
        else:
            error_msg = results.get('error', 'No results returned') if results else 'Analysis failed'
            db.update_job_status(job_id, 'error', error_msg)
            
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        if 'job_id' in locals():
            db.update_job_status(job_id, 'error', str(e))
        if 'method' in locals():
            ch.basic_ack(delivery_tag=method.delivery_tag)

@app.post("/start_job")
async def start_job(input_data: InputData):
    """Start a new analysis job"""
    try:
        job_id = db.create_job(input_data.website_url)
        
        connection = get_rabbitmq_connection()
        if not connection:
            raise HTTPException(status_code=503, detail="Queue service unavailable")
            
        channel = connection.channel()
        channel.queue_declare(queue='seo_analysis', durable=True)
        
        channel.basic_publish(
            exchange='',
            routing_key='seo_analysis',
            body=json.dumps({
                'job_id': job_id,
                'website_url': input_data.website_url,
                'max_pages': input_data.max_pages
            }),
            properties=pika.BasicProperties(
                delivery_mode=2
            )
        )
        
        return {
            "status": "success",
            "job_id": str(job_id),
            "payment_id": f"pay_{job_id}"
        }
        
    except Exception as e:
        logger.error(f"Error starting job: {str(e)}")
        raise HTTPException(status_code=500, detail="Error starting analysis job")

@app.get("/status")
async def get_status(job_id: int):
    """Get job status and results"""
    try:
        job = db.get_job_status(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        response = {
            "job_id": job_id,
            "status": job['status'],
            "created_at": job['created_at'].isoformat(),
            "started_at": job['started_at'].isoformat() if job['started_at'] else None,
            "completed_at": job['completed_at'].isoformat() if job['completed_at'] else None
        }

        if job['status'] == 'error' and job['error']:
            response["error"] = job['error']

        if job['status'] == 'completed':
            results = db.get_job_results(job_id)
            if results:
                response["result"] = {
                    "meta_tags": json.loads(results['meta_tags']) if results['meta_tags'] else {},
                    "headings": json.loads(results['headings']) if results['headings'] else {},
                    "keywords": json.loads(results['keywords']) if results['keywords'] else {},
                    "links": json.loads(results['links']) if results['links'] else {},
                    "images": json.loads(results['images']) if results['images'] else {},
                    "content_stats": json.loads(results['content_stats']) if results['content_stats'] else {},
                    "mobile_stats": json.loads(results['mobile_stats']) if results['mobile_stats'] else {},
                    "performance_stats": json.loads(results['performance_stats']) if results['performance_stats'] else {},
                    "recommendations": json.loads(results['recommendations']) if results['recommendations'] else {}
                }

        return response

    except Exception as e:
        logger.error(f"Error checking status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/availability")
async def check_availability():
    """Check service availability"""
    try:
        db.get_cursor()
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
    """Get expected input schema"""
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
    """Health check endpoint"""
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

@app.on_event("startup")
async def startup_event():
    """Start worker thread on startup"""
    if os.getenv('DYNO'):
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
    worker_thread = threading.Thread(target=start_worker, daemon=True)
    worker_thread.start()
    logger.info("Worker thread started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logging.info("Shutting down worker...")