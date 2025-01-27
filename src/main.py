#!/usr/bin/env python
import sys
import warnings
from crew import SEOAnalyseCrew



warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    # Prompt for website URL
    website_url = input("Enter the website URL to analyze: ")
    
    # Create crew with the URL
    crew = SEOAnalyseCrew(website_url=website_url)
    
    # Start the crew process
    crew.crew().kickoff()

run()
