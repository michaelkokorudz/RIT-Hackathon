import json
import time
import os
import matplotlib.pyplot as plt
from src.client import RITClient
from src.visualizer import MarketVisualizer
from src.tender import TenderAnalyzer

def load_settings():
    # Get the directory containing this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    settings_path = os.path.join(current_dir, 'settings.json')
        
    try:
        with open(settings_path) as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"settings.json not found at {settings_path}")

def main():
    settings = load_settings()
    client = RITClient(settings)
    visualizer = MarketVisualizer()
    analyzer = TenderAnalyzer()
    
    try:
        while True:
            securities = client.get_securities()
            abc_history = client.get_ticker_history('ABC')
            xyz_history = client.get_ticker_history('XYZ')
            tenders = client.get_tenders()
            
            analyzer.analyze_tenders(tenders, securities)
            
            if all([securities, abc_history, xyz_history]):
                visualizer.update(securities, abc_history, xyz_history)
                plt.pause(0.01)
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nStopping market data monitoring...")
        plt.close('all')
    except Exception as e:
        print(f"An error occurred: {e}")
        print(f"Type: {type(e)}")
        import traceback
        traceback.print_exc()
        plt.close('all')

if __name__ == "__main__":
    main()
