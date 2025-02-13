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
from src.tools.LoadingTimeTracker import LoadingTimeTracker
from src.tools.MobileTesting import MobileOptimizationTool
import markdown
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from html.parser import HTMLParser
from src.tools.SubpageAnalyzer import SubpageAnalyzer
from src.tools.BrowserlessScraper import BrowserlessScraper
from concurrent.futures import ThreadPoolExecutor
import uuid

# Load environment variables
load_dotenv()

class HTMLStripper(HTMLParser):
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

@CrewBase
class SEOAnalyseCrew:
    """Main class that orchestrates the SEO analysis process using multiple AI agents."""

    def __init__(self, website_url: str):
        """Initialize with target website URL and load config files"""
        self.website_url = website_url
        self.config_dir = os.path.join(os.path.dirname(__file__), 'config')
        self.agents_config = self._load_config('agents.yaml')
        self.tasks_config = self._load_config('tasks.yaml')
        self.agents = self._initialize_agents()
        self.job_id = str(uuid.uuid4())
        super().__init__()

    def _load_config(self, filename: str) -> dict:
        """Load configuration from YAML file"""
        config_path = os.path.join(self.config_dir, filename)
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _initialize_agents(self) -> dict:
        """Initialize all agents with their configurations"""
        return {
            'scraper_agent': self.scraper_agent(),
            'analyse_agent': self.analyse_agent(),
            'optimization_agent': self.optimization_agent()
        }

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
        config = self.agents_config['scraper_agent']
        return Agent(
            role=config['role'],
            goal=config['goal'],
            backstory=config['backstory'],
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
        config = self.agents_config['analyse_agent']
        return Agent(
            role=config['role'],
            goal=config['goal'],
            backstory=config['backstory'],
            verbose=True,
            llm=self.openai_llm
        )
    
    @agent
    def optimization_agent(self) -> Agent:
        """Agent responsible for providing optimization recommendations"""
        config = self.agents_config['optimization_agent']
        return Agent(
            role=config['role'],
            goal=config['goal'],
            backstory=config['backstory'],
            verbose=True,
            llm=self.openai_llm
        )

    @task
    def data_collection_task(self) -> Task:
        """Task for collecting website data"""
        config = self.tasks_config['data_collection_task']
        return Task(
            description=config['description'].format(website_url=self.website_url),
            expected_output=config['expected_output'].format(website_url=self.website_url),
            agent=self.agents['scraper_agent'],
            context_variables={"website_url": self.website_url},
            max_retries=3
        )

    @task
    def analysis_task(self) -> Task:
        """Task for analyzing collected data"""
        config = self.tasks_config['analysis_task']
        return Task(
            description=config['description'].format(website_url=self.website_url),
            agent=self.agents['analyse_agent'],
            expected_output=config['expected_output'],
            output_file='report.md'
        )

    @task
    def optimization_task(self) -> Task:
        """Task for generating optimization recommendations"""
        config = self.tasks_config['optimization_task']
        return Task(
            description=config['description'],
            agent=self.agents['optimization_agent'],
            expected_output=config['expected_output'],
            output_file='report.md'
        )

    def _create_pdf_styles(self) -> dict:
        """Create and return PDF styles"""
        styles = getSampleStyleSheet()
        custom_styles = {
            'DashboardTitle': ParagraphStyle(
                'DashboardTitle', parent=styles['Title'],
                fontSize=28, spaceAfter=20, spaceBefore=10,
                textColor=colors.HexColor('#1A365D'), alignment=0
            ),
            'SectionHeader': ParagraphStyle(
                'SectionHeader', parent=styles['Heading1'],
                fontSize=16, spaceAfter=10, spaceBefore=10,
                textColor=colors.HexColor('#2C5282')
            ),
            'SubsectionHeader': ParagraphStyle(
                'SubsectionHeader', parent=styles['Heading2'],
                fontSize=14, spaceAfter=8, spaceBefore=8,
                textColor=colors.HexColor('#2D3748')
            ),
            'MetricValue': ParagraphStyle(
                'MetricValue', parent=styles['Normal'],
                fontSize=20, spaceAfter=4, spaceBefore=4,
                textColor=colors.HexColor('#2D3748'), alignment=0
            ),
            'CustomBody': ParagraphStyle(
                'CustomBody', parent=styles['Normal'],
                fontSize=10, textColor=colors.HexColor('#4A5568')
            )
        }
        styles.update(custom_styles)
        return styles

    def _create_metrics_table(self, metrics: list, styles: dict) -> Table:
        """Create a formatted metrics table"""
        table = Table(metrics, colWidths=[200, 300])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2D3748')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ]))
        return table

    def convert_to_pdf(self, markdown_content: str = None) -> str:
        """Convert markdown report to PDF"""
        try:
            if markdown_content is None:
                with open('report.md', 'r', encoding='utf-8') as f:
                    markdown_content = f.read()

            domain = self.website_url.replace('https://', '').replace('http://', '')\
                                   .replace('www.', '').rstrip('/').replace('/', '_')
            pdf_filename = f"seo_report-{domain}.pdf"
            
            doc = SimpleDocTemplate(
                pdf_filename,
                pagesize=letter,
                rightMargin=40,
                leftMargin=40,
                topMargin=60,
                bottomMargin=40
            )
            
            styles = self._create_pdf_styles()
            story = []

            # Add header with logo
            logo_path = "src/image.png"
            if os.path.exists(logo_path):
                img = Image(logo_path)
                img.drawHeight = 50
                img.drawWidth = 50
                header = Table([
                    [Paragraph("SEO Analysis Report", styles['DashboardTitle']), img]
                ], colWidths=[450, 80])
                header.setStyle(TableStyle([
                    ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                story.append(header)
            
            # Add domain info and process content
            story.append(Paragraph(f"Domain: {self.website_url}", styles['SectionHeader']))
            story.append(Spacer(1, 20))

            # Process markdown sections
            self._process_markdown_sections(markdown_content, story, styles)

            # Generate PDF
            doc.build(story)
            print(f"PDF report generated successfully as '{pdf_filename}'")
            return pdf_filename
            
        except Exception as e:
            print(f"Error converting to PDF: {str(e)}")
            return None

    def _process_markdown_sections(self, content: str, story: list, styles: dict):
        """Process markdown content into PDF sections"""
        sections = content.split('\n\n')
        for section in sections:
            if not section.strip():
                continue
                
            lines = section.strip().split('\n')
            
            # Handle section headers
            if any(header in lines[0] for header in [
                'ANALYSIS REPORT FOR:',
                'SEO ANALYSIS REPORT FOR:',
                'OPTIMIZATION RECOMMENDATIONS FOR:'
            ]):
                story.append(Paragraph(lines[0], styles['SectionHeader']))
                story.append(Spacer(1, 10))
                continue
            
            # Process section content
            self._process_section_content(lines, story, styles)

    def _process_section_content(self, lines: list, story: list, styles: dict):
        """Process individual section content"""
        if lines[0].strip()[0].isdigit() and lines[0].strip()[1] == '.':
            story.append(Paragraph(lines[0].strip(), styles['SubsectionHeader']))
            story.append(Spacer(1, 8))
            metrics = self._extract_metrics(lines[1:])
            if metrics:
                story.append(self._create_metrics_table(metrics, styles))
                story.append(Spacer(1, 15))
        elif lines[0].strip() and not lines[0].strip().startswith('-'):
            story.append(Paragraph(lines[0].strip(), styles['SubsectionHeader']))
            story.append(Spacer(1, 8))
            metrics = self._extract_metrics(lines[1:])
            if metrics:
                story.append(self._create_metrics_table(metrics, styles))
                story.append(Spacer(1, 15))

    def _extract_metrics(self, lines: list) -> list:
        """Extract metrics from lines of text"""
        metrics = []
        for line in lines:
            if line.strip().startswith('- '):
                metric_line = line.strip('- ').strip()
                if ':' in metric_line:
                    label, value = metric_line.split(':', 1)
                    metrics.append([label.strip(), value.strip()])
        return metrics

    @crew
    def crew(self) -> Crew:
        """Creates and runs the SEO analysis crew"""
        crew_instance = Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
        result = crew_instance.kickoff()
        self.convert_to_pdf()
        return result

    async def run_analysis(self):
        """Runs the actual SEO analysis"""
        try:
            # Get crew instance and start analysis
            crew_instance = self.crew()
            result = crew_instance.kickoff()
            
            # Convert the result to PDF
            pdf_file = self.convert_to_pdf()
            
            return {
                'analysis_result': result,
                'pdf_report': pdf_file
            }
            
        except Exception as e:
            print(f"Error running analysis: {str(e)}")
            raise

    