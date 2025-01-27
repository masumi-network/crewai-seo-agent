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



load_dotenv()

@CrewBase
class SEOAnalyseCrew():
	"""SEOAnalyseCrew"""

	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	def __init__(self, website_url: str):
		self.website_url = website_url
		# Load configuration files
		with open(self.agents_config, 'r') as f:
			self.agents_config = yaml.safe_load(f)
		with open(self.tasks_config, 'r') as f:
			self.tasks_config = yaml.safe_load(f)

	# Configure OpenAI LLM
	openai_llm = LLM(
		model='gpt-4',  
		api_key=os.getenv('OPENAI_API_KEY'),  
	)

	@agent
	def scraper_agent(self) -> Agent:		
		return Agent(
			config=self.agents_config['scraper_agent'],
			tools=[
				SeleniumScraper(),
				LoadingTimeTracker(),
				MobileOptimizationTool(),
			],
			verbose=True,
			llm=self.openai_llm  
		)

	@agent
	def analyse_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['analyse_agent'],
			verbose=True,
			llm=self.openai_llm  
		)
	
	@agent
	def optimization_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['optimization_agent'],
			verbose=True,
			llm=self.openai_llm  
		)


	@task
	def data_collection_task(self) -> Task:
		task_config = self.tasks_config['data_collection_task']
		return Task(
			description=task_config['description'].format(website_url=self.website_url),
			agent=self.scraper_agent(),
			expected_output=task_config['expected_output'],
		)

	@task
	def analysis_task(self) -> Task:
		task_config = self.tasks_config['analysis_task']
		return Task(
			description=task_config['description'].format(website_url=self.website_url),
			agent=self.analyse_agent(),
			expected_output=task_config['expected_output'],
			output_file='report.md'
		)

	@task
	def optimization_task(self) -> Task:
		task_config = self.tasks_config['optimization_task']
		return Task(
			description=task_config['description'],
			agent=self.optimization_agent(),
			expected_output=task_config['expected_output'],
			output_file='report.md'
		)

	@crew
	def crew(self) -> Crew:
		"""Creates the SEOAnalyseCrew"""
		return Crew(
			agents=self.agents, 
			tasks=self.tasks, 
			process=Process.sequential,
			verbose=True,
		)
