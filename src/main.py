#!/usr/bin/env python
import sys
import warnings
from crew import SEOAnalyseCrew
import openai

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def check_openai_connection():
    try:
        # Test the API connection
        openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        return True
    except Exception as e:
        print(f"Error connecting to OpenAI API: {str(e)}")
        print("Please check your internet connection and API key.")
        return False

def run():
    """
    Run the crew.
    """
    if not check_openai_connection():
        sys.exit(1)
        
    # Prompt for website URL
    website_url = input("Enter the website URL to make SEO analysis: ")
    
    # Create crew with the URL
    crew = SEOAnalyseCrew(website_url)
    
    # Get the crew instance and kickoff
    crew_instance = crew.crew()
    if hasattr(crew_instance, 'kickoff'):
        result = crew_instance.kickoff()
    else:
        result = crew_instance  # For newer versions of crewAI

if __name__ == "__main__":
    run()
