import asyncio
import aio_pika
import json
import os
from crew import SEOAnalyseCrew

async def process_message(message: aio_pika.IncomingMessage):
    async with message.process():
        # Parse message
        body = json.loads(message.body.decode())
        website_url = body["website_url"]
        
        try:
            # Run SEO analysis
            crew = SEOAnalyseCrew(website_url)
            result = crew.crew()
            
            # Here you could store the results in a database
            print(f"Analysis completed for {website_url}")
            
        except Exception as e:
            print(f"Error processing {website_url}: {str(e)}")

async def main():
    # Connect to RabbitMQ
    connection = await aio_pika.connect_robust(
        f"amqp://user:password@{os.getenv('RABBITMQ_HOST', 'localhost')}"
    )
    
    async with connection:
        # Create channel
        channel = await connection.channel()
        
        # Declare queue
        queue = await channel.declare_queue("seo_analysis")
        
        # Start consuming messages
        await queue.consume(process_message)
        
        try:
            # Wait until terminate
            await asyncio.Future()
        finally:
            await connection.close()

if __name__ == "__main__":
    asyncio.run(main()) 