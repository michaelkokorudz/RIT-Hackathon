# RIT Hackathon: Liability Trading UI & Market-Making Algorithm  

This repository contains two key components developed during the **RIT Hackathon**:  

1. **Liability Trading UI**: A hands-on interface designed to streamline decision-making in the **Liability Trading Case**, enabling participants to efficiently value tender offers in real time.  
2. **Market-Making Algorithm**: An advanced trading bot created for the **Market-Making Case**, leveraging a mean-reversion strategy to dynamically manage positions, spreads, and risks.  

---

## Overview  

The RIT Hackathon required participants to design systems capable of solving challenges in two distinct cases:  

1. **Liability Trading Case**:  
   Participants acted as traders tasked with managing liabilities through a dynamic tendering process. To streamline this process, we created the **Liability Trading UI**, which allowed us to efficiently value, accept, or decline tender offers in real time. We believed this interface would simplify decision-making and provide better insights into tender valuations and risk management.  

2. **Market-Making Case**:  
   This case tested the ability to develop an **algorithmic trading strategy** capable of making markets efficiently. The challenge involved designing a bot that could dynamically quote bid-ask spreads, manage risk, and optimize profitability in a highly volatile environment.  


## Market-Making Algorithm  

The **Market-Making Algorithm** was developed for the **Market-Making Case** and leveraged a **mean-reversion strategy** to exploit price inefficiencies while managing inventory and risk.  

### Key Features:  

1. **Dynamic Spread Management**  
   - Adapts spreads dynamically based on market conditions, volatility, and current inventory.  
   - Implements position-aware spreads to avoid excessive exposure in one direction.  

2. **Mean-Reversion Trading**  
   - Calculates Z-scores using price history to identify overbought or oversold conditions.  
   - Executes trades to profit from price reversion to the mean.  

3. **Inventory & Risk Management**  
   - Tracks open positions and ensures compliance with position limits.  
   - Aggressively reduces positions when risk thresholds are breached.  

4. **Real-Time Execution**  
   - Continuously monitors market data and updates orders at regular intervals.  
   - Ensures orders are refreshed to prevent stale quotes.  
 
