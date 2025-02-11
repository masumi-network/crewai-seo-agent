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

# Ignore syntax warnings from the pysbd module
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

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

app = FastAPI()

class AnalysisRequest(BaseModel):
    website_url: str

class JobStatus(BaseModel):
    job_id: str
    payment_id: Optional[str]
    status: str
    result: Optional[dict] = None

@app.post("/start_job")
async def start_job(request: AnalysisRequest):
    try:
        # Create a connection to RabbitMQ
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host='rabbitmq',
                credentials=pika.PlainCredentials('user', 'password')
            )
        )
        channel = connection.channel()
        
        # Declare queue
        channel.queue_declare(queue='seo_tasks', durable=True)
        
        # Create job data
        job_id = str(uuid.uuid4())
        job_data = {
            'website_url': request.website_url,
            'job_id': job_id
        }
        
        # Publish message
        channel.basic_publish(
            exchange='',
            routing_key='seo_tasks',
            body=json.dumps(job_data),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            )
        )
        
        connection.close()
        return {"job_id": job_id, "status": "queued"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    # For now, just return that the job is in progress
    # You can implement actual status tracking later
    return {"job_id": job_id, "status": "in_progress"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
