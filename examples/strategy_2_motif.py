"""
Strategy 2: Motif-Based Trading
Identifies recurring patterns and trades on pattern completion

Run: python strategy_2_motif.py
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


def analyze_motif(score, previous_scores):
    """
    Analyze motif patterns.
    Lower score = stronger recurring pattern
    """
    if score > 2.0:
        return "NO PATTERN", "No significant recurring pattern detected"
    
    elif score > 1.0:
        return "WEAK PATTERN", f"Weak recurring pattern (score: {score:.2f})"
    
    elif score > 0.5:
        # Clear pattern detected
        if len(previous_scores) >= 2:
            trend = "strengthening" if score < previous_scores[-1] else "weakening"
            return "PATTERN DETECTED", f"Clear pattern {trend} (score: {score:.2f})"
        return "PATTERN DETECTED", f"Clear recurring pattern (score: {score:.2f})"
    
    else:
        # Very strong pattern - high predictability
        return "STRONG PATTERN", f"Very strong recurring pattern! (score: {score:.2f}) - HIGH PREDICTABILITY"


def get_pattern_signal(motif_score, btc_change, pattern_history):
    """
    Generate trading signal based on pattern strength and direction.
    """
    if motif_score > 1.0:
        return "HOLD", "Wait for clear pattern"
    
    # Strong pattern detected - analyze direction
    if len(pattern_history) >= 3:
        # Calculate average direction after pattern
        avg_direction = sum(pattern_history[-3:]) / 3
        
        if motif_score < 0.5:
            # Very strong pattern
            if avg_direction > 0.5:
                return "BUY", f"Strong bullish pattern (avg: {avg_direction:+.2f}%)"
            elif avg_direction < -0.5:
                return "SELL", f"Strong bearish pattern (avg: {avg_direction:+.2f}%)"
        
        elif motif_score < 1.0:
            # Moderate pattern
            if avg_direction > 1.0:
                return "WEAK BUY", f"Bullish tendency (avg: {avg_direction:+.2f}%)"
            elif avg_direction < -1.0:
                return "WEAK SELL", f"Bearish tendency (avg: {avg_direction:+.2f}%)"
    
    return "WATCH", "Pattern detected, collecting directional data"


def main():
    print("=" * 70)
    print("  STRATEGY 2: MOTIF-BASED TRADING")
    print("  Identifies recurring patterns for predictable trades")
    print("=" * 70)
    print()
    
    # Initialize series
    send_command({"type": "CreateSeries", "data": {"name": "motif_returns", "dimension": 2}})
    print("[INIT] Series created: motif_returns (BTC%, ETH%)")
    print(f"[INIT] Polling interval: {POLL_INTERVAL} seconds")
    print()
    print("Press Ctrl+C to stop")
    print("-" * 70)
    
    data_count = 0
    motif_scores = []
    pattern_history = []
    
    while True:
        try:
            prices = fetch_prices()
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            if prices:
                # Insert returns data
                send_command({
                    "type": "Insert",
                    "data": {
                        "series": "motif_returns",
                        "values": [prices["btc_change"], prices["eth_change"]]
                    }
                })
                data_count += 1
                pattern_history.append(prices["btc_change"])
                if len(pattern_history) > 20:
                    pattern_history.pop(0)
                
                # Need at least 15 points for motif detection
                if data_count >= 15:
                    result = send_command({
                        "type": "Motif",
                        "data": {"series": "motif_returns", "window": 5, "k": 1}
                    })
                    
                    if result["status"] == "Motifs" and result["data"]:
                        score = result["data"][0]["score"]
                        motif_scores.append(score)
                        if len(motif_scores) > 10:
                            motif_scores.pop(0)
                        
                        pattern_status, pattern_desc = analyze_motif(score, motif_scores)
                        signal, signal_reason = get_pattern_signal(score, prices["btc_change"], pattern_history)
                        
                        # Display
                        pattern_indicator = {
                            "NO PATTERN": "[ ]",
                            "WEAK PATTERN": "[~]",
                            "PATTERN DETECTED": "[#]",
                            "STRONG PATTERN": "[###]"
                        }.get(pattern_status, "")
                        
                        signal_indicator = {
                            "HOLD": "",
                            "WATCH": "[?]",
                            "WEAK BUY": "[+]",
                            "WEAK SELL": "[-]",
                            "BUY": "[BUY]",
                            "SELL": "[SELL]"
                        }.get(signal, "")
                        
                        print(f"[{timestamp}] BTC: ${prices['btc']:,.0f} ({prices['btc_change']:+.2f}%) | "
                              f"Motif Score: {score:.3f} {pattern_indicator} | {signal_indicator} {signal}")
                        
                        if pattern_status == "STRONG PATTERN" or signal in ["BUY", "SELL"]:
                            print(f"         Pattern: {pattern_desc}")
                            if signal in ["BUY", "SELL", "WEAK BUY", "WEAK SELL"]:
                                print(f"         Signal: {signal_reason}")
                    else:
                        print(f"[{timestamp}] BTC: ${prices['btc']:,.0f} | Analyzing patterns... ({data_count} points)")
                else:
                    print(f"[{timestamp}] BTC: ${prices['btc']:,.0f} | Warming up... ({data_count}/15 points)")
            else:
                print(f"[{timestamp}] Failed to fetch prices")
            
            time.sleep(POLL_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n[STOP] Strategy stopped by user")
            break


if __name__ == "__main__":
    main()
