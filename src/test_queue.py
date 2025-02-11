import pika
import json
import time

def test_queue():
    # Connect to RabbitMQ in Docker
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            # Use Docker service name if running inside Docker, localhost if running locally
            host='rabbitmq',  # or 'localhost' if running outside Docker
            port=5672,        # RabbitMQ port
            credentials=pika.PlainCredentials('user', 'password'),
            # Add connection retry logic
            connection_attempts=5,
            retry_delay=5
        )
    )
    channel = connection.channel()
    
    # Declare queue as durable
    channel.queue_declare(queue='seo_tasks', durable=True)
    
    # Test URLs
    test_urls = [
        "https://example.com",
        "https://test.com",
        "https://demo.com"
    ]
    
    try:
        # Send test jobs with persistent delivery mode
        for i, url in enumerate(test_urls):
            job_data = {
                'website_url': url,
                'job_id': f'test_job_{i}'
            }
            
            # Make messages persistent
            channel.basic_publish(
                exchange='',
                routing_key='seo_tasks',
                body=json.dumps(job_data),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                )
            )
            print(f" [x] Sent job for {url}")
            time.sleep(1)  # Small delay between jobs
        
        print("All test jobs sent successfully!")
        
    except Exception as e:
        print(f"Error sending jobs: {str(e)}")
    
    finally:
        connection.close()

if __name__ == "__main__":
    test_queue() 