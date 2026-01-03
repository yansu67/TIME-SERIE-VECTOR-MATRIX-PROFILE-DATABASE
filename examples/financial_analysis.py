"""
TSDB Financial Analysis Example
Crypto Market Analysis with Macro Factors (Gold, DXY, etc.)

This script demonstrates how to use TSDB for:
1. Storing multi-dimensional financial time series
2. Finding correlations between crypto and macro factors
3. Detecting anomalies in market behavior
4. Finding recurring patterns (motifs)
"""

import socket
import json
import random
from datetime import datetime, timedelta

# TSDB Connection Settings
TSDB_HOST = "127.0.0.1"
TSDB_PORT = 9999


def send_command(command: dict) -> dict:
    """Send JSON command to TSDB and return response."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((TSDB_HOST, TSDB_PORT))
        sock.sendall((json.dumps(command) + "\n").encode())
        response = sock.recv(65536).decode()
        return json.loads(response)


def create_series(name: str, dimension: int) -> dict:
    """Create a new time series."""
    return send_command({
        "type": "CreateSeries",
        "data": {"name": name, "dimension": dimension}
    })


def insert_data(series: str, values: list) -> dict:
    """Insert data point into series."""
    return send_command({
        "type": "Insert",
        "data": {"series": series, "values": values}
    })


def query_data(series: str) -> dict:
    """Query all data from series."""
    return send_command({
        "type": "Query",
        "data": {"series": series}
    })


def find_similar(series: str, vector: list, limit: int = 10, threshold: float = 0.5) -> dict:
    """Find similar patterns."""
    return send_command({
        "type": "FindSimilar",
        "data": {
            "series": series,
            "vector": vector,
            "limit": limit,
            "threshold": threshold
        }
    })


def detect_anomaly(series: str, window: int, k: int) -> dict:
    """Detect anomalies using Matrix Profile."""
    return send_command({
        "type": "Anomaly",
        "data": {"series": series, "window": window, "k": k}
    })


def find_motif(series: str, window: int, k: int) -> dict:
    """Find recurring patterns using Matrix Profile."""
    return send_command({
        "type": "Motif",
        "data": {"series": series, "window": window, "k": k}
    })


def get_stats(series: str) -> dict:
    """Get series statistics."""
    return send_command({
        "type": "GetStats",
        "data": {"series": series}
    })


# =============================================================================
# Example: Crypto-Macro Correlation Analysis
# =============================================================================

def generate_sample_data():
    """
    Generate sample financial data for demonstration.
    In production, replace with real data from APIs like:
    - CoinGecko/Binance for crypto
    - Yahoo Finance for gold/stocks
    - FRED for macro indicators
    """
    data = []
    base_btc = 42000
    base_eth = 2200
    base_gold = 2050
    base_dxy = 102.5
    base_sp500 = 4750
    
    for i in range(100):
        # Simulate correlated market movements
        market_factor = random.gauss(0, 1)
        risk_on = random.gauss(0, 0.5)
        
        btc_change = market_factor * 500 + risk_on * 300 + random.gauss(0, 200)
        eth_change = market_factor * 30 + risk_on * 20 + random.gauss(0, 15)
        gold_change = -market_factor * 10 + random.gauss(0, 5)  # Inverse correlation
        dxy_change = -risk_on * 0.3 + random.gauss(0, 0.1)
        sp500_change = market_factor * 20 + random.gauss(0, 10)
        
        data.append({
            "btc_price": base_btc + btc_change,
            "eth_price": base_eth + eth_change,
            "gold_price": base_gold + gold_change,
            "dxy_index": base_dxy + dxy_change,
            "sp500": base_sp500 + sp500_change,
            # Normalized returns for correlation analysis
            "btc_return": btc_change / base_btc * 100,
            "eth_return": eth_change / base_eth * 100,
            "gold_return": gold_change / base_gold * 100,
        })
        
        # Update base prices
        base_btc += btc_change * 0.1
        base_eth += eth_change * 0.1
        base_gold += gold_change * 0.1
        base_dxy += dxy_change * 0.1
        base_sp500 += sp500_change * 0.1
    
    return data


def main():
    print("=" * 60)
    print("TSDB Financial Analysis - Crypto & Macro Correlation")
    print("=" * 60)
    print()
    
    # 1. Create series for different analysis types
    print("[1] Creating time series...")
    
    # Multi-asset price series (5 dimensions: BTC, ETH, Gold, DXY, SP500)
    result = create_series("crypto_macro_prices", 5)
    print(f"    crypto_macro_prices: {result['status']}")
    
    # Returns series for correlation (3 dimensions: BTC, ETH, Gold returns)
    result = create_series("returns_correlation", 3)
    print(f"    returns_correlation: {result['status']}")
    
    # 2. Insert sample data
    print()
    print("[2] Inserting 100 time points of market data...")
    
    sample_data = generate_sample_data()
    
    for i, point in enumerate(sample_data):
        # Insert price data
        insert_data("crypto_macro_prices", [
            point["btc_price"],
            point["eth_price"],
            point["gold_price"],
            point["dxy_index"],
            point["sp500"]
        ])
        
        # Insert returns data
        insert_data("returns_correlation", [
            point["btc_return"],
            point["eth_return"],
            point["gold_return"]
        ])
        
        if (i + 1) % 25 == 0:
            print(f"    Inserted {i + 1} points...")
    
    # 3. Get statistics
    print()
    print("[3] Series Statistics:")
    
    stats = get_stats("crypto_macro_prices")
    print(f"    crypto_macro_prices: {stats['data']['total_points']} points, dim={stats['data']['dimension']}")
    
    stats = get_stats("returns_correlation")
    print(f"    returns_correlation: {stats['data']['total_points']} points, dim={stats['data']['dimension']}")
    
    # 4. Similarity Search - Find similar market conditions
    print()
    print("[4] Similarity Search - Finding similar market conditions...")
    
    # Search for periods similar to "risk-off" scenario
    # (BTC down, ETH down, Gold up)
    risk_off_pattern = [-2.0, -2.5, 0.5]  # Returns: BTC -2%, ETH -2.5%, Gold +0.5%
    
    similar = find_similar("returns_correlation", risk_off_pattern, limit=5, threshold=0.0)
    print(f"    Query pattern (risk-off): BTC=-2%, ETH=-2.5%, Gold=+0.5%")
    print(f"    Found {len(similar.get('data', []))} similar periods:")
    
    for i, match in enumerate(similar.get('data', [])[:3]):
        print(f"      #{i+1}: similarity={match['similarity']:.4f}, values={[round(v,2) for v in match['values']]}")
    
    # 5. Anomaly Detection
    print()
    print("[5] Anomaly Detection - Finding unusual market behavior...")
    
    anomalies = detect_anomaly("returns_correlation", window=5, k=3)
    print(f"    Detected {len(anomalies.get('data', []))} anomalies:")
    
    for i, anomaly in enumerate(anomalies.get('data', [])):
        print(f"      #{i+1}: score={anomaly['score']:.4f}, window_size={anomaly['window_size']}")
    
    # 6. Motif Discovery - Find recurring patterns
    print()
    print("[6] Motif Discovery - Finding recurring market patterns...")
    
    motifs = find_motif("returns_correlation", window=5, k=3)
    print(f"    Discovered {len(motifs.get('data', []))} recurring patterns:")
    
    for i, motif in enumerate(motifs.get('data', [])):
        print(f"      #{i+1}: score={motif['score']:.4f}, window_size={motif['window_size']}")
    
    # 7. Cross-asset correlation analysis
    print()
    print("[7] Cross-Asset Correlation Analysis...")
    
    # Query recent data
    data = query_data("returns_correlation")
    points = data.get('data', [])
    
    if len(points) >= 10:
        # Calculate simple correlation between BTC and Gold
        btc_returns = [p['values'][0] for p in points[-30:]]
        gold_returns = [p['values'][2] for p in points[-30:]]
        
        # Simple correlation coefficient
        n = len(btc_returns)
        mean_btc = sum(btc_returns) / n
        mean_gold = sum(gold_returns) / n
        
        numerator = sum((btc_returns[i] - mean_btc) * (gold_returns[i] - mean_gold) for i in range(n))
        denom_btc = sum((x - mean_btc) ** 2 for x in btc_returns) ** 0.5
        denom_gold = sum((x - mean_gold) ** 2 for x in gold_returns) ** 0.5
        
        if denom_btc > 0 and denom_gold > 0:
            correlation = numerator / (denom_btc * denom_gold)
            print(f"    BTC-Gold correlation (last 30 periods): {correlation:.4f}")
            
            if correlation < -0.3:
                print("    Interpretation: Strong inverse correlation (risk-on/risk-off dynamic)")
            elif correlation > 0.3:
                print("    Interpretation: Positive correlation (both moving together)")
            else:
                print("    Interpretation: Weak/no correlation")
    
    print()
    print("=" * 60)
    print("Analysis Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
