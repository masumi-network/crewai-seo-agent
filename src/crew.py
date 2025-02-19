# Import necessary libraries:
# - crewAI for agent/crew functionality
# - dotenv for environment variables
# - yaml for config files
# - Various tools for web scraping and PDF generation
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv
import openai
import os
import yaml
from tools.LoadingTimeTracker import LoadingTimeTracker
from tools.MobileTesting import MobileOptimizationTool
from tools.SubpageAnalyzer import SubpageAnalyzer
from tools.BrowserlessScraper import BrowserlessScraper
import asyncio
from typing import Dict, Any, List
import logging

# Add this near the top of the file, after imports
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Main SEO Analysis Crew class decorated with CrewBase
@CrewBase
class SEOAnalyseCrew():
    """
    Main class that orchestrates the SEO analysis process using multiple AI agents.
    It handles data collection, analysis, and optimization recommendations.
    """

    # Config file paths
    agents_config = os.path.join(os.path.dirname(__file__), 'config', 'agents.yaml')
    tasks_config = os.path.join(os.path.dirname(__file__), 'config', 'tasks.yaml')

    def __init__(self, website_url: str):
        """Initialize with target website URL and load config files"""
        self.website_url = website_url
        logger.info(f"Initializing SEO Analysis Crew for {website_url}")
        
        # Load agent and task configurations from YAML files
        with open(self.agents_config, 'r') as f:
            self.agents_config = yaml.safe_load(f)
        with open(self.tasks_config, 'r') as f:
            self.tasks_config = yaml.safe_load(f)
            
        # Initialize tools
        self.tools = [
            BrowserlessScraper(),
            LoadingTimeTracker(),
            MobileOptimizationTool(),
            SubpageAnalyzer()
        ]
        logger.info("Tools initialized successfully")
        
        # Initialize agents dictionary
        self.agents = {
            'scraper_agent': self.scraper_agent(),
            'analyse_agent': self.analyse_agent(),
            'optimization_agent': self.optimization_agent()
        }
        logger.info("Agents initialized successfully")
        
        self.tool_timeout = 60  # 60 second timeout for each tool
        super().__init__()

    # Configure GPT-4 with specific settings
    openai_llm = LLM(
        model='gpt-4o',  
        api_key=os.getenv('OPENAI_API_KEY'),
        max_retries=3,
        temperature=0.5
    )

    @agent
    def scraper_agent(self) -> Agent:
        """Agent responsible for collecting data from the website"""        
        return Agent(
            role=self.agents_config['scraper_agent']['role'],
            goal=self.agents_config['scraper_agent']['goal'],
            backstory=self.agents_config['scraper_agent']['backstory'],
            tools=[
                BrowserlessScraper(),
                LoadingTimeTracker(),
                MobileOptimizationTool(),
                SubpageAnalyzer(),
            ],
            verbose=True,
            llm=self.openai_llm  
        )

    @agent
    def analyse_agent(self) -> Agent:
        """Agent responsible for analyzing collected data"""
        return Agent(
            role=self.agents_config['analyse_agent']['role'],
            goal=self.agents_config['analyse_agent']['goal'],
            backstory=self.agents_config['analyse_agent']['backstory'],
            verbose=True,
            llm=self.openai_llm  
        )
    
    @agent
    def optimization_agent(self) -> Agent:
        """Agent responsible for providing optimization recommendations"""
        return Agent(
            role=self.agents_config['optimization_agent']['role'],
            goal=self.agents_config['optimization_agent']['goal'],
            backstory=self.agents_config['optimization_agent']['backstory'],
            verbose=True,
            llm=self.openai_llm  
        )

    @task
    def data_collection_task(self) -> Task:
        """Task for collecting website data"""
        task_config = self.tasks_config['data_collection_task']
        return Task(
            description=task_config['description'].format(website_url=self.website_url),
            expected_output=task_config['expected_output'].format(website_url=self.website_url),
            agent=self.agents['scraper_agent'],
            context_variables={"website_url": self.website_url},
            max_retries=3
        )

    @task
    def analysis_task(self) -> Task:
        """Task for analyzing collected data"""
        task_config = self.tasks_config['analysis_task']
        return Task(
            description=task_config['description'].format(website_url=self.website_url),
            agent=self.agents['analyse_agent'],
            expected_output=task_config['expected_output']
        )

    @task
    def optimization_task(self) -> Task:
        """Task for generating optimization recommendations"""
        task_config = self.tasks_config['optimization_task']
        return Task(
            description=task_config['description'],
            agent=self.agents['optimization_agent'],
            expected_output=task_config['expected_output']
        )

    @crew
    def crew(self) -> dict:
        """
        Creates and runs the SEO analysis crew.
        Returns results as a dictionary for JSON storage.
        """
        crew_instance = Crew(
            agents=self.agents, 
            tasks=[
                self.data_collection_task(),
                self.analysis_task(),
                self.optimization_task()
            ],
            process=Process.sequential,
            verbose=True,
        )
        
        # Run the analysis
        result = crew_instance.kickoff()
        
        # Parse and structure the results
        try:
            # Convert the crew's output into structured data
            structured_results = {
                'meta_tags': {},
                'headings': {},
                'keywords': {},
                'links': {},
                'images': {},
                'content_stats': {},
                'mobile_stats': {},
                'performance_stats': {},
                'recommendations': {}
            }
            
            # Parse the result string and populate the structured_results
            # This will depend on your specific output format
            # You might need to adjust this parsing logic
            
            return structured_results
            
        except Exception as e:
            return {
                'error': str(e),
                'raw_result': result
            }

    async def analyze(self) -> Dict[str, Any]:
        """Run the full SEO analysis"""
        try:
            logger.info("Starting SEO analysis crew...")
            
            # Create tasks
            data_collection = self.data_collection_task()
            analysis = self.analysis_task()
            optimization = self.optimization_task()
            
            # Create crew with tasks
            crew = Crew(
                agents=[self.scraper_agent(), self.analyse_agent(), self.optimization_agent()],
                tasks=[data_collection, analysis, optimization],
                verbose=True
            )
            
            # Run crew and get results
            results = await crew.run()
            
            # Process results into structured format
            structured_results = self._process_results(results)
            
            return structured_results
            
        except Exception as e:
            logger.error(f"Crew analysis error: {str(e)}")
            raise

    def _process_results(self, results) -> Dict[str, Any]:
        """Process the crew results into a structured format"""
        try:
            # Initialize the results structure
            processed_results = {
                'meta_tags': {},
                'headings': {},
                'keywords': {},
                'links': {},
                'images': {},
                'content_stats': {},
                'mobile_stats': {},
                'performance_stats': {},
                'recommendations': {}
            }
            
            # Extract data from CrewOutput
            if hasattr(results, 'raw_output'):
                raw_results = results.raw_output
            else:
                raw_results = results

            # Process each task output
            for output in raw_results:
                if isinstance(output, str):
                    if "Meta Tags Analysis:" in output:
                        processed_results['meta_tags'] = self._extract_meta_info(output)
                    if "Content Analysis:" in output:
                        processed_results['keywords'] = self._extract_keyword_info(output)
                    if "Content Structure:" in output:
                        processed_results['headings'] = self._extract_heading_info(output)
                    if "Link Analysis:" in output:
                        processed_results['links'] = self._extract_link_info(output)
                    if "Media Inventory:" in output:
                        processed_results['images'] = self._extract_image_info(output)
                    if "Performance Metrics:" in output:
                        processed_results['performance_stats'] = self._extract_performance_info(output)
                    if "OPTIMIZATION RECOMMENDATIONS" in output:
                        processed_results['recommendations'] = self._extract_recommendations(output)

            return processed_results
            
        except Exception as e:
            logger.error(f"Error processing results: {str(e)}")
            raise

    def _extract_meta_info(self, text: str) -> Dict:
        """Extract meta tag information"""
        meta_info = {'total_tags': 0, 'tags': {}}
        try:
            lines = text.split('\n')
            for line in lines:
                if 'Total number of meta tags:' in line:
                    meta_info['total_tags'] = int(line.split(':')[1].strip())
                if '*' in line and ':' in line:
                    tag, count = line.split(':')
                    meta_info['tags'][tag.strip('* ')] = int(count.split()[0])
        except Exception:
            pass
        return meta_info

    # Add similar extraction methods for other sections
    # _extract_keyword_info, _extract_heading_info, etc.

    async def run(self) -> Dict[str, Any]:
        """Run the SEO analysis crew and return results"""
        try:
            # Create and configure the crew
            crew = Crew(
                agents=[self.scraper_agent(), self.analyse_agent(), self.optimization_agent()],
                tasks=[
                    self.data_collection_task(),
                    self.analysis_task(),
                    self.optimization_task()
                ],
                process=Process.sequential,
                verbose=True
            )
            
            # Run the crew and get results
            crew_output = crew.kickoff()  # Remove await since kickoff() returns CrewOutput directly
            
            # Process and return results
            return self._process_results(crew_output)
            
        except Exception as e:
            logger.error(f"Crew run error: {str(e)}")
            raise
