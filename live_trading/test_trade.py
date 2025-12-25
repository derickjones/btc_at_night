#!/usr/bin/env python3
"""
Test script to verify Alpaca paper trading is working.
Executes a small test trade to confirm connectivity and order execution.
"""

import sys
from datetime import datetime
from alpaca_client import AlpacaTradingClient
from config import SYMBOL

def main():
    print("=" * 60)
    print("🧪 ALPACA PAPER TRADING TEST")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Symbol: {SYMBOL}")
    print()
    
    # Initialize client
    print("1️⃣  Connecting to Alpaca...")
    client = AlpacaTradingClient()
    
    if not client.api:
        print("❌ Failed to connect to Alpaca API")
        sys.exit(1)
    
    # Get account info
    print("\n2️⃣  Checking account...")
    account_info = client.get_account_info()
    if account_info:
        print(f"   ✅ Account connected")
        print(f"   💰 Buying Power: ${account_info.get('buying_power', 0):,.2f}")
        print(f"   📊 Portfolio Value: ${account_info.get('portfolio_value', 0):,.2f}")
    else:
        print("   ❌ Could not get account info")
        sys.exit(1)
    
    # Check current position
    print(f"\n3️⃣  Checking current {SYMBOL} position...")
    position = client.get_current_position()
    if position:
        print(f"   📈 Current position: {position['qty']} shares")
        print(f"   💵 Market value: ${position['market_value']:,.2f}")
        print(f"   📊 Unrealized P&L: ${position['unrealized_pl']:,.2f}")
    else:
        print(f"   📭 No current {SYMBOL} position")
    
    # Get current price
    print(f"\n4️⃣  Getting current {SYMBOL} price...")
    price = client.get_latest_price()
    if price:
        print(f"   💲 Current price: ${price:.2f}")
    else:
        print("   ❌ Could not get price")
        sys.exit(1)
    
    # Check if market is open
    print("\n5️⃣  Checking market status...")
    market_open = client.is_market_open()
    print(f"   🏛️  Market is: {'OPEN ✅' if market_open else 'CLOSED ❌'}")
    
    if not market_open:
        print("\n⚠️  Market is closed - cannot execute test trade")
        print("   The market is open Mon-Fri 9:30 AM - 4:00 PM ET")
        print("   All connection tests passed! ✅")
        return
    
    # Ask user if they want to execute a test trade
    print("\n" + "=" * 60)
    print("🧪 READY TO EXECUTE TEST TRADE")
    print("=" * 60)
    print(f"This will BUY 1 share of {SYMBOL} at ~${price:.2f}")
    print("This is PAPER TRADING - no real money involved")
    print()
    
    response = input("Execute test trade? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("\n❌ Test trade cancelled")
        return
    
    # Execute test buy
    print(f"\n6️⃣  Placing BUY order for 1 share of {SYMBOL}...")
    order_id = client.place_market_order('buy', 1)
    
    if order_id:
        print(f"   ✅ Order placed! ID: {order_id}")
        
        # Wait for fill
        print("   ⏳ Waiting for order to fill...")
        filled = client.wait_for_order_fill(order_id, timeout=30)
        
        if filled:
            print("   ✅ ORDER FILLED SUCCESSFULLY!")
            
            # Check new position
            new_position = client.get_current_position()
            if new_position:
                print(f"   📈 New position: {new_position['qty']} shares")
        else:
            print("   ⚠️  Order not filled within timeout (may still fill)")
    else:
        print("   ❌ Failed to place order")
        sys.exit(1)
    
    # Ask if user wants to sell
    print("\n" + "=" * 60)
    response = input("Sell the test share? (yes/no): ").strip().lower()
    
    if response == 'yes':
        print(f"\n7️⃣  Placing SELL order for 1 share of {SYMBOL}...")
        sell_order_id = client.place_market_order('sell', 1)
        
        if sell_order_id:
            print(f"   ✅ Sell order placed! ID: {sell_order_id}")
            filled = client.wait_for_order_fill(sell_order_id, timeout=30)
            if filled:
                print("   ✅ SELL ORDER FILLED!")
        else:
            print("   ❌ Failed to place sell order")
    
    print("\n" + "=" * 60)
    print("✅ TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
