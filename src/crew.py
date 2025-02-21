# src/crew.py
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv
import openai
import os
import yaml
from .tools.LoadingTimeTracker import LoadingTimeTracker
from .tools.MobileTesting import MobileOptimizationTool
from .tools.SubpageAnalyzer import SubpageAnalyzer
from .tools.BrowserlessScraper import BrowserlessScraper
import asyncio
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

load_dotenv()

@CrewBase
class SEOAnalyseCrew():
    """
    Main class that orchestrates the SEO analysis process using multiple AI agents.
    It handles data collection, analysis, and optimization recommendations.
    """
    agents_config = os.path.join(os.path.dirname(__file__), 'config', 'agents.yaml')
    tasks_config = os.path.join(os.path.dirname(__file__), 'config', 'tasks.yaml')

    def __init__(self, website_url: str):
        """Initialize with target website URL and load config files"""
        self.website_url = website_url
        logger.info(f"Initializing SEO Analysis Crew for {website_url}")
        
        with open(self.agents_config, 'r') as f:
            self.agents_config = yaml.safe_load(f)
        with open(self.tasks_config, 'r') as f:
            self.tasks_config = yaml.safe_load(f)
            
        self.tools = [
            BrowserlessScraper(),
            LoadingTimeTracker(),
            MobileOptimizationTool(),
            SubpageAnalyzer()
        ]
        logger.info("Tools initialized successfully")
        
        self.agents = {
            'scraper_agent': self.scraper_agent(),
            'analyse_agent': self.analyse_agent(),
            'optimization_agent': self.optimization_agent()
        }
        logger.info("Agents initialized successfully")
        
        self.tool_timeout = 60
        super().__init__()

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
            tools=self.tools,
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

    async def run(self) -> Dict[str, Any]:
        """Run the SEO analysis crew and return results as JSON"""
        try:
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
            
            crew_output = crew.kickoff()
            return self._process_results(crew_output)
            
        except Exception as e:
            logger.error(f"Crew run error: {str(e)}")
            return {"error": str(e)}

    def _process_results(self, results) -> Dict[str, Any]:
        """Process crew output into structured JSON format"""
        structured_results = {
            "meta_tags": {},
            "headings": {},
            "keywords": {},
            "links": {},
            "images": {},
            "content_stats": {},
            "mobile_stats": {},
            "performance_stats": {},
            "recommendations": {}
        }

        try:
            if hasattr(results, 'tasks_output'):
                for task_output in results.tasks_output:
                    output = str(task_output)
                    if "Meta Tags Analysis" in output:
                        structured_results["meta_tags"] = self._extract_meta_info(output)
                    elif "Content Analysis" in output:
                        structured_results["keywords"] = self._extract_keyword_info(output)
                    elif "Content Structure" in output:
                        structured_results["headings"] = self._extract_heading_info(output)
                    elif "Link Analysis" in output:
                        structured_results["links"] = self._extract_link_info(output)
                    elif "Media Inventory" in output:
                        structured_results["images"] = self._extract_image_info(output)
                    elif "Performance Metrics" in output:
                        structured_results["performance_stats"] = self._extract_performance_info(output)
                    elif "Mobile Optimization" in output:
                        structured_results["mobile_stats"] = self._extract_mobile_info(output)
                    elif "OPTIMIZATION RECOMMENDATIONS" in output:
                        structured_results["recommendations"] = self._extract_recommendations(output)
            return structured_results
        except Exception as e:
            logger.error(f"Error processing results: {str(e)}")
            return {"error": str(e)}

    def _extract_meta_info(self, text: str) -> Dict:
        meta_info = {"total_tags": 0, "tags": {}}
        lines = text.split('\n')
        for line in lines:
            if "Total number of meta tags:" in line:
                meta_info["total_tags"] = int(line.split(':')[1].strip())
            elif "*" in line and ":" in line:
                tag, count = line.split(':')
                meta_info["tags"][tag.strip("* ")] = int(count.split()[0])
        return meta_info

    def _extract_keyword_info(self, text: str) -> Dict:
        keyword_info = {"frequent_words": {}, "density": {}, "total_words": 0}
        lines = text.split('\n')
        for line in lines:
            if "Total word count:" in line:
                keyword_info["total_words"] = int(line.split(':')[1].strip())
            elif "*" in line and ":" in line:
                parts = line.split(':')
                word = parts[0].strip("* ")
                count_part = parts[1].strip()
                count = int(count_part.split()[0])
                keyword_info["frequent_words"][word] = count
                # Placeholder for density calculation if needed
        return keyword_info

    def _extract_heading_info(self, text: str) -> Dict:
        heading_info = {"h1": 0, "h2": 0, "h3": 0, "h4_h6": 0}
        lines = text.split('\n')
        for line in lines:
            if "H1 tags:" in line:
                heading_info["h1"] = int(line.split(':')[1].strip())
            elif "H2 tags:" in line:
                heading_info["h2"] = int(line.split(':')[1].strip())
            elif "H3 tags:" in line:
                heading_info["h3"] = int(line.split(':')[1].strip())
            elif "H4-H6 tags:" in line:
                heading_info["h4_h6"] = int(line.split(':')[1].strip())
        return heading_info

    def _extract_link_info(self, text: str) -> Dict:
        link_info = {"internal": 0, "external": 0, "broken": 0}
        lines = text.split('\n')
        for line in lines:
            if "Internal links:" in line:
                link_info["internal"] = int(line.split(':')[1].strip())
            elif "External links:" in line:
                link_info["external"] = int(line.split(':')[1].strip())
            elif "Broken links found:" in line:
                link_info["broken"] = int(line.split(':')[1].strip())
        return link_info

    def _extract_image_info(self, text: str) -> Dict:
        image_info = {"total_images": 0, "with_alt": 0, "without_alt": 0}
        lines = text.split('\n')
        for line in lines:
            if "Total images:" in line:
                image_info["total_images"] = int(line.split(':')[1].strip())
            elif "Images with alt text:" in line:
                image_info["with_alt"] = int(line.split(':')[1].strip())
            elif "Images without alt text:" in line:
                image_info["without_alt"] = int(line.split(':')[1].strip())
        return image_info

    def _extract_performance_info(self, text: str) -> Dict:
        performance_info = {"avg_load_time": 0.0, "fastest_load": 0.0, "slowest_load": 0.0}
        lines = text.split('\n')
        for line in lines:
            if "Average load time:" in line:
                performance_info["avg_load_time"] = float(line.split(':')[1].strip().split()[0])
            elif "Fastest load:" in line:
                performance_info["fastest_load"] = float(line.split(':')[1].strip().split()[0])
            elif "Slowest load:" in line:
                performance_info["slowest_load"] = float(line.split(':')[1].strip().split()[0])
        return performance_info

    def _extract_mobile_info(self, text: str) -> Dict:
        mobile_info = {"viewport": "No", "text_readability": 0, "tap_target_spacing": 0}
        lines = text.split('\n')
        for line in lines:
            if "Viewport Meta Tag:" in line:
                mobile_info["viewport"] = line.split(':')[1].strip()
            elif "Text Readability Score:" in line:
                mobile_info["text_readability"] = float(line.split(':')[1].strip().rstrip('%'))
            elif "Tap Target Spacing Score:" in line:
                mobile_info["tap_target_spacing"] = float(line.split(':')[1].strip().rstrip('%'))
        return mobile_info

    def _extract_recommendations(self, text: str) -> Dict:
        recommendations = {
            "priority_fixes": [],
            "impact_forecast": {},
            "key_statistics": {},
            "page_specific": []
        }
        lines = text.split('\n')
        current_section = None
        for line in lines:
            line = line.strip()
            if "Priority Fixes:" in line:
                current_section = "priority_fixes"
            elif "Impact Forecast:" in line:
                current_section = "impact_forecast"
            elif "Key Statistics:" in line:
                current_section = "key_statistics"
            elif "Page-Specific Optimizations:" in line:
                current_section = "page_specific"
            elif line and current_section:
                if current_section == "priority_fixes" and "->" in line:
                    issue, target = line.split("->")
                    recommendations["priority_fixes"].append({
                        "issue": issue.strip(),
                        "target": target.strip()
                    })
                elif current_section == "impact_forecast" and ":" in line:
                    key, value = line.split(":")
                    recommendations["impact_forecast"][key.strip()] = value.strip()
                elif current_section == "key_statistics" and ":" in line:
                    key, value = line.split(":")
                    recommendations["key_statistics"][key.strip()] = value.strip()
                elif current_section == "page_specific" and line.startswith("- ["):
                    recommendations["page_specific"].append(line.strip("- "))
        return recommendations