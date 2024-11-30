import json
import time
import os
from src.client import RITClient
from src.tender import evaluate_tender
from src.volatility import calculate_volatility
from src.close_out_utils import calculate_liquidity
from src.visualizer import MarketVisualizer


def load_settings():
    print("Loading settings...")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    settings_path = os.path.join(current_dir, 'settings.json')

    try:
        with open(settings_path) as f:
            print("Settings loaded successfully.")
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"settings.json not found at {settings_path}")


def main():
    """
    Main function to monitor and evaluate tender offers in the market.
    """
    print("Starting script...")
    settings = load_settings()
    client = RITClient(settings)
    visualizer = MarketVisualizer()

    # Configuration for evaluating tenders
    config = {
        "min_time_to_close": 20,           # Minimum time to close a position
        "max_price_gap": 0.05,             # Maximum acceptable price gap
        "liquidity_to_tender_ratio": 0.2   # Minimum liquidity ratio
    }

    try:
        while True:
            print("Fetching case status...")
            try:
                case_status = client.get_case_status()
                if not case_status:
                    print("Unable to retrieve case status. Retrying...")
                    time.sleep(1)
                    continue
            except Exception as e:
                print(f"Error fetching case status: {e}")
                time.sleep(1)
                continue

            session_status = case_status.get("status")
            current_tick = case_status.get("tick", 0)
            ticks_per_period = case_status.get("ticks_per_period", 600)
            total_periods = case_status.get("total_periods", 1)

            print(f"Session Status: {session_status}, Tick: {current_tick}")

            if session_status in ["RUNNING", "ACTIVE"]:
                print(f"Simulation Progress: Tick {current_tick} out of {ticks_per_period} in Period 1 of {total_periods}")

                try:
                    securities = client.get_securities()
                    if not securities:
                        raise ValueError("Securities data is empty or None.")
                    print("Securities fetched successfully.")
                except Exception as e:
                    print(f"Error fetching securities: {e}")
                    time.sleep(1)
                    continue

                try:
                    tenders = client.get_tenders()
                    if tenders is None:
                        raise ValueError("Tenders data is None.")
                    print(f"Tenders fetched: {len(tenders)} active offers.")
                except Exception as e:
                    print(f"Error fetching tenders: {e}")
                    time.sleep(1)
                    continue

                # Update the market visualizer
                visualizer.update(securities, tenders, current_tick)

                if not tenders:
                    print("No active tender offers. Skipping processing.")
                    time.sleep(1)
                    continue

                for tender in tenders:
                    ticker = tender["ticker"]
                    try:
                        order_book = client.get_order_book(ticker)
                        liquidity = calculate_liquidity(order_book, action=tender["action"])

                        # Ensure that securities contain data for the ticker
                        security_data = next((s for s in securities if s["ticker"] == ticker), None)
                        if not security_data:
                            raise ValueError(f"No securities data found for ticker {ticker}.")

                        market_data = {
                            "bid": security_data["bid"],
                            "ask": security_data["ask"],
                            "last": security_data["last"],
                            "volatility": calculate_volatility(
                                ticker=ticker,
                                prices=[security_data["last"]],
                                liquidity=liquidity,
                                elapsed_time=current_tick,
                                current_tender_size=tender["quantity"],
                            ),
                            "liquidity": liquidity,
                            "order_book": order_book,
                        }

                        print(f"Market data for {ticker}: {market_data}")

                        # Analyze this single tender
                        result = evaluate_tender(tender, market_data, ticks_per_period - current_tick, config)
                        print(f"Tender Analysis Result: {result}")

                        if result["decision"] == "ACCEPT":
                            print(f"Accepting tender: {tender}")
                            # Call API to accept tender if required
                            # client.accept_tender(tender["tender_id"])
                    except Exception as e:
                        print(f"Error processing tender {tender.get('tender_id')} for {ticker}: {e}")

            elif session_status == "PAUSED":
                print("Session is PAUSED. Waiting...")
                time.sleep(2)

            elif session_status == "ENDED":
                print("Session has ENDED. Resetting visualizer and waiting for new simulation...")
                visualizer.reset()

                # Wait for a new simulation to start
                while session_status == "ENDED":
                    time.sleep(2)
                    try:
                        case_status = client.get_case_status()
                        session_status = case_status.get("status")
                        current_tick = case_status.get("tick", 0)
                        print(f"Waiting... Session Status: {session_status}, Tick: {current_tick}")
                    except Exception as e:
                        print(f"Error fetching case status: {e}")
                        time.sleep(1)
                        continue

                print("New simulation detected. Reinitializing visualizer.")
                # Reinitialize the visualizer for the new simulation
                visualizer.reset()

            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping market data monitoring...")
        visualizer.reset()
    except Exception as e:
        print(f"An error occurred: {e}")
        visualizer.reset()


if __name__ == "__main__":
    print("Running main()...")
    main()
