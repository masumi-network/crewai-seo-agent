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
from crewai_tools import ScrapeWebsiteTool, SeleniumScrapingTool
from tools.SeleniumScraper import SeleniumScraper
from tools.LoadingTimeTracker import LoadingTimeTracker
from tools.MobileTesting import MobileOptimizationTool
import markdown
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from html.parser import HTMLParser
from tools.OffPageSEOAnalyzer import OffPageSEOAnalyzer

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
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self, website_url: str):
        """Initialize with target website URL and load config files"""
        self.website_url = website_url
        # Load agent and task configurations from YAML files
        with open(self.agents_config, 'r') as f:
            self.agents_config = yaml.safe_load(f)
        with open(self.tasks_config, 'r') as f:
            self.tasks_config = yaml.safe_load(f)

    # Configure GPT-4 with specific settings
    openai_llm = LLM(
        model='gpt-4',  
        api_key=os.getenv('OPENAI_API_KEY'),
        max_retries=3,
        request_timeout=60,
        temperature=0.5
    )

    @agent
    def scraper_agent(self) -> Agent:
        """Agent responsible for collecting data from the website"""		
        return Agent(
            config=self.agents_config['scraper_agent'],
            tools=[
                SeleniumScraper(),
                LoadingTimeTracker(),
                MobileOptimizationTool(),
                OffPageSEOAnalyzer(),
            ],
            verbose=True,
            llm=self.openai_llm  
        )

    @agent
    def analyse_agent(self) -> Agent:
        """Agent responsible for analyzing collected data"""
        return Agent(
            config=self.agents_config['analyse_agent'],
            verbose=True,
            llm=self.openai_llm  
        )
    
    @agent
    def optimization_agent(self) -> Agent:
        """Agent responsible for providing optimization recommendations"""
        return Agent(
            config=self.agents_config['optimization_agent'],
            verbose=True,
            llm=self.openai_llm  
        )

    @task
    def data_collection_task(self) -> Task:
        """Task for collecting website data"""
        task_config = self.tasks_config['data_collection_task']
        return Task(
            description=task_config['description'].format(website_url=self.website_url),
            agent=self.scraper_agent(),
            expected_output=task_config['expected_output'],
        )

    @task
    def analysis_task(self) -> Task:
        """Task for analyzing collected data"""
        task_config = self.tasks_config['analysis_task']
        return Task(
            description=task_config['description'].format(website_url=self.website_url),
            agent=self.analyse_agent(),
            expected_output=task_config['expected_output'],
            output_file='report.md'
        )

    @task
    def optimization_task(self) -> Task:
        """Task for generating optimization recommendations"""
        task_config = self.tasks_config['optimization_task']
        return Task(
            description=task_config['description'],
            agent=self.optimization_agent(),
            expected_output=task_config['expected_output'],
            output_file='report.md'
        )

    # Helper class for stripping HTML tags
    class MLStripper(HTMLParser):
        """Utility class to remove HTML tags from text"""
        def __init__(self):
            super().__init__()
            self.reset()
            self.strict = False
            self.convert_charrefs = True
            self.text = []
        
        def handle_data(self, d):
            self.text.append(d)
        
        def get_data(self):
            return ''.join(self.text)

    def strip_tags(self, html):
        """Remove HTML tags from a string"""
        s = self.MLStripper()
        s.feed(html)
        return s.get_data()

    def convert_to_pdf(self):
        """
        Converts the markdown report to a formatted PDF file.
        Handles the entire process of:
        - Reading markdown
        - Converting to HTML
        - Formatting with styles
        - Generating PDF with proper layout
        """
        try:
            # Clean up domain name for filename
            domain = self.website_url.replace('https://', '').replace('http://', '').replace('www.', '')
            domain = domain.rstrip('/').replace('/', '_')
            
            pdf_filename = f"seo_report-{domain}.pdf"
            
            # Read and convert markdown
            with open('report.md', 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            html_content = markdown.markdown(markdown_content)
            
            # Setup PDF document
            doc = SimpleDocTemplate(
                pdf_filename,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Define document styles
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(
                name='CustomTitle',
                parent=styles['Title'],
                fontSize=24,
                spaceAfter=30
            ))
            styles.add(ParagraphStyle(
                name='CustomHeading1',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=16
            ))
            styles.add(ParagraphStyle(
                name='CustomHeading2',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=14
            ))
            styles.add(ParagraphStyle(
                name='CustomBody',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=12
            ))
            
            # Build document content
            story = []
            story.append(Paragraph(f"SEO Analysis Report - {domain}", styles['CustomTitle']))
            story.append(Spacer(1, 12))
            
            # Process each line and apply appropriate styling
            lines = html_content.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('<h1>'):
                    text = self.strip_tags(line)
                    story.append(Paragraph(text, styles['CustomHeading1']))
                elif line.startswith('<h2>'):
                    text = self.strip_tags(line)
                    story.append(Paragraph(text, styles['CustomHeading2']))
                else:
                    text = self.strip_tags(line)
                    story.append(Paragraph(text, styles['CustomBody']))
                
                story.append(Spacer(1, 6))
            
            # Generate final PDF
            doc.build(story)
            print(f"PDF report generated successfully as '{pdf_filename}'")
            
        except Exception as e:
            print(f"Error converting to PDF: {str(e)}")
            print("The markdown file was still generated as 'report.md'")

    @crew
    def crew(self) -> Crew:
        """
        Creates and runs the SEO analysis crew.
        Executes tasks sequentially and generates final report.
        """
        crew_instance = Crew(
            agents=self.agents, 
            tasks=self.tasks, 
            process=Process.sequential,
            verbose=True,
        )
        result = crew_instance.kickoff()
        self.convert_to_pdf()
        return result
