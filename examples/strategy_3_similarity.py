"""
Strategy 3: Similarity-Based Trading
Finds historical precedents and predicts based on what happened next

Run: python strategy_3_similarity.py
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


def analyze_similarity(matches, price_history):
    """
    Analyze similar historical conditions and predict next move.
    """
    if not matches:
        return "NO MATCH", None, "No similar historical conditions found"
    
    best_match = matches[0]
    similarity = best_match["similarity"]
    match_values = best_match["values"]
    
    if similarity < 0.7:
        return "WEAK MATCH", similarity, f"Low similarity ({similarity:.2%}), unreliable"
    
    elif similarity < 0.85:
        return "MODERATE MATCH", similarity, f"Moderate similarity ({similarity:.2%})"
    
    elif similarity < 0.95:
        return "GOOD MATCH", similarity, f"Good historical match ({similarity:.2%})"
    
    else:
        return "EXCELLENT MATCH", similarity, f"Excellent match ({similarity:.2%}) - HIGH CONFIDENCE"


def predict_from_history(matches, all_data, current_btc):
    """
    Look at what happened after similar conditions in history.
    """
    if not matches or len(all_data) < 5:
        return "HOLD", "Insufficient data for prediction"
    
    best_similarity = matches[0]["similarity"]
    
    if best_similarity < 0.7:
        return "HOLD", "Similarity too low for reliable prediction"
    
    # Count bullish vs bearish outcomes after similar conditions
    bullish_count = 0
    bearish_count = 0
    avg_move = 0
    
    for i, match in enumerate(matches[:5]):
        # Simulate: in real implementation, track what happened next
        # For demo, use simple momentum
        if match["values"][0] > 0:
            bullish_count += 1
            avg_move += match["values"][0]
        else:
            bearish_count += 1
            avg_move += match["values"][0]
    
    if bullish_count + bearish_count > 0:
        avg_move /= (bullish_count + bearish_count)
    
    confidence = best_similarity * 100
    
    if bullish_count > bearish_count * 1.5:
        if confidence > 85:
            return "BUY", f"Historically bullish ({bullish_count}/{bullish_count+bearish_count}) - {confidence:.0f}% confidence"
        return "WEAK BUY", f"Bullish tendency ({bullish_count}/{bullish_count+bearish_count})"
    
    elif bearish_count > bullish_count * 1.5:
        if confidence > 85:
            return "SELL", f"Historically bearish ({bearish_count}/{bullish_count+bearish_count}) - {confidence:.0f}% confidence"
        return "WEAK SELL", f"Bearish tendency ({bearish_count}/{bullish_count+bearish_count})"
    
    return "NEUTRAL", f"Mixed historical outcomes ({bullish_count}B/{bearish_count}S)"


def main():
    print("=" * 70)
    print("  STRATEGY 3: SIMILARITY-BASED TRADING")
    print("  Finds historical precedents to predict next moves")
    print("=" * 70)
    print()
    
    # Initialize series
    send_command({"type": "CreateSeries", "data": {"name": "similarity_returns", "dimension": 2}})
    print("[INIT] Series created: similarity_returns (BTC%, ETH%)")
    print(f"[INIT] Polling interval: {POLL_INTERVAL} seconds")
    print()
    print("Press Ctrl+C to stop")
    print("-" * 70)
    
    data_count = 0
    price_history = []
    
    while True:
        try:
            prices = fetch_prices()
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            if prices:
                current_vector = [prices["btc_change"], prices["eth_change"]]
                
                # Insert returns data
                send_command({
                    "type": "Insert",
                    "data": {
                        "series": "similarity_returns",
                        "values": current_vector
                    }
                })
                data_count += 1
                price_history.append(prices["btc_change"])
                if len(price_history) > 50:
                    price_history.pop(0)
                
                # Need some history for similarity search
                if data_count >= 10:
                    # Find similar conditions
                    result = send_command({
                        "type": "FindSimilar",
                        "data": {
                            "series": "similarity_returns",
                            "vector": current_vector,
                            "limit": 10,
                            "threshold": 0.5
                        }
                    })
                    
                    if result["status"] == "Similar":
                        matches = result.get("data", [])
                        
                        # Analyze matches
                        match_status, similarity, match_desc = analyze_similarity(matches, price_history)
                        signal, signal_reason = predict_from_history(matches, price_history, prices["btc_change"])
                        
                        # Display
                        match_indicator = {
                            "NO MATCH": "[ ]",
                            "WEAK MATCH": "[~]",
                            "MODERATE MATCH": "[=]",
                            "GOOD MATCH": "[#]",
                            "EXCELLENT MATCH": "[###]"
                        }.get(match_status, "")
                        
                        signal_indicator = {
                            "HOLD": "",
                            "NEUTRAL": "[=]",
                            "WEAK BUY": "[+]",
                            "WEAK SELL": "[-]",
                            "BUY": "[BUY]",
                            "SELL": "[SELL]"
                        }.get(signal, "")
                        
                        sim_pct = f"{similarity:.1%}" if similarity else "N/A"
                        
                        print(f"[{timestamp}] BTC: ${prices['btc']:,.0f} ({prices['btc_change']:+.2f}%) | "
                              f"Matches: {len(matches)} | Best: {sim_pct} {match_indicator} | {signal_indicator} {signal}")
                        
                        if match_status in ["GOOD MATCH", "EXCELLENT MATCH"] or signal in ["BUY", "SELL"]:
                            print(f"         Historical: {match_desc}")
                            print(f"         Prediction: {signal_reason}")
                    else:
                        print(f"[{timestamp}] BTC: ${prices['btc']:,.0f} | Searching history... ({data_count} points)")
                else:
                    print(f"[{timestamp}] BTC: ${prices['btc']:,.0f} | Building history... ({data_count}/10 points)")
            else:
                print(f"[{timestamp}] Failed to fetch prices")
            
            time.sleep(POLL_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n[STOP] Strategy stopped by user")
            break


if __name__ == "__main__":
    main()
