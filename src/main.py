#!/usr/bin/env python
# This is the main entry point file for an SEO analysis tool that uses crewAI

import sys
import warnings
from crew import SEOAnalyseCrew  # Imports the custom SEO analysis crew
import openai

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

def run():
    """
    Main function that:
    1. Checks OpenAI connectivity
    2. Gets website URL from user
    3. Creates and runs the SEO analysis crew
    """
    # Exit if OpenAI connection fails
    if not check_openai_connection():
        sys.exit(1)
        
    # Get the target website URL from user input
    website_url = input("Enter the website URL to make SEO analysis: ")
    
    # Initialize the SEO analysis crew with the URL
    crew = SEOAnalyseCrew(website_url)
    
    # Get crew instance and start analysis
    # Handles both old and new versions of crewAI
    crew_instance = crew.crew()
    if hasattr(crew_instance, 'kickoff'):
        result = crew_instance.kickoff()  # Old version
    else:
        result = crew_instance  # New version

def test_pdf():
    """Test function to convert markdown to PDF without running the crew"""
    crew = SEOAnalyseCrew("test.com")
    crew.test_pdf_conversion()

def main():
    run()

# Run the analysis if this file is executed directly
if __name__ == "__main__":
    # Add command line argument handling
    if len(sys.argv) > 1 and sys.argv[1] == "--test-pdf":
        test_pdf()
    else:
        main()
