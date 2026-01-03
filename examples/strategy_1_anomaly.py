"""
Strategy 1: Anomaly-Based Trading
Detects unusual market behavior and generates reversal signals

Run: python strategy_1_anomaly.py
"""

import socket
import json
import time
import urllib.request
from datetime import datetime

TSDB_HOST = "127.0.0.1"
TSDB_PORT = 9999
POLL_INTERVAL = 60  # seconds


def send_command(command: dict) -> dict:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((TSDB_HOST, TSDB_PORT))
        sock.sendall((json.dumps(command) + "\n").encode())
        return json.loads(sock.recv(65536).decode())


def fetch_prices():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            return {
                "btc": data["bitcoin"]["usd"],
                "btc_change": data["bitcoin"]["usd_24h_change"],
                "eth": data["ethereum"]["usd"],
                "eth_change": data["ethereum"]["usd_24h_change"],
            }
    except:
        return None


def analyze_anomaly(score, btc_change):
    """Generate trading signal based on anomaly score."""
    if score < 1.5:
        return "HOLD", "Normal market conditions"
    elif score < 2.0:
        return "CAUTION", "Slightly unusual activity"
    elif score < 2.5:
        if btc_change < -2:
            return "BUY", f"Anomaly + Oversold (BTC {btc_change:+.2f}%)"
        elif btc_change > 2:
            return "SELL", f"Anomaly + Overbought (BTC {btc_change:+.2f}%)"
        else:
            return "WATCH", "Anomaly detected, waiting for direction"
    else:
        if btc_change < -3:
            return "STRONG BUY", f"Extreme anomaly + Deep oversold (BTC {btc_change:+.2f}%)"
        elif btc_change > 3:
            return "STRONG SELL", f"Extreme anomaly + Deep overbought (BTC {btc_change:+.2f}%)"
        else:
            return "HIGH ALERT", "Extreme anomaly, major move expected"


def main():
    print("=" * 70)
    print("  STRATEGY 1: ANOMALY-BASED TRADING")
    print("  Detects unusual market behavior for reversal opportunities")
    print("=" * 70)
    print()
    
    # Initialize series
    send_command({"type": "CreateSeries", "data": {"name": "anomaly_returns", "dimension": 2}})
    print("[INIT] Series created: anomaly_returns (BTC%, ETH%)")
    print(f"[INIT] Polling interval: {POLL_INTERVAL} seconds")
    print()
    print("Press Ctrl+C to stop")
    print("-" * 70)
    
    data_count = 0
    
    while True:
        try:
            prices = fetch_prices()
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            if prices:
                # Insert returns data
                send_command({
                    "type": "Insert",
                    "data": {
                        "series": "anomaly_returns",
                        "values": [prices["btc_change"], prices["eth_change"]]
                    }
                })
                data_count += 1
                
                # Need at least 10 points for anomaly detection
                if data_count >= 10:
                    result = send_command({
                        "type": "Anomaly",
                        "data": {"series": "anomaly_returns", "window": 5, "k": 1}
                    })
                    
                    if result["status"] == "Anomalies" and result["data"]:
                        score = result["data"][0]["score"]
                        signal, reason = analyze_anomaly(score, prices["btc_change"])
                        
                        signal_color = {
                            "HOLD": "",
                            "CAUTION": "[!]",
                            "WATCH": "[?]",
                            "BUY": "[BUY]",
                            "SELL": "[SELL]",
                            "STRONG BUY": "[*** BUY ***]",
                            "STRONG SELL": "[*** SELL ***]",
                            "HIGH ALERT": "[!!! ALERT !!!]"
                        }.get(signal, "")
                        
                        print(f"[{timestamp}] BTC: ${prices['btc']:,.0f} ({prices['btc_change']:+.2f}%) | "
                              f"ETH: ${prices['eth']:,.0f} ({prices['eth_change']:+.2f}%) | "
                              f"Anomaly: {score:.2f} | {signal_color} {signal}")
                        
                        if signal in ["BUY", "SELL", "STRONG BUY", "STRONG SELL", "HIGH ALERT"]:
                            print(f"         Reason: {reason}")
                    else:
                        print(f"[{timestamp}] BTC: ${prices['btc']:,.0f} ({prices['btc_change']:+.2f}%) | "
                              f"ETH: ${prices['eth']:,.0f} ({prices['eth_change']:+.2f}%) | "
                              f"Collecting data... ({data_count} points)")
                else:
                    print(f"[{timestamp}] BTC: ${prices['btc']:,.0f} ({prices['btc_change']:+.2f}%) | "
                          f"Warming up... ({data_count}/10 points)")
            else:
                print(f"[{timestamp}] Failed to fetch prices")
            
            time.sleep(POLL_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n[STOP] Strategy stopped by user")
            break


if __name__ == "__main__":
    main()
