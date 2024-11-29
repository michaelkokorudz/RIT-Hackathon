import requests

class RITClient:
    def __init__(self, settings):
        self.api_key = settings['API_KEY']
        self.user = settings['USER']
        self.password = settings['PASSWORD']
        self.base_url = settings['URL']
        self.api_version = settings["VERSION"]

        self.headers = {
            'X-API-Key': self.api_key,
            'Authorization': f"Basic {self.user}:{self.password}"
        }
        
    def _make_request(self, endpoint, params=None):
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.get(
                url, 
                headers=self.headers,
                params=params,
                timeout=5,
                auth=(self.user, self.password)
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Request failed: {e}")
            return None

    def get_securities(self):
        return self._make_request(f"/{self.api_version}/securities")
    
    def get_positions(self):
        return self._make_request(f"/{self.api_version}/positions")
    
    def get_ticker_history(self, ticker):
        return self._make_request(f"/{self.api_version}/securities/history", params={'ticker': ticker})
        
    def get_tenders(self):
        return self._make_request(f"/{self.api_version}/tenders")