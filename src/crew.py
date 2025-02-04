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
from tools.ReferringDomainAnalyzer import ReferringDomainAnalyzer
from tools.SubpageAnalyzer import SubpageAnalyzer
from tools.BrowserlessScraper import BrowserlessScraper

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
            
        # Initialize agents dictionary
        self.agents = {
            'scraper_agent': self.scraper_agent(),
            'analyse_agent': self.analyse_agent(),
            'optimization_agent': self.optimization_agent()
        }

    # Configure GPT-4 with specific settings
    openai_llm = LLM(
        model='gpt-4o',  
        api_key=os.getenv('OPENAI_API_KEY'),
        max_retries=3,
        request_timeout=60,
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
                OffPageSEOAnalyzer(),
                ReferringDomainAnalyzer(),
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
            agent=self.agents['scraper_agent'],  # Use the agent from self.agents
            context_variables={"website_url": self.website_url},
            max_retries=3
        )

    @task
    def analysis_task(self) -> Task:
        """Task for analyzing collected data"""
        task_config = self.tasks_config['analysis_task']
        return Task(
            description=task_config['description'].format(website_url=self.website_url),
            agent=self.agents['analyse_agent'],  # Use the agent from self.agents
            expected_output=task_config['expected_output'],
            output_file='report.md'
        )

    @task
    def optimization_task(self) -> Task:
        """Task for generating optimization recommendations"""
        task_config = self.tasks_config['optimization_task']
        return Task(
            description=task_config['description'],
            agent=self.agents['optimization_agent'],  # Use the agent from self.agents
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
        Converts the markdown report to a clean, well-formatted PDF
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
                rightMargin=50,  # Reduced margins
                leftMargin=50,
                topMargin=50,
                bottomMargin=50
            )
            
            # Define document styles with better spacing
            styles = getSampleStyleSheet()
            
            # Title style
            styles.add(ParagraphStyle(
                name='CustomTitle',
                parent=styles['Title'],
                fontSize=20,  # Smaller title
                spaceAfter=30,
                spaceBefore=20,
                alignment=1  # Center alignment
            ))
            
            # Main heading style
            styles.add(ParagraphStyle(
                name='CustomHeading1',
                parent=styles['Heading1'],
                fontSize=16,  # Smaller heading
                spaceAfter=16,
                spaceBefore=20,
                textColor=colors.HexColor('#2C3E50')  # Dark blue color
            ))
            
            # Subheading style
            styles.add(ParagraphStyle(
                name='CustomHeading2',
                parent=styles['Heading2'],
                fontSize=14,  # Smaller subheading
                spaceAfter=12,
                spaceBefore=15,
                textColor=colors.HexColor('#34495E')  # Lighter blue color
            ))
            
            # Body text style
            styles.add(ParagraphStyle(
                name='CustomBody',
                parent=styles['Normal'],
                fontSize=10,  # Smaller body text
                spaceAfter=8,
                spaceBefore=8,
                leading=14  # Line spacing
            ))
            
            # List item style
            styles.add(ParagraphStyle(
                name='CustomListItem',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=3,
                spaceBefore=3,
                leftIndent=20,
                leading=14
            ))
            
            # Build document content
            story = []
            
            # Add title
            story.append(Paragraph(f"SEO Analysis Report", styles['CustomTitle']))
            story.append(Paragraph(f"Domain: {domain}", styles['CustomHeading2']))
            story.append(Spacer(1, 20))
            
            # Process each line and apply appropriate styling
            lines = html_content.split('\n')
            in_list = False
            
            for line in lines:
                line = line.strip()
                if not line:
                    if in_list:
                        story.append(Spacer(1, 8))
                    else:
                        story.append(Spacer(1, 12))
                    continue
                
                if line.startswith('<h1>'):
                    in_list = False
                    text = self.strip_tags(line)
                    story.append(Paragraph(text, styles['CustomHeading1']))
                elif line.startswith('<h2>'):
                    in_list = False
                    text = self.strip_tags(line)
                    story.append(Paragraph(text, styles['CustomHeading2']))
                elif line.startswith('- ') or line.startswith('* '):
                    in_list = True
                    text = self.strip_tags(line)
                    story.append(Paragraph(text, styles['CustomListItem']))
                else:
                    in_list = False
                    text = self.strip_tags(line)
                    story.append(Paragraph(text, styles['CustomBody']))
            
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
