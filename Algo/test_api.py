import json
import os
import time
from datetime import datetime
from src.client import RITClient, OrderType, OrderAction

class APITester:
    def __init__(self):
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.settings = self._load_settings()
        self.client = RITClient(self.settings)
        self.output_dir = os.path.join(self.current_dir, 'test_output')
        os.makedirs(self.output_dir, exist_ok=True)
        
    def _load_settings(self):
        settings_path = os.path.join(self.current_dir, 'settings.json')
        try:
            with open(settings_path) as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"settings.json not found at {settings_path}")

    def _save_data(self, data, filename):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = os.path.join(self.output_dir, f"{filename}_{timestamp}.json")
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
        return filepath

    def test_securities(self, duration=10):
        """Test securities endpoint for a specified duration"""
        print(f"\nTesting securities endpoint for {duration} seconds...")
        securities_data = []
        
        start_time = time.time()
        while time.time() - start_time < duration:
            try:
                securities = self.client.get_securities()
                if securities:
                    securities_data.append({
                        'timestamp': datetime.now().isoformat(),
                        'data': securities
                    })
                    print(f"Retrieved data for {len(securities)} securities")
                time.sleep(1)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
        
        # Save collected data
        if securities_data:
            filepath = self._save_data(securities_data, 'securities_test')
            print(f"Securities data saved to: {filepath}")

    def test_order_submission(self):
        """Test order submission functionality"""
        print("\nTesting order submission...")
        try:
            # Get available securities first
            securities = self.client.get_securities()
            if not securities:
                print("No securities available for testing orders")
                return
            
            # Test with first available security
            security = securities[0]
            ticker = security['ticker']
            
            print(f"Testing orders for {ticker}")
            
            # Test limit order
            limit_price = float(security.get('bid', 0)) - 0.10  # More conservative pricing
            print(f"Submitting limit order at {limit_price}")
            
            # Add more debug info
            print(f"Security details: {json.dumps(security, indent=2)}")
            
            limit_order = self.client.submit_order(
                ticker=ticker,
                type=OrderType.LIMIT,
                quantity=100,
                action=OrderAction.BUY,
                price=limit_price
            )
            
            if limit_order:
                
                print(f"Successfully submitted limit order: {limit_order}")
                self._save_data(limit_order, 'limit_order_test')
                
                # Wait a moment before canceling
                time.sleep(1)
                
                # Cancel all orders
                cancel_result = self.client.cancel_all_orders()
                if cancel_result:
                    print("Successfully cancelled all orders")
                    self._save_data(cancel_result, 'cancel_orders_test')
                else:
                    print("Failed to cancel orders")
            else:
                print("Failed to submit limit order")
                print("Checking API status...")
                api_info = self.client._make_request("api/info")
                if api_info:
                    print("API is accessible. Available endpoints:")
                    print(json.dumps(api_info, indent=2))
                
        except Exception as e:
            print(f"Order submission test failed: {e}")
            print("Attempting to get API status...")
            try:
                api_info = self.client._make_request("api/info")
                if api_info:
                    print("API is still accessible")
            except Exception as inner_e:
                print(f"Could not get API status: {inner_e}")

    def test_case_info(self):
        """Test case information endpoint"""
        print("\nTesting case information...")
        try:
            response = self.client._make_request("case")
            if response:
                print("Case Information:")
                print(json.dumps(response, indent=2))
            else:
                print("Failed to get case information")
        except Exception as e:
            print(f"Case information test failed: {e}")

    def test_api_info(self):
        """Test API information endpoint to see available methods"""
        print("\nTesting API information...")
        try:
            response = self.client._make_request("api/info")
            if response:
                print("Available API Methods:")
                print(json.dumps(response, indent=2))
            else:
                print("Failed to get API information")
        except Exception as e:
            print(f"API information test failed: {e}")

def main():
    tester = APITester()
    
    # Test API information first
    try:
        tester.test_api_info()
    except Exception as e:
        print(f"API info test failed but continuing: {e}")

    # Skip securities test
    # tester.test_securities(duration=10)
    
    # Test order submission with better error handling
    try:
        print("\nAttempting order submission with debug info...")
        tester.test_order_submission()
    except Exception as e:
        print(f"Order submission test failed: {e}")
        print("Response headers and status code would be helpful here")

if __name__ == "__main__":
    main()