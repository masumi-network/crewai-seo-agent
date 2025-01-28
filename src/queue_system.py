# This file implements a job queue system for handling SEO analysis requests asynchronously

from typing import Dict, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel
import asyncio
import uuid
from crew import SEOAnalyseCrew

# Enum defining possible job statuses
class JobStatus(str, Enum):
    PENDING = "pending"      # Job is queued but not started
    PROCESSING = "processing"  # Job is currently being processed
    COMPLETED = "completed"    # Job finished successfully
    FAILED = "failed"         # Job encountered an error

# Pydantic model defining the structure of a job
class Job(BaseModel):
    job_id: str                    # Unique identifier for the job
    status: JobStatus              # Current status of the job
    created_at: datetime           # When the job was created
    input_data: str                # The website URL to analyze
    result: Optional[Dict] = None  # Results of the analysis (if completed)
    error: Optional[str] = None    # Error message (if failed)

# Main queue system class that manages jobs
class QueueSystem:
    def __init__(self):
        self.jobs: Dict[str, Job] = {}  # Store all jobs by ID
        self.queue = asyncio.Queue()     # Async queue for job processing
        self._start_time = datetime.utcnow()  # Track system uptime

    async def start_job(self, input_data: str) -> str:
        """
        Creates a new job and adds it to the processing queue
        Args:
            input_data: Website URL to analyze
        Returns:
            job_id: Unique identifier for tracking the job
        """
        job_id = str(uuid.uuid4())
        
        job = Job(
            job_id=job_id,
            status=JobStatus.PENDING,
            created_at=datetime.utcnow(),
            input_data=input_data
        )
        
        self.jobs[job_id] = job
        await self.queue.put(job_id)
        
        return job_id

    def get_job_status(self, job_id: str) -> Optional[Job]:
        """
        Retrieves the current status and results of a specific job
        Args:
            job_id: ID of the job to look up
        Returns:
            Job object if found, None otherwise
        """
        return self.jobs.get(job_id)

    def get_availability(self) -> Dict:
        """
        Returns system status information including uptime
        Returns:
            Dict containing status, uptime and availability message
        """
        uptime = (datetime.utcnow() - self._start_time).seconds
        return {
            "status": "available",
            "uptime": uptime,
            "message": "SEO Analysis Agent is operational"
        }

    async def process_jobs(self):
        """
        Main processing loop that:
        1. Gets jobs from the queue
        2. Updates job status to processing
        3. Runs the SEO analysis
        4. Updates job with results or error
        5. Marks job as completed/failed
        """
        while True:
            try:
                # Get next job from queue
                job_id = await self.queue.get()
                job = self.jobs[job_id]
                
                # Mark as processing
                job.status = JobStatus.PROCESSING
                
                try:
                    # Run SEO analysis
                    crew = SEOAnalyseCrew(website_url=job.input_data)
                    result = crew.crew().kickoff()
                    
                    # Store results and mark as complete
                    job.result = result
                    job.status = JobStatus.COMPLETED
                    
                except Exception as e:
                    # Handle errors by marking job as failed
                    job.status = JobStatus.FAILED
                    job.error = str(e)
                
                finally:
                    self.queue.task_done()
                    
            except Exception as e:
                print(f"Error in job processing loop: {e}")
                await asyncio.sleep(1)  # Prevent tight loop on errors