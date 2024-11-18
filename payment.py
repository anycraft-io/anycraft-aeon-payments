from enum import Enum
import hashlib
import json
import requests
import logging
from typing import Dict, Optional, Any
import time
from config import APP_ID, SECRET_KEY, BASE_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrderStatus(Enum):
    """Payment order status enumeration"""
    INIT = "INIT"  # Initial state
    PROCESSING = "PROCESSING"  # Payment in progress
    COMPLETED = "COMPLETED"  # Payment successful
    CLOSE = "CLOSE"  # Order closed
    TIMEOUT = "TIMEOUT"  # Payment timeout
    FAILED = "FAILED"  # Payment failed
    DELAY_SUCCESS = "DELAY_SUCCESS"  # Success after delay
    DELAY_FAILED = "DELAY_FAILED"  # Failure after delay

class PaymentAPI:
    """API wrapper for AEON payment system"""
    def __init__(self):
        self.APP_ID = APP_ID
        self.SECRET_KEY = SECRET_KEY
        self.BASE_URL = BASE_URL
        self.HEADERS = {"Content-Type": "application/json"}

    def generate_sign(self, params: Dict[str, Any]) -> str:
        """Generate signature for API request parameters"""
        # Filter and convert parameters
        filtered_params = {
            k: str(v) for k, v in params.items() 
            if k != 'sign' and v is not None
        }
        
        # Sort and join parameters
        sorted_keys = sorted(filtered_params.keys())
        param_string = '&'.join(
            f"{key}={filtered_params[key]}" 
            for key in sorted_keys
        )
        
        # Add secret key and generate hash
        string_to_sign = f"{param_string}&key={self.SECRET_KEY}"
        logger.debug(f"String to sign: {string_to_sign}")
        
        return hashlib.sha512(string_to_sign.encode()).hexdigest().upper()

    async def create_payment(self, amount: float, user_id: int, order_id: str, custom_data: Dict = None) -> Dict:
        """Create new payment order"""
        request_params = {
            "appId": self.APP_ID,
            "merchantOrderNo": order_id,
            "orderAmount": str(amount),
            "payCurrency": "USD",
            "userId": str(user_id),
            "paymentTokens": "USDT",
            "paymentExchange": "16f021b0-f220-4bbb-aa3b-82d423301957"
        }
        
        # Generate signature before adding customParam
        request_params["sign"] = self.generate_sign(request_params)
        
        # Add custom data with timestamp
        if custom_data:
            custom_data["orderTs"] = str(int(time.time() * 1000))
            request_params["customParam"] = json.dumps(custom_data)
        
        try:
            url = f"{self.BASE_URL}/open/api/payment"
            response = requests.post(url, json=request_params, headers=self.HEADERS)
            
            logger.debug(f"Request params: {json.dumps(request_params, indent=2)}")
            logger.debug(f"Response: {response.text}")
            
            return response.json()
        except Exception as e:
            logger.error(f"Payment error: {str(e)}")
            return {
                "error": True,
                "msg": str(e),
                "code": "ERROR"
            }

    async def fetch_order(self, merchant_order_no: str) -> Optional[Dict]:
        """Query order status"""
        request_params = {
            "appId": self.APP_ID,
            "merchantOrderNo": merchant_order_no
        }
        
        request_params["sign"] = self.generate_sign(request_params)
        
        try:
            url = f"{self.BASE_URL}/open/api/payment/query"
            response = requests.post(url, json=request_params, headers=self.HEADERS)
            logger.debug(f"Query response: {response.text}")
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching order: {str(e)}")
            return None

    async def validate_payment(self, order_id: str) -> bool:
        """Validate payment status"""
        request_params = {
            "appId": self.APP_ID,
            "merchantOrderNo": order_id,
        }
        
        request_params["sign"] = self.generate_sign(request_params)

        try:
            url = f"{self.BASE_URL}/open/api/payment/validate"
            response = requests.post(url, json=request_params, headers=self.HEADERS)
            result = response.json()
            return result.get("code") == "0" and result.get("model", {}).get("status") == "SUCCESS"
        except Exception as e:
            logger.error(f"Payment validation error: {str(e)}")
            return False

    async def refund_payment(self, order_id: str, amount: float) -> bool:
        """Request payment refund"""
        request_params = {
            "appId": self.APP_ID,
            "merchantOrderNo": order_id,
            "refundAmount": str(amount)
        }
        
        request_params["sign"] = self.generate_sign(request_params)

        try:
            url = f"{self.BASE_URL}/open/api/refund/apply"
            response = requests.post(url, json=request_params, headers=self.HEADERS)
            result = response.json()
            return result.get("code") == "0"
        except Exception as e:
            logger.error(f"Refund error: {str(e)}")
            return False
