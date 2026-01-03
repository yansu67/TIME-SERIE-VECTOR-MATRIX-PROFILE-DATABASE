"""
TSDB Data Analyzer
Performs comprehensive analysis on existing data in TSDB

Features:
- Query all stored data
- Anomaly detection on historical data
- Motif discovery
- Similarity analysis
- Statistical summary
"""

import socket
import json
from datetime import datetime


TSDB_HOST = "127.0.0.1"
TSDB_PORT = 9999


def send_command(command: dict) -> dict:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((TSDB_HOST, TSDB_PORT))
        sock.sendall((json.dumps(command) + "\n").encode())
        return json.loads(sock.recv(65536).decode())


def print_separator(title=""):
    print()
    if title:
        print(f"{'='*70}")
        print(f"  {title}")
        print(f"{'='*70}")
    else:
        print("-" * 70)


def main():
    print_separator("TSDB DATA ANALYZER")
    print("  Comprehensive Analysis of Stored Time Series Data")
    print_separator()
    
    # 1. List all series
    print()
    print("[1] AVAILABLE SERIES")
    print("-" * 40)
    
    # Get stats for known series
    series_list = [
        "macro_complete",
        "anomaly_returns", 
        "motif_returns",
        "similarity_returns",
        "macro_correlation",
        "crypto_macro_prices",
        "returns_correlation",
        "sensor1",
        "benchmark"
    ]
    
    available_series = []
    for series in series_list:
        result = send_command({"type": "GetStats", "data": {"series": series}})
        if result.get("status") == "Stats":
            stats = result["data"]
            available_series.append({
                "name": series,
                "points": stats["total_points"],
                "dimension": stats["dimension"]
            })
            print(f"  [{series}] {stats['total_points']} points, dim={stats['dimension']}")
    
    if not available_series:
        print("  No data found!")
        return
    
    # 2. Analyze macro_complete (main analysis series)
    print_separator("MACRO COMPLETE ANALYSIS")
    
    result = send_command({"type": "Query", "data": {"series": "macro_complete"}})
    
    if result.get("status") == "Data" and result.get("data"):
        points = result["data"]
        print(f"  Total data points: {len(points)}")
        
        if len(points) > 0:
            # Extract values
            btc_changes = [p["values"][0] for p in points]
            eth_changes = [p["values"][1] for p in points]
            btc_dominance = [p["values"][2] for p in points]
            eth_btc = [p["values"][3] / 100 for p in points]  # Unscale
            fear_greed = [p["values"][4] for p in points]
            gold_changes = [p["values"][5] for p in points]
            
            print()
            print("  STATISTICAL SUMMARY")
            print("  " + "-" * 50)
            
            def stats_line(name, values):
                avg = sum(values) / len(values)
                min_v = min(values)
                max_v = max(values)
                print(f"  {name:20} | Avg: {avg:+8.3f} | Min: {min_v:+8.3f} | Max: {max_v:+8.3f}")
            
            stats_line("BTC 24h Change (%)", btc_changes)
            stats_line("ETH 24h Change (%)", eth_changes)
            stats_line("BTC Dominance (%)", btc_dominance)
            stats_line("ETH/BTC Ratio", eth_btc)
            stats_line("Fear & Greed", fear_greed)
            stats_line("Gold 24h Change (%)", gold_changes)
            
            # Calculate BTC-Gold correlation
            print()
            print("  CORRELATION ANALYSIS")
            print("  " + "-" * 50)
            
            if len(btc_changes) >= 5:
                # Pearson correlation
                n = len(btc_changes)
                mean_btc = sum(btc_changes) / n
                mean_gold = sum(gold_changes) / n
                
                numerator = sum((btc_changes[i] - mean_btc) * (gold_changes[i] - mean_gold) for i in range(n))
                denom_btc = sum((x - mean_btc) ** 2 for x in btc_changes) ** 0.5
                denom_gold = sum((x - mean_gold) ** 2 for x in gold_changes) ** 0.5
                
                if denom_btc > 0 and denom_gold > 0:
                    btc_gold_corr = numerator / (denom_btc * denom_gold)
                    print(f"  BTC-Gold Correlation: {btc_gold_corr:+.4f}")
                    
                    if btc_gold_corr < -0.5:
                        print("  Interpretation: Strong INVERSE correlation (risk-on/risk-off dynamic)")
                    elif btc_gold_corr < -0.2:
                        print("  Interpretation: Moderate inverse correlation")
                    elif btc_gold_corr > 0.5:
                        print("  Interpretation: Strong POSITIVE correlation (unusual)")
                    elif btc_gold_corr > 0.2:
                        print("  Interpretation: Moderate positive correlation")
                    else:
                        print("  Interpretation: Weak/no significant correlation")
                
                # BTC-ETH correlation
                mean_eth = sum(eth_changes) / n
                numerator = sum((btc_changes[i] - mean_btc) * (eth_changes[i] - mean_eth) for i in range(n))
                denom_eth = sum((x - mean_eth) ** 2 for x in eth_changes) ** 0.5
                
                if denom_btc > 0 and denom_eth > 0:
                    btc_eth_corr = numerator / (denom_btc * denom_eth)
                    print(f"  BTC-ETH Correlation: {btc_eth_corr:+.4f}")
    
    # 3. Anomaly Detection
    print_separator("ANOMALY DETECTION")
    
    for series_info in available_series:
        if series_info["points"] >= 10:
            result = send_command({
                "type": "Anomaly",
                "data": {"series": series_info["name"], "window": 5, "k": 3}
            })
            
            if result.get("status") == "Anomalies" and result.get("data"):
                print(f"\n  Series: {series_info['name']}")
                print(f"  " + "-" * 40)
                
                for i, anomaly in enumerate(result["data"]):
                    score = anomaly["score"]
                    severity = "HIGH" if score > 2.5 else "MEDIUM" if score > 1.5 else "LOW"
                    print(f"    Anomaly #{i+1}: score={score:.3f} [{severity}]")
    
    # 4. Motif Discovery
    print_separator("MOTIF DISCOVERY (Recurring Patterns)")
    
    for series_info in available_series:
        if series_info["points"] >= 15:
            result = send_command({
                "type": "Motif",
                "data": {"series": series_info["name"], "window": 5, "k": 3}
            })
            
            if result.get("status") == "Motifs" and result.get("data"):
                print(f"\n  Series: {series_info['name']}")
                print(f"  " + "-" * 40)
                
                for i, motif in enumerate(result["data"]):
                    score = motif["score"]
                    strength = "STRONG" if score < 0.5 else "MODERATE" if score < 1.0 else "WEAK"
                    print(f"    Pattern #{i+1}: score={score:.3f} [{strength}]")
    
    # 5. Similarity Search
    print_separator("SIMILARITY SEARCH")
    
    # Search for specific patterns
    patterns = [
        ("Risk-Off", [-1.0, -1.0, 55.0, 3.5, 30.0, 0.5, 200.0, 50.0]),
        ("Risk-On", [2.0, 2.5, 45.0, 4.5, 70.0, -0.5, 200.0, 100.0]),
        ("Neutral", [0.0, 0.0, 50.0, 4.0, 50.0, 0.0, 200.0, 70.0]),
    ]
    
    for pattern_name, pattern_vector in patterns:
        result = send_command({
            "type": "FindSimilar",
            "data": {
                "series": "macro_complete",
                "vector": pattern_vector,
                "limit": 3,
                "threshold": 0.0
            }
        })
        
        if result.get("status") == "Similar" and result.get("data"):
            print(f"\n  Pattern: {pattern_name}")
            print(f"  " + "-" * 40)
            
            for i, match in enumerate(result["data"][:2]):
                sim = match["similarity"]
                print(f"    Match #{i+1}: similarity={sim:.4f} ({sim*100:.1f}%)")
    
    # 6. Market Summary
    print_separator("MARKET SUMMARY")
    
    result = send_command({"type": "Query", "data": {"series": "macro_complete"}})
    
    if result.get("status") == "Data" and result.get("data"):
        points = result["data"]
        if len(points) > 0:
            latest = points[-1]["values"]
            
            # Calculate overall sentiment
            btc_change = latest[0]
            eth_change = latest[1]
            btc_dom = latest[2]
            fear_greed = latest[4]
            gold_change = latest[5]
            
            print()
            print("  LATEST MARKET STATE")
            print("  " + "-" * 50)
            print(f"  BTC 24h Change:    {btc_change:+.2f}%")
            print(f"  ETH 24h Change:    {eth_change:+.2f}%")
            print(f"  BTC Dominance:     {btc_dom:.1f}%")
            print(f"  Fear & Greed:      {fear_greed:.0f}")
            print(f"  Gold 24h Change:   {gold_change:+.2f}%")
            
            print()
            print("  MARKET INTERPRETATION")
            print("  " + "-" * 50)
            
            # Determine market condition
            if fear_greed < 30:
                print("  - FEAR in market: Potential contrarian BUY opportunity")
            elif fear_greed > 70:
                print("  - GREED in market: Consider taking profits")
            
            if btc_dom > 55:
                print("  - HIGH BTC Dominance: Risk-off, money flowing to BTC")
            elif btc_dom < 45:
                print("  - LOW BTC Dominance: Alt season potential")
            
            if gold_change > 0.3 and btc_change < -0.3:
                print("  - Gold up, BTC down: Flight to safety active")
            elif gold_change < -0.3 and btc_change > 0.3:
                print("  - BTC up, Gold down: Risk-on sentiment")
            
            if btc_change > 2:
                print("  - Strong BTC momentum: Bullish")
            elif btc_change < -2:
                print("  - Weak BTC momentum: Bearish")
            else:
                print("  - Sideways movement: Wait for breakout")
    
    print_separator()
    print("  Analysis Complete!")
    print_separator()


if __name__ == "__main__":
    main()
