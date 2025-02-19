# Import required libraries:
# - crewai.tools.BaseTool: Base class for creating custom tools
# - typing: For type hints
# - pydantic: For data validation and settings management
# - requests: For making HTTP requests
# - time: For timing measurements
# - urlparse: For parsing URLs
# - os: For environment variable access
# - statistics: For statistical calculations
# - datetime: For date and time operations
from crewai.tools import BaseTool
from typing import Type, Dict
from pydantic import BaseModel, Field
import requests
import time
import os
import statistics
from datetime import datetime
from urllib.parse import urlparse

# Define input schema requiring a URL to test
class LoadingTimeInput(BaseModel):
    """Input for LoadingTimeTracker"""
    website_url: str = Field(..., description="The URL of the website to analyze")
    samples: int = Field(default=3, description="Number of samples to collect")

# Main loading time tracking tool
class LoadingTimeTracker(BaseTool):
    # Tool metadata
    name: str = "Loading Time Tracker"
    description: str = """
    Tracks website loading times using browserless.io:
    - Measures full page load time
    - Takes multiple samples
    - Provides min/max/average times
    - Tracks network requests
    """
    args_schema: Type[BaseModel] = LoadingTimeInput

    def _run(self, website_url: str, samples: int = 3) -> str:
        """Runs the loading time analysis"""
        try:
            # Reduce samples for faster analysis
            samples = min(samples, 10)  # Maximum 2 samples instead of 3
            
            # Clean up URL
            website_url = website_url.strip('"')
            if not website_url.startswith(('http://', 'https://')):
                website_url = 'https://' + website_url

            # Get browserless API key
            browserless_api_key = os.getenv('BROWSERLESS_API_KEY')
            if not browserless_api_key:
                return "Error: BROWSERLESS_API_KEY not found in environment variables"

            # Configure browserless request
            scrape_url = f'https://chrome.browserless.io/content?token={browserless_api_key}'

            load_times = []
            total_sizes = []
            
            for i in range(samples):
                try:
                    start_time = time.time()
                    
                    # Basic payload for content endpoint
                    payload = {
                        'url': website_url,
                        'gotoOptions': {
                            'waitUntil': 'domcontentloaded',
                            'timeout': 15000
                        }
                    }

                    response = requests.post(
                        scrape_url,
                        json=payload,
                        headers={'Content-Type': 'application/json'},
                        timeout=20
                    )

                    if response.status_code == 200:
                        end_time = time.time()
                        load_time = end_time - start_time
                        load_times.append(load_time)
                        total_sizes.append(len(response.content) / (1024 * 1024))  # Size in MB
                        
                    time.sleep(1)  # Reduced from 2
                    
                except Exception as e:
                    print(f"Error in sample {i + 1}: {str(e)}")
                    continue

            if not load_times:
                return "Error: Could not collect loading time samples"

            # Calculate statistics
            avg_load_time = statistics.mean(load_times)
            min_load_time = min(load_times)
            max_load_time = max(load_times)
            std_dev = statistics.stdev(load_times) if len(load_times) > 1 else 0
            avg_size = statistics.mean(total_sizes)

            # Format results
            report = [
                f"\n=== Loading Time Analysis for {website_url} ===\n",
                f"Samples collected: {len(load_times)}",
                f"Average load time: {avg_load_time:.2f} seconds",
                f"Minimum load time: {min_load_time:.2f} seconds",
                f"Maximum load time: {max_load_time:.2f} seconds",
                f"Standard deviation: {std_dev:.2f} seconds",
                f"Average page size: {avg_size:.2f} MB",
                "\nPerformance Rating:",
                self._get_performance_rating(avg_load_time)
            ]

            return "\n".join(report)

        except Exception as e:
            return f"Error tracking loading time: {str(e)}"

    def _get_performance_rating(self, avg_load_time: float) -> str:
        """Returns a performance rating based on average load time"""
        if avg_load_time <= 2:
            return "Excellent (Under 2 seconds)"
        elif avg_load_time <= 3:
            return "Good (2-3 seconds)"
        elif avg_load_time <= 5:
            return "Fair (3-5 seconds)"
        else:
            return "Poor (Over 5 seconds)"

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
                start_time = time.time()
                response = requests.get(url, timeout=10)  # 10 second timeout
                end_time = time.time()
                
                if response.status_code == 200:
                    load_time = end_time - start_time
                    load_times.append(load_time)
                    
            except (requests.RequestException, TimeoutError):
                continue
                
            time.sleep(0.5)  # Reduced pause between requests
            
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
