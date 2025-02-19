import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import json
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.conn_params = {
            'dbname': os.getenv('POSTGRES_DB', 'seo_analysis'),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
            'host': os.getenv('POSTGRES_HOST', 'postgres'),
            'port': os.getenv('POSTGRES_PORT', '5432')
        }

    @contextmanager
    def get_connection(self):
        conn = psycopg2.connect(**self.conn_params)
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def get_cursor(self):
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            try:
                yield cursor
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cursor.close()

    def create_job(self, website_url):
        with self.get_cursor() as cur:
            cur.execute(
                "INSERT INTO jobs (website_url) VALUES (%s) RETURNING id",
                (website_url,)
            )
            return cur.fetchone()['id']

    def update_job_status(self, job_id, status, error=None):
        """Update job status with timestamp"""
        with self.get_cursor() as cur:
            if status == 'started':
                cur.execute(
                    """
                    UPDATE jobs 
                    SET status = %s, started_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                    """,
                    (status, job_id)
                )
            elif status == 'completed':
                cur.execute(
                    """
                    UPDATE jobs 
                    SET status = %s, completed_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                    """,
                    (status, job_id)
                )
            elif status == 'error':
                cur.execute(
                    """
                    UPDATE jobs 
                    SET status = %s, error = %s 
                    WHERE id = %s
                    """,
                    (status, error, job_id)
                )

    def store_results(self, job_id: int, results: dict):
        """Store analysis results in the database"""
        try:
            with self.get_cursor() as cur:
                # Ensure recommendations is a JSON string
                if isinstance(results.get('recommendations'), dict):
                    results['recommendations'] = json.dumps(results['recommendations'])
                
                cur.execute("""
                    INSERT INTO results (
                        job_id, recommendations
                    ) VALUES (%s, %s)
                """, (
                    job_id,
                    results.get('recommendations')
                ))
                
                # Update job status to completed
                self.update_job_status(job_id, 'completed')
                
        except Exception as e:
            logger.error(f"Error storing results for job {job_id}: {str(e)}")
            raise

    def get_job_status(self, job_id):
        with self.get_cursor() as cur:
            cur.execute(
                "SELECT * FROM jobs WHERE id = %s",
                (job_id,)
            )
            return cur.fetchone()

    def get_job_results(self, job_id):
        with self.get_cursor() as cur:
            cur.execute(
                "SELECT * FROM results WHERE job_id = %s",
                (job_id,)
            )
            return cur.fetchone() 