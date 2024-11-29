import json
import time
import matplotlib.pyplot as plt
from src.client import RITClient
from src.visualizer import MarketVisualizer

def load_settings():
    with open('settings.json') as f:
        return json.load(f)

def main():
    settings = load_settings()
    client = RITClient(settings)
    visualizer = MarketVisualizer()
    
    try:
        while True:
            securities = client.get_securities()
            abc_history = client.get_ticker_history('ABC')
            xyz_history = client.get_ticker_history('XYZ')
            
            if all([securities, abc_history, xyz_history]):
                visualizer.update(securities, abc_history, xyz_history)
                plt.pause(0.01)
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nStopping market data monitoring...")
        plt.close('all')
    except Exception as e:
        print(f"An error occurred: {e}")
        plt.close('all')

if __name__ == "__main__":
    main()
