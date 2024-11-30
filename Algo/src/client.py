from enum import Enum
from typing import Optional, Dict, Any, List
import requests
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import base64

class OrderType(Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"

class OrderAction(Enum):
    BUY = "BUY"
    SELL = "SELL"

class RITClient:
    def __init__(self, settings: Dict[str, str]):
        self.api_key = settings['API_KEY']
        self.base_url = f"{settings['URL']}:{settings['PORT']}"
        self.api_version = settings['VERSION']
        
        auth_str = f"Basic {settings['USER']}:{settings['PASSWORD']}"
        auth_bytes = auth_str.encode('ascii')
        base64_auth = base64.b64encode(auth_bytes).decode('ascii')
        
        print(f"Initializing RIT Client:")
        print(f"- Base URL: {self.base_url}")
        print(f"- API Version: {self.api_version}")
        print(f"- User: {settings['USER']}")
        
        self.headers = {
            'X-API-Key': self.api_key,
            'Authorization': f'Basic {base64_auth}'
        }
        
        self._test_connection()

    def _test_connection(self):
        """Test API connection and print status"""
        try:
            response = requests.get(
                f"{self.base_url}/{self.api_version}/case",
                headers=self.headers,
                timeout=5
            )
            if response.ok:
                case_info = response.json()
                print("Successfully connected to RIT API")
                print(f"Case: {case_info.get('name', 'Unknown')}")
                print(f"Period: {case_info.get('period', 0)}/{case_info.get('total_periods', 0)}")
            else:
                print(f"Warning: Could not get case information. Status: {response.status_code}")
        except Exception as e:
            print(f"Warning: Connection test failed - {str(e)}")

    def _make_request(self, endpoint: str, method: str = "GET", params: Dict = None, json: Dict = None) -> Optional[Dict]:
        """Make a request to the RIT API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        if not endpoint.startswith(self.api_version):
            url = f"{self.base_url}/{self.api_version}/{endpoint.lstrip('/')}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers, params=params, timeout=5)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=json, timeout=5)
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers, timeout=5)
            
            response.raise_for_status()
            return response.json() if response.content else None
                
        except Exception as e:
            print(f"API request failed ({method} {endpoint}): {str(e)}")
            return None

    def get_securities(self) -> Optional[List[Dict[str, Any]]]:
        """Get all securities information"""
        return self._make_request("securities")
    
    def submit_order(
        self,
        ticker: str,
        type: OrderType,
        quantity: int,
        action: OrderAction,
        price: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """Submit a new order"""
        if quantity <= 0:
            print("Invalid quantity: must be positive")
            return None
        
        payload = {
            "ticker": ticker,
            "type": type.value,
            "quantity": int(quantity),
            "action": action.value,
            "price": round(price, 2) if price else None
        }
        
        payload = {k: v for k, v in payload.items() if v is not None}
        
        return self._make_request("orders", method="POST", json=payload)

    def cancel_all_orders(self) -> Optional[Dict[str, Any]]:
        """Cancel all existing orders"""
        return self._make_request("orders", method="DELETE")