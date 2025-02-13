#!/usr/bin/env python
# This is the main entry point file for an SEO analysis tool that uses crewAI

import sys
import warnings
from src.crew import SEOAnalyseCrew  # Updated import path
import openai
import os
import pika
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn
import json
import uuid
import logging

# Ignore syntax warnings from the pysbd module
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

app = FastAPI()
QUEUE_NAME = 'seo_tasks'
RABBITMQ_CREDS = {'username': 'user', 'password': 'password'}

def check_openai_connection():
    """
    Tests the connection to OpenAI's API by making a small test request.
    Returns True if successful, False if there are any connection issues.
    """
    try:
        # Makes a minimal API call to test connectivity
        openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        return True
    except Exception as e:
        # Prints helpful error message if connection fails
        print(f"Error connecting to OpenAI API: {str(e)}")
        print("Please check your internet connection and API key.")
        return False

def wait_for_rabbitmq():
    retries = 30  # Number of retries
    while retries > 0:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host='rabbitmq',
                    credentials=pika.PlainCredentials('user', 'password')
                )
            )
            connection.close()
            return True
        except pika.exceptions.AMQPConnectionError:
            retries -= 1
            print(f"Waiting for RabbitMQ to be ready... {retries} attempts left")
            time.sleep(2)
    return False

def run():
    # Wait for RabbitMQ
    if not wait_for_rabbitmq():
        print("Could not connect to RabbitMQ")
        sys.exit(1)

    # Example using environment variable:
    website_url = os.getenv('WEBSITE_URL', 'https://www.masumi.network/')
    
    # Continue with your existing logic
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host='rabbitmq',
            credentials=pika.PlainCredentials('user', 'password')
        )
    )
    channel = connection.channel()
    
    # Declare the queue
    channel.queue_declare(queue='seo_tasks')
    
    # Exit if OpenAI connection fails
    if not check_openai_connection():
        sys.exit(1)
        
    # Initialize the SEO analysis crew with the URL
    crew = SEOAnalyseCrew(website_url)
    
    # Get crew instance and start analysis
    crew_instance = crew.crew()
    if hasattr(crew_instance, 'kickoff'):
        result = crew_instance.kickoff()
    else:
        result = crew_instance

def main():
    run()

# Run the analysis if this file is executed directly
if __name__ == "__main__":
    main()

class AnalysisRequest(BaseModel):
    website_url: str

class JobStatus(BaseModel):
    job_id: str
    payment_id: Optional[str]
    status: str
    result: Optional[dict] = None

def get_rabbitmq_channel():
    """Establishes connection to RabbitMQ and returns channel"""
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host='rabbitmq',
            credentials=pika.PlainCredentials(**RABBITMQ_CREDS),
            heartbeat=600
        )
    )
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    return connection, channel

@app.post("/start_job")
async def start_job(data: dict):
    """Starts a new SEO analysis job"""
    try:
        website_url = data.get("website_url")
        if not website_url:
            raise HTTPException(status_code=400, detail="website_url is required")

        job_id = str(uuid.uuid4())
        job_data = {
            "job_id": job_id,
            "website_url": website_url
        }

        # Create a new connection for each request
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host='rabbitmq',
                credentials=pika.PlainCredentials(**RABBITMQ_CREDS),
                heartbeat=600,
                connection_attempts=5,
                retry_delay=5
            )
        )
        channel = connection.channel()
        
        # Declare queue as durable
        channel.queue_declare(queue=QUEUE_NAME, durable=True)
        
        # Publish message with persistent delivery mode
        channel.basic_publish(
            exchange='',
            routing_key=QUEUE_NAME,
            body=json.dumps(job_data),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
                content_type='application/json'
            )
        )
        
        # Close connection after publishing
        connection.close()
        return {"status": "Job started", "job_id": job_id}
        
    except Exception as e:
        logger.error(f"Error starting job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    """Gets the status of a job"""
    return {"job_id": job_id, "status": "in_progress"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
