from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import aio_pika
import json
import os
from typing import Dict

app = FastAPI()

class AnalysisRequest(BaseModel):
    website_url: str

async def send_to_queue(website_url: str):
    # Connect to RabbitMQ
    connection = await aio_pika.connect_robust(
        f"amqp://user:password@{os.getenv('RABBITMQ_HOST', 'localhost')}"
    )
    
    async with connection:
        # Create channel
        channel = await connection.channel()

        # Declare queue
        queue = await channel.declare_queue("seo_analysis")

        # Send message
        await channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps({
                "website_url": website_url
            }).encode()),
            routing_key="seo_analysis"
        )

@app.post("/analyze")
async def analyze_website(request: AnalysisRequest, background_tasks: BackgroundTasks):
    # Add task to queue
    background_tasks.add_task(send_to_queue, request.website_url)
    return {"message": "Analysis request queued", "website_url": request.website_url}

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 