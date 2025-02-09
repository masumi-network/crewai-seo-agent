#!/usr/bin/env python
# This is the main entry point file for an SEO analysis tool that uses crewAI

import sys
import warnings
from crew import SEOAnalyseCrew  # Imports the custom SEO analysis crew
import openai
import os
import pika
import time

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
