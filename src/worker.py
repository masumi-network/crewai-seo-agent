import pika
import time
import json
from src.crew import SEOAnalyseCrew
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
import sys
import traceback

# Set up logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

QUEUE_NAME = 'seo_tasks'
RABBITMQ_CREDS = {'username': 'user', 'password': 'password'}

def get_rabbitmq_connection():
    """Creates a RabbitMQ connection with standard parameters"""
    logger.info("Attempting to connect to RabbitMQ...")
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host='rabbitmq',
            credentials=pika.PlainCredentials(**RABBITMQ_CREDS),
            heartbeat=600,
            connection_attempts=5,
            retry_delay=5
        )
    )
    logger.info("Successfully connected to RabbitMQ")
    return connection

async def process_seo_analysis(website_url, job_id):
    """Performs SEO analysis for a given URL"""
    try:
        logger.info(f"Starting SEO analysis for {website_url} (Job ID: {job_id})")
        crew = SEOAnalyseCrew(website_url)
        result = await crew.start_analysis()
        logger.info(f"Analysis completed for {website_url}")
        return result
    except Exception as e:
        logger.error(f"Error in SEO analysis: {str(e)}")
        logger.error(traceback.format_exc())
        return {"error": str(e), "job_id": job_id, "status": "failed"}

def callback(ch, method, properties, body):
    """Handles incoming messages from RabbitMQ"""
    job_id = None
    try:
        logger.info(f"Received message: {body.decode()}")
        job_data = json.loads(body)
        website_url = job_data.get('website_url')
        job_id = job_data.get('job_id')
        
        logger.info(f"Processing job {job_id} for URL: {website_url}")
        
        if not website_url:
            logger.error("No website URL in message")
            return

        # Create new event loop for this callback
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(process_seo_analysis(website_url, job_id))
            logger.info(f"Analysis result for {website_url}: {result}")
        finally:
            loop.close()
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        logger.error(traceback.format_exc())
    finally:
        try:
            # Always acknowledge the message
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"Acknowledged message for job {job_id}")
        except Exception as e:
            logger.error(f"Error acknowledging message: {str(e)}")

def main():
    """Main worker function"""
    logger.info("Worker starting up...")
    
    while True:
        try:
            # Create a new connection
            connection = get_rabbitmq_connection()
            channel = connection.channel()
            
            # Declare the queue (idempotent operation)
            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            
            # Set prefetch count to 1 to distribute load
            channel.basic_qos(prefetch_count=1)
            
            logger.info(f"Connected to RabbitMQ, waiting for messages on queue '{QUEUE_NAME}'")
            
            # Start consuming messages
            channel.basic_consume(
                queue=QUEUE_NAME,
                on_message_callback=callback
            )
            
            # Start consuming (blocking operation)
            try:
                logger.info("Starting to consume messages...")
                channel.start_consuming()
            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
                channel.stop_consuming()
                connection.close()
                break
            except Exception as e:
                logger.error(f"Error while consuming: {str(e)}")
                logger.error(traceback.format_exc())
                # Wait before trying to reconnect
                time.sleep(5)
                continue
            
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"AMQP Connection Error: {str(e)}")
            logger.info("Waiting before reconnecting...")
            time.sleep(5)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            logger.error(traceback.format_exc())
            logger.info("Waiting before retrying...")
            time.sleep(5)

if __name__ == '__main__':
    try:
        logger.info("Starting worker process")
        main()
    except KeyboardInterrupt:
        logger.info("Worker shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1) 