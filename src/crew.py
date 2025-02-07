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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from html.parser import HTMLParser
from tools.SubpageAnalyzer import SubpageAnalyzer
from tools.BrowserlessScraper import BrowserlessScraper
from concurrent.futures import ThreadPoolExecutor

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
    
    def convert_to_pdf(self):
        """
        Converts the markdown report to a professional PDF with analytics-style formatting
        """
        try:
            # Clean up domain name for filename
            domain = self.website_url.replace('https://', '').replace('http://', '').replace('www.', '')
            domain = domain.rstrip('/').replace('/', '_')
            pdf_filename = f"seo_report-{domain}.pdf"
            
            # Read markdown content
            with open('report.md', 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # Setup PDF document
            doc = SimpleDocTemplate(
                pdf_filename,
                pagesize=letter,
                rightMargin=40,
                leftMargin=40,
                topMargin=60,
                bottomMargin=40
            )
            
            # Define styles
            styles = getSampleStyleSheet()
            
            # Custom styles
            styles.add(ParagraphStyle(
                name='DashboardTitle',
                parent=styles['Title'],
                fontSize=28,
                spaceAfter=20,
                spaceBefore=10,
                textColor=colors.HexColor('#1A365D'),
                alignment=0
            ))
            
            styles.add(ParagraphStyle(
                name='SectionHeader',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=10,
                spaceBefore=10,
                textColor=colors.HexColor('#2C5282')
            ))
            
            # Add SubsectionHeader style
            styles.add(ParagraphStyle(
                name='SubsectionHeader',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=8,
                spaceBefore=8,
                textColor=colors.HexColor('#2D3748')
            ))
            
            styles.add(ParagraphStyle(
                name='MetricValue',
                parent=styles['Normal'],
                fontSize=20,
                spaceAfter=4,
                spaceBefore=4,
                textColor=colors.HexColor('#2D3748'),
                alignment=0
            ))
            
            styles.add(ParagraphStyle(
                name='CustomBody',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#4A5568')
            ))
            
            # Build document content
            story = []
            
            # Add header with logo
            logo_path = "image.png"
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
            
            # Add domain info
            story.append(Paragraph(f"Domain: {self.website_url}", styles['SectionHeader']))
            story.append(Spacer(1, 20))

            # Extract priority issues
            story.append(Paragraph("Priority Issues", styles['SectionHeader']))
            story.append(Spacer(1, 10))
            
            # Create priority issues table
            issues_data = []
            capture_issues = False
            for line in markdown_content.split('\n'):
                # Match both formats: "1. Priority Fixes:" and "Priority Fixes:"
                if "Priority Fixes:" in line:
                    capture_issues = True
                    continue
                # Match both indentation styles
                if capture_issues and (line.strip().startswith('- Issue') or line.strip().startswith('   - Issue')):
                    try:
                        # Remove any leading spaces and "- Issue X: "
                        line_content = line.strip().replace('- Issue ', '').split(':', 1)[1].strip()
                        
                        # Handle both formats:
                        # "Mobile Optimization [72.3%] -> [Target: 85%]"
                        # "Mobile Optimization - Current: 59.1% -> Target: 85%"
                        if ' - Current:' in line_content:
                            # Format: "Name - Current: X% -> Target: Y%"
                            name = line_content.split(' - Current:')[0].strip()
                            values = line_content.split(' - Current:')[1].strip()
                            current = values.split('->')[0].strip()
                            target = values.split('Target:')[1].strip()
                        else:
                            # Format: "Name [X%] -> [Target: Y%]"
                            name = line_content.split('[')[0].strip()
                            current = line_content.split('[')[1].split(']')[0].strip()
                            target = line_content.split('[Target:')[1].split(']')[0].strip()
                        
                        issues_data.append([name, current, target])
                        
                    except Exception as e:
                        print(f"Failed to parse priority issue line: {line}")
                        print(f"Error: {str(e)}")
                        continue
                elif capture_issues and line.strip().startswith('2.'):
                    break
                elif capture_issues and not line.strip():
                    break

            # Create and add the table if we have data
            if issues_data:
                table_data = [[
                    Paragraph("Issue", styles['SectionHeader']),
                    Paragraph("Current", styles['SectionHeader']),
                    Paragraph("Target", styles['SectionHeader'])
                ]]
                
                for issue in issues_data:
                    table_data.append([
                        Paragraph(issue[0], styles['CustomBody']),
                        Paragraph(issue[1], styles['CustomBody']),
                        Paragraph(issue[2], styles['CustomBody'])
                    ])
                
                # Create and style the table
                issues_table = Table(table_data, colWidths=[250, 125, 125])
                issues_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EDF2F7')),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (1, 1), (2, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('LEFTPADDING', (0, 0), (-1, -1), 15),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
                ]))
                story.append(issues_table)
                story.append(Spacer(1, 20))

            # Add Impact Forecast section
            story.append(Paragraph("Impact Forecast", styles['SectionHeader']))
            impact_data = []
            capture_impact = False
            for line in markdown_content.split('\n'):
                if "Impact Forecast:" in line:
                    capture_impact = True
                    continue
                if capture_impact and line.startswith('   - '):
                    impact_data.append(line.strip('   - '))
                elif capture_impact and not line.strip():
                    break

            if impact_data:
                impact_rows = [[
                    Paragraph("Metric", styles['SectionHeader']),
                    Paragraph("Expected Improvement", styles['SectionHeader'])
                ]]
                for impact in impact_data:
                    try:
                        metric, value = impact.split(':')
                        impact_rows.append([
                            Paragraph(metric.strip(), styles['CustomBody']),
                            Paragraph(value.strip(), styles['CustomBody'])
                        ])
                    except:
                        continue

                impact_table = Table(impact_rows, colWidths=[250, 250])
                impact_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EDF2F7')),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('TOPPADDING', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('LEFTPADDING', (0, 0), (-1, -1), 15),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
                ]))
                story.append(impact_table)
                story.append(Spacer(1, 20))

            # Add Key Statistics section
            story.append(Paragraph("Key Statistics", styles['SectionHeader']))
            
            # Parse key statistics
            main_stats = []
            word_stats = []
            subpage_stats = []
            capture_stats = False
            capture_subpages = False
            
            for line in markdown_content.split('\n'):
                if "Key Statistics:" in line:
                    capture_stats = True
                    continue
                if "Top Subpages:" in line:
                    capture_subpages = True
                    continue
                if capture_subpages and (line.strip().startswith('•') or line.strip().startswith('-')):
                    # Parse subpage line (e.g., "• /about-us: Engagement potential 80%")
                    subpage_line = line.strip('• -').strip()
                    try:
                        page, metric = subpage_line.split(':', 1)
                        subpage_stats.append([page.strip(), metric.strip()])
                    except:
                        print(f"Failed to parse subpage line: {line}")
                        continue
                elif capture_subpages and not line.strip():
                    capture_subpages = False
                    
                if capture_stats and line.startswith('   - '):
                    stat_line = line.strip('   - ')
                    if "Average Load Time" in stat_line:
                        main_stats.append(["Average Load Time", stat_line.split(': ')[1]])
                    elif "Most Used Meta Tags" in stat_line:
                        main_stats.append(["Most Used Meta Tags", stat_line.split(': ')[1]])
                    elif "Mobile Compatibility" in stat_line:
                        main_stats.append(["Mobile Compatibility", stat_line.split(': ')[1]])
                    elif "Most Frequent Words" in stat_line:
                        words = stat_line.split(': ')[1].split(', ')
                        for word in words:
                            word_parts = word.split(' (')
                            if len(word_parts) == 2:
                                word_stats.append([
                                    word_parts[0],
                                    word_parts[1].rstrip(')')
                                ])
                elif capture_stats and not line.strip():
                    capture_stats = False

            # Create main statistics table
            if main_stats:
                main_table_data = [[
                    Paragraph("Metric", styles['SectionHeader']),
                    Paragraph("Value", styles['SectionHeader'])
                ]]
                
                for stat in main_stats:
                    main_table_data.append([
                        Paragraph(stat[0], styles['CustomBody']),
                        Paragraph(stat[1], styles['CustomBody'])
                    ])
                
                main_stats_table = Table(main_table_data, colWidths=[200, 300])
                main_stats_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EDF2F7')),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('LEFTPADDING', (0, 0), (-1, -1), 15),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
                ]))
                story.append(main_stats_table)
                story.append(Spacer(1, 20))

            # Create word frequency table
            if word_stats:
                story.append(Paragraph("Most Frequent Words", styles['SectionHeader']))
                word_table_data = [[
                    Paragraph("Word", styles['SectionHeader']),
                    Paragraph("Frequency", styles['SectionHeader'])
                ]]
                
                for word in word_stats:
                    word_table_data.append([
                        Paragraph(word[0], styles['CustomBody']),
                        Paragraph(word[1], styles['CustomBody'])
                    ])
                
                word_stats_table = Table(word_table_data, colWidths=[200, 300])
                word_stats_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EDF2F7')),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (1, 1), (1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('LEFTPADDING', (0, 0), (-1, -1), 15),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
                ]))
                story.append(word_stats_table)
                story.append(Spacer(1, 20))

            # Create subpages table
            if subpage_stats:
                story.append(Paragraph("Top Subpages", styles['SectionHeader']))
                subpage_table_data = [[
                    Paragraph("Page", styles['SectionHeader']),
                    Paragraph("Metric", styles['SectionHeader'])
                ]]
                
                for subpage in subpage_stats:
                    subpage_table_data.append([
                        Paragraph(subpage[0], styles['CustomBody']),
                        Paragraph(subpage[1], styles['CustomBody'])
                    ])
                
                subpage_stats_table = Table(subpage_table_data, colWidths=[200, 300])
                subpage_stats_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EDF2F7')),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),     # Header font size
                    ('FONTSIZE', (0, 1), (-1, -1), 10),    # Content font size
                    ('TOPPADDING', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('LEFTPADDING', (0, 0), (-1, -1), 15),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
                ]))
                story.append(subpage_stats_table)
                story.append(Spacer(1, 20))

            # Add Page-Specific Optimizations section
            story.append(Paragraph("Page-Specific Optimizations", styles['SectionHeader']))
            
            # High-Priority Pages table
            high_priority_pages = []
            content_gaps = []
            structure_enhancements = []
            timeline = []
            
            capture_high_priority = False
            capture_content_gaps = False
            capture_structure = False
            capture_timeline = False
            current_page = None
            page_tasks = []
            
            for line in markdown_content.split('\n'):
                if "High-Priority Pages:" in line:
                    capture_high_priority = True
                    continue
                elif "Content Gaps:" in line:
                    capture_high_priority = False
                    capture_content_gaps = True
                    continue
                elif "Structure Enhancements:" in line:
                    capture_content_gaps = False
                    capture_structure = True
                    continue
                elif "Implementation Timeline:" in line:
                    capture_structure = False
                    capture_timeline = True
                    continue
                
                # Parse High-Priority Pages
                if capture_high_priority:
                    if line.strip().startswith('- /'):
                        if current_page and page_tasks:
                            high_priority_pages.append([current_page, '\n'.join(page_tasks)])
                            page_tasks = []
                        current_page = line.strip('- ').split(':')[0].strip()
                    elif line.strip().startswith('- ') and current_page:
                        task = line.strip('- ').strip()
                        if task:
                            page_tasks.append('• ' + task)
                
                # Parse Content Gaps
                elif capture_content_gaps and line.strip().startswith('- '):
                    content = line.strip('- ').strip()
                    if content:
                        content_gaps.append(content)
                
                # Parse Structure Enhancements
                elif capture_structure and line.strip().startswith('- '):
                    content = line.strip('- ').strip()
                    if content:
                        structure_enhancements.append(content)
                
                # Parse Timeline
                elif capture_timeline and line.strip().startswith('- '):
                    content = line.strip('- ').strip()
                    if content:
                        timeline.append(content)

            # Add final page if exists
            if current_page and page_tasks:
                high_priority_pages.append([current_page, '\n'.join(page_tasks)])

            # Create High-Priority Pages table
            if high_priority_pages:
                story.append(Paragraph("High-Priority Pages", styles['SectionHeader']))
                page_table_data = [[
                    Paragraph("Page", styles['SectionHeader']),
                    Paragraph("Optimizations", styles['SectionHeader'])
                ]]
                
                for page in high_priority_pages:
                    page_table_data.append([
                        Paragraph(page[0], styles['CustomBody']),
                        Paragraph(page[1], styles['CustomBody'])
                    ])
                
                page_table = Table(page_table_data, colWidths=[150, 350])
                page_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EDF2F7')),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('LEFTPADDING', (0, 0), (-1, -1), 15),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
                ]))
                story.append(page_table)
                story.append(Spacer(1, 20))

            # Create Content Gaps table
            if content_gaps:
                story.append(Paragraph("Content Gaps", styles['SectionHeader']))
                gaps_table_data = [[Paragraph("Identified Gaps and Improvements", styles['SectionHeader'])]]
                for gap in content_gaps:
                    gaps_table_data.append([Paragraph(gap, styles['CustomBody'])])
                
                gaps_table = Table(gaps_table_data, colWidths=[500])
                gaps_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EDF2F7')),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('LEFTPADDING', (0, 0), (-1, -1), 15),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
                ]))
                story.append(gaps_table)
                story.append(Spacer(1, 20))

            # Create Structure Enhancements table
            if structure_enhancements:
                story.append(Paragraph("Structure Enhancements", styles['SectionHeader']))
                structure_table_data = [[Paragraph("Recommended Improvements", styles['SectionHeader'])]]
                for enhancement in structure_enhancements:
                    structure_table_data.append([Paragraph(enhancement, styles['CustomBody'])])
                
                structure_table = Table(structure_table_data, colWidths=[500])
                structure_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EDF2F7')),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('LEFTPADDING', (0, 0), (-1, -1), 15),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
                ]))
                story.append(structure_table)
                story.append(Spacer(1, 20))

            # Create Implementation Timeline table
            if timeline:
                story.append(Paragraph("Implementation Timeline", styles['SectionHeader']))
                timeline_table_data = [[Paragraph("Timeline", styles['SectionHeader'])]]
                for step in timeline:
                    timeline_table_data.append([Paragraph(step, styles['CustomBody'])])
                
                timeline_table = Table(timeline_table_data, colWidths=[500])
                timeline_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EDF2F7')),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('LEFTPADDING', (0, 0), (-1, -1), 15),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
                ]))
                story.append(timeline_table)
                story.append(Spacer(1, 20))

            # Generate PDF
            doc.build(story)
            print(f"PDF report generated successfully as '{pdf_filename}'")
            
        except Exception as e:
            print(f"Error converting to PDF: {str(e)}")
            print(f"Error details: {str(e.__class__.__name__)}")
            print("The markdown file was still generated as 'report.md'")
