class TenderAnalyzer:
    def __init__(self):
        self._processed_tenders = set()
        
    def analyze_tenders(self, tenders, securities):
        if not tenders or not securities:
            return
            
        # Get current market prices
        market_prices = {
            s['ticker']: {
                'bid': s['bid'],
                'ask': s['ask'],
                'last': s['last']
            } for s in securities
        }
        
        for tender in tenders:
            tender_id = tender.get('tender_id')
            if tender_id and tender_id not in self._processed_tenders:
                self._processed_tenders.add(tender_id)
                self._analyze_single_tender(tender, market_prices)
    
    def _analyze_single_tender(self, tender, market_prices):
        ticker = tender.get('ticker')
        action = tender.get('action', '').upper()
        quantity = tender.get('quantity', 0)
        tender_price = tender.get('price', 0)
        
        if not all([ticker, action, quantity, tender_price]) or ticker not in market_prices:
            print(f"\n⚠️  Invalid tender data received: {tender}")
            return
            
        market_data = market_prices[ticker]
        
        # Calculate potential profit/loss
        if action == 'BUY':
            market_value = market_data['bid']  # We can sell at bid
            profit_per_share = market_value - tender_price
        else:  # SELL
            market_value = market_data['ask']  # We need to buy at ask
            profit_per_share = tender_price - market_value
            
        total_profit = profit_per_share * quantity
        
        self._print_analysis(
            tender, 
            market_value, 
            profit_per_share, 
            total_profit
        )
    
    def _print_analysis(self, tender, market_value, profit_per_share, total_profit):
        print("\n🔍 === Tender Analysis ===")
        print(f"ID: {tender.get('tender_id')}")
        print(f"Ticker: {tender.get('ticker')}")
        print(f"Action: {tender.get('action', 'N/A')}")
        print(f"Quantity: {tender.get('quantity', 0):,}")
        print(f"Tender Price: ${tender.get('price', 0):.2f}")
        print(f"Market Price: ${market_value:.2f}")
        print("\n📊 Results:")
        print(f"Profit per Share: ${profit_per_share:.3f}")
        print(f"Total Profit: ${total_profit:.2f}")
        
        recommendation = self._get_recommendation(total_profit)
        print(f"\n💡 Recommendation: {recommendation}")
        print("=====================\n")
    
    def _get_recommendation(self, total_profit):
        if total_profit > 0:
            return f"ACCEPT ✅ - Profit of ${total_profit:.2f}"
        else:
            return f"REJECT ❌ - Loss of ${abs(total_profit):.2f}"
