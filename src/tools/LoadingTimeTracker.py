# Import required libraries:
# - crewai.tools.BaseTool: Base class for creating custom tools
# - typing: For type hints
# - pydantic: For data validation and settings management
# - requests: For making HTTP requests
# - time: For timing measurements
# - urlparse: For parsing URLs
from crewai.tools import BaseTool
from typing import Type, Dict
from pydantic import BaseModel, Field
import requests
import time
from urllib.parse import urlparse

# Define input schema requiring a URL to test
class LoadingTimeTrackerInput(BaseModel):
    """Input for LoadingTimeTracker"""
    url: str = Field(..., description="The URL to check loading time for")

# Main loading time tracking tool
class LoadingTimeTracker(BaseTool):
    # Tool metadata
    name: str = "Loading Time Tracker"
    description: str = "Tracks and analyzes the loading time of a given webpage by taking multiple samples"
    args_schema: Type[BaseModel] = LoadingTimeTrackerInput
    history: Dict[str, float] = Field(default_factory=dict)  # Store historical load times by domain

    def _run(self, url: str) -> str:
        """
        Main method that runs the loading time analysis
        
        Args:
            url: Website URL to test
            
        Returns:
            str: Formatted analysis report with loading time statistics
        """
        results = self.measure_load_time(url)
        
        # Return error message if measurement failed
        if results['average'] is None:
            return f"Error: Could not measure loading time for {url}"
            
        # Format and return the analysis results
        return (
            f"Loading Time Analysis for {url}:\n"
            f"- Average Loading Time: {results['average']:.2f} seconds\n"
            f"- Min Loading Time: {results['min']:.2f} seconds\n"
            f"- Max Loading Time: {results['max']:.2f} seconds\n"
            f"- Samples Collected: {results['samples']}\n"
        )

    def measure_load_time(self, url: str, num_samples: int = 3) -> Dict[str, float]:
        """
        Measure the loading time of a website by taking multiple samples
        
        Args:
            url: The website URL to measure
            num_samples: Number of samples to take (default 3)
            
        Returns:
            Dict containing average, min and max load times in seconds
        """
        # Ensure URL has protocol
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        load_times = []
        
        # Take multiple samples of load time measurements
        for _ in range(num_samples):
            try:
                # Measure time for request to complete
                start_time = time.time()
                response = requests.get(url, timeout=30)
                end_time = time.time()
                
                # Only record successful requests
                if response.status_code == 200:
                    load_time = end_time - start_time
                    load_times.append(load_time)
                    
            except (requests.RequestException, TimeoutError):
                continue
                
            time.sleep(1)  # Brief pause between requests to avoid overwhelming server
            
        # Return null results if no measurements succeeded
        if not load_times:
            return {
                'average': None,
                'min': None,
                'max': None,
                'samples': 0
            }
            
        # Calculate statistics from measurements
        results = {
            'average': sum(load_times) / len(load_times),
            'min': min(load_times),
            'max': max(load_times),
            'samples': len(load_times)
        }
        
        # Store the average in history keyed by domain
        domain = urlparse(url).netloc
        self.history[domain] = results['average']
        
        return results
    
    def get_history(self) -> Dict[str, float]:
        """Get the history of average load times by domain"""
        return self.history
