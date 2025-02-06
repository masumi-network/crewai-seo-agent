import pika
import time
import sys

def wait_for_rabbitmq():
    retries = 30
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

def callback(ch, method, properties, body):
    print(f" [x] Received {body}")
    # Add your SEO analysis logic here
    time.sleep(1)  # Simulate some work
    print(f" [x] Done processing {body}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    # Wait for RabbitMQ
    if not wait_for_rabbitmq():
        print("Could not connect to RabbitMQ")
        sys.exit(1)

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host='rabbitmq',
            credentials=pika.PlainCredentials('user', 'password')
        )
    )
    channel = connection.channel()
    
    # Make sure queue name matches what's used in main.py
    channel.queue_declare(queue='seo_tasks')
    
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='seo_tasks', on_message_callback=callback)
    
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    main() 