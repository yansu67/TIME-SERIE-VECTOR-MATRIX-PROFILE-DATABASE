"""
TSDB Real-Time Crypto Analysis with Live Data
Uses CoinGecko API (free, no API key required)

Features:
- Fetch real BTC, ETH, and Gold prices
- Store in TSDB with multi-dimensional vectors
- Analyze correlations and detect anomalies
"""

import socket
import json
import time
import urllib.request
from datetime import datetime


# TSDB Connection
TSDB_HOST = "127.0.0.1"
TSDB_PORT = 9999


def send_command(command: dict) -> dict:
    """Send JSON command to TSDB."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((TSDB_HOST, TSDB_PORT))
        sock.sendall((json.dumps(command) + "\n").encode())
        response = sock.recv(65536).decode()
        return json.loads(response)


def fetch_crypto_prices():
    """Fetch real prices from CoinGecko API."""
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,tether-gold&vs_currencies=usd&include_24hr_change=true"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            
            return {
                "btc_price": data.get("bitcoin", {}).get("usd", 0),
                "btc_24h_change": data.get("bitcoin", {}).get("usd_24h_change", 0),
                "eth_price": data.get("ethereum", {}).get("usd", 0),
                "eth_24h_change": data.get("ethereum", {}).get("usd_24h_change", 0),
                "gold_price": data.get("tether-gold", {}).get("usd", 0),
                "gold_24h_change": data.get("tether-gold", {}).get("usd_24h_change", 0),
            }
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None


def main():
    print("=" * 60)
    print("TSDB Real-Time Crypto Analysis")
    print("=" * 60)
    print()
    
    # Create series
    print("[1] Creating series...")
    
    # Price series: BTC, ETH, Gold (3 dimensions)
    result = send_command({
        "type": "CreateSeries",
        "data": {"name": "live_crypto_prices", "dimension": 3}
    })
    print(f"    live_crypto_prices: {result['status']}")
    
    # 24h change series for correlation
    result = send_command({
        "type": "CreateSeries",
        "data": {"name": "live_24h_changes", "dimension": 3}
    })
    print(f"    live_24h_changes: {result['status']}")
    
    # Fetch and insert data
    print()
    print("[2] Fetching live prices from CoinGecko...")
    
    prices = fetch_crypto_prices()
    
    if prices:
        print(f"    BTC: ${prices['btc_price']:,.2f} ({prices['btc_24h_change']:+.2f}%)")
        print(f"    ETH: ${prices['eth_price']:,.2f} ({prices['eth_24h_change']:+.2f}%)")
        print(f"    Gold: ${prices['gold_price']:,.2f} ({prices['gold_24h_change']:+.2f}%)")
        
        # Insert prices
        result = send_command({
            "type": "Insert",
            "data": {
                "series": "live_crypto_prices",
                "values": [prices['btc_price'], prices['eth_price'], prices['gold_price']]
            }
        })
        print(f"\n    Inserted prices: {result['status']}")
        
        # Insert 24h changes
        result = send_command({
            "type": "Insert",
            "data": {
                "series": "live_24h_changes",
                "values": [prices['btc_24h_change'], prices['eth_24h_change'], prices['gold_24h_change']]
            }
        })
        print(f"    Inserted 24h changes: {result['status']}")
    else:
        print("    Failed to fetch live data")
    
    # Query and analyze
    print()
    print("[3] Query stored data...")
    
    result = send_command({
        "type": "Query",
        "data": {"series": "live_crypto_prices"}
    })
    
    if result['status'] == 'Data':
        points = result['data']
        print(f"    Total data points: {len(points)}")
        if points:
            latest = points[-1]
            print(f"    Latest: BTC=${latest['values'][0]:,.2f}, ETH=${latest['values'][1]:,.2f}, Gold=${latest['values'][2]:,.2f}")
    
    # Find similar market conditions
    print()
    print("[4] Similarity Search - Finding similar 24h change patterns...")
    
    if prices:
        result = send_command({
            "type": "FindSimilar",
            "data": {
                "series": "live_24h_changes",
                "vector": [prices['btc_24h_change'], prices['eth_24h_change'], prices['gold_24h_change']],
                "limit": 5,
                "threshold": 0.0
            }
        })
        
        if result['status'] == 'Similar' and result['data']:
            print(f"    Found {len(result['data'])} similar patterns")
            for i, match in enumerate(result['data'][:3]):
                vals = match['values']
                print(f"      #{i+1}: BTC={vals[0]:+.2f}%, ETH={vals[1]:+.2f}%, Gold={vals[2]:+.2f}% (similarity={match['similarity']:.4f})")
        else:
            print("    No similar patterns found yet (need more data)")
    
    print()
    print("[5] Continuous monitoring mode...")
    print("    Run this script periodically (e.g., every 5 minutes) to build historical data")
    print("    For real-time monitoring, use: while True: fetch_and_insert(); time.sleep(300)")
    
    print()
    print("=" * 60)
    print("Done!")
    print("=" * 60)


# Example: Continuous monitoring loop (uncomment to use)
def continuous_monitoring(interval_seconds=300):
    """Run continuous monitoring loop."""
    print(f"Starting continuous monitoring (interval: {interval_seconds}s)")
    print("Press Ctrl+C to stop")
    
    # Create series once
    send_command({
        "type": "CreateSeries",
        "data": {"name": "live_crypto_prices", "dimension": 3}
    })
    
    while True:
        try:
            prices = fetch_crypto_prices()
            if prices:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{timestamp}] BTC=${prices['btc_price']:,.2f}, ETH=${prices['eth_price']:,.2f}, Gold=${prices['gold_price']:,.2f}")
                
                send_command({
                    "type": "Insert",
                    "data": {
                        "series": "live_crypto_prices",
                        "values": [prices['btc_price'], prices['eth_price'], prices['gold_price']]
                    }
                })
            
            time.sleep(interval_seconds)
            
        except KeyboardInterrupt:
            print("\nStopping monitoring...")
            break


if __name__ == "__main__":
    main()
    
    # Uncomment below for continuous monitoring:
    # continuous_monitoring(interval_seconds=60)
