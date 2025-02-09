import os
import requests
from typing import Dict, Optional

class MasumiPaymentHandler:
    def __init__(self):
        self.payment_service_url = os.getenv('PAYMENT_SERVICE_URL')
        self.payment_api_key = os.getenv('PAYMENT_API_KEY')
        
    def create_payment_request(self, amount: float, job_id: str) -> Dict:
        """Create a payment request for an SEO analysis job"""
        try:
            response = requests.post(
                f"{self.payment_service_url}/create_payment",
                headers={"Authorization": f"Bearer {self.payment_api_key}"},
                json={
                    "amount": amount,
                    "job_id": job_id,
                    "service_type": "seo_analysis"
                }
            )
            return response.json()
        except Exception as e:
            print(f"Error creating payment request: {str(e)}")
            raise

    def check_payment_status(self, payment_id: str) -> Dict:
        """Check the status of a payment"""
        try:
            response = requests.get(
                f"{self.payment_service_url}/status/{payment_id}",
                headers={"Authorization": f"Bearer {self.payment_api_key}"}
            )
            return response.json()
        except Exception as e:
            print(f"Error checking payment status: {str(e)}")
            raise 