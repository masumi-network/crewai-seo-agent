import pika
import time
import sys
import json
from src.crew import SEOAnalyseCrew

def wait_for_rabbitmq():
    retries = 30
    while retries > 0:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host='rabbitmq',
                    credentials=pika.PlainCredentials('user', 'password'),
                    connection_attempts=5,
                    retry_delay=5
                )
            )
            connection.close()
            return True
        except pika.exceptions.AMQPConnectionError:
            retries -= 1
            print(f"Waiting for RabbitMQ to be ready... {retries} attempts left")
            time.sleep(2)
    return False

def callback(ch, method, properties, body):
    try:
        print(f" [x] Received job: {body.decode()}")  # Decode bytes to string
        job_data = json.loads(body)
        website_url = job_data.get('website_url')
        job_id = job_data.get('job_id')
        print(f"Processing job {job_id} for URL: {website_url}")

        if not website_url:
            print("Error: No website URL in job data")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # Run SEO analysis
        print(f"Starting analysis for {website_url}")
        crew = SEOAnalyseCrew(website_url)
        
        # Run analysis synchronously since we're in a callback
        try:
            result = crew.crew().kickoff()  # Use the crew's kickoff method
            print(f"Analysis completed for {website_url}. Result: {result}")
        except Exception as analysis_error:
            print(f"Analysis failed: {str(analysis_error)}")
            result = {"error": str(analysis_error)}
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"Error processing job: {str(e)}")
        import traceback
        print(traceback.format_exc())  # Print full stack trace
        ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    # Wait for RabbitMQ
    if not wait_for_rabbitmq():
        print("Could not connect to RabbitMQ")
        sys.exit(1)

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host='rabbitmq',
            credentials=pika.PlainCredentials('user', 'password'),
            connection_attempts=5,
            retry_delay=5
        )
    )
    channel = connection.channel()
    
    # Declare queue as durable to match test_queue.py
    channel.queue_declare(queue='seo_tasks', durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='seo_tasks', on_message_callback=callback)
    
    print(' [*] Worker ready. Waiting for SEO analysis jobs...')
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    finally:
        connection.close()

if __name__ == '__main__':
    main() 