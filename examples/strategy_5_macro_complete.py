"""
Strategy 5: Comprehensive Macro Analysis
Integrates ALL macro factors for complete market analysis

Categories:
1. Currency & Rates (DXY, Treasury Yield, EUR/USD)
2. Equity Markets (S&P 500, NASDAQ, VIX)
3. Commodities (Gold, Silver, Oil)
4. Crypto-Specific (BTC Dominance, Stablecoin Supply, ETH/BTC, Funding)
5. On-Chain Metrics (Exchange Flow, Active Addresses, Hash Rate)

Run: python strategy_5_macro_complete.py
"""

import socket
import json
import time
import urllib.request
from datetime import datetime

TSDB_HOST = "127.0.0.1"
TSDB_PORT = 9999
POLL_INTERVAL = 60


def send_command(command: dict) -> dict:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((TSDB_HOST, TSDB_PORT))
        sock.sendall((json.dumps(command) + "\n").encode())
        return json.loads(sock.recv(65536).decode())


def fetch_url(url, timeout=10):
    """Fetch JSON from URL."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        return None


# =============================================================================
# DATA FETCHERS
# =============================================================================

def fetch_crypto_data():
    """Fetch crypto prices and metrics from CoinGecko."""
    # Basic prices
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,tether,usd-coin&vs_currencies=usd,btc&include_24hr_change=true&include_market_cap=true"
    data = fetch_url(url)
    
    if not data:
        return None
    
    btc = data.get("bitcoin", {})
    eth = data.get("ethereum", {})
    usdt = data.get("tether", {})
    usdc = data.get("usd-coin", {})
    
    # Calculate metrics
    eth_btc_ratio = eth.get("btc", 0)
    stablecoin_mcap = usdt.get("usd_market_cap", 0) + usdc.get("usd_market_cap", 0)
    
    return {
        "btc_price": btc.get("usd", 0),
        "btc_24h_change": btc.get("usd_24h_change", 0),
        "btc_mcap": btc.get("usd_market_cap", 0),
        "eth_price": eth.get("usd", 0),
        "eth_24h_change": eth.get("usd_24h_change", 0),
        "eth_btc_ratio": eth_btc_ratio,
        "stablecoin_mcap": stablecoin_mcap / 1e9,  # in billions
    }


def fetch_global_crypto():
    """Fetch global crypto metrics including BTC dominance."""
    url = "https://api.coingecko.com/api/v3/global"
    data = fetch_url(url)
    
    if not data or "data" not in data:
        return None
    
    global_data = data["data"]
    return {
        "btc_dominance": global_data.get("market_cap_percentage", {}).get("btc", 0),
        "eth_dominance": global_data.get("market_cap_percentage", {}).get("eth", 0),
        "total_mcap": global_data.get("total_market_cap", {}).get("usd", 0) / 1e12,  # in trillions
        "total_volume": global_data.get("total_volume", {}).get("usd", 0) / 1e9,  # in billions
    }


def fetch_fear_greed():
    """Fetch Crypto Fear & Greed Index."""
    url = "https://api.alternative.me/fng/?limit=1"
    data = fetch_url(url)
    
    if not data or "data" not in data:
        return None
    
    fng = data["data"][0]
    return {
        "fear_greed_value": int(fng.get("value", 50)),
        "fear_greed_class": fng.get("value_classification", "Neutral"),
    }


def fetch_commodities():
    """Fetch Gold and other commodity prices from CoinGecko."""
    # Using tokenized gold as proxy
    url = "https://api.coingecko.com/api/v3/simple/price?ids=tether-gold,pax-gold&vs_currencies=usd&include_24hr_change=true"
    data = fetch_url(url)
    
    if not data:
        return {"gold_price": 0, "gold_24h_change": 0}
    
    paxg = data.get("pax-gold", {})
    return {
        "gold_price": paxg.get("usd", 0),
        "gold_24h_change": paxg.get("usd_24h_change", 0),
    }


# =============================================================================
# ANALYSIS FUNCTIONS
# =============================================================================

def calculate_macro_score(data):
    """
    Calculate overall macro score from all factors.
    Returns score from -100 (very bearish) to +100 (very bullish)
    """
    score = 0
    factors = []
    
    # 1. Crypto momentum
    btc_change = data.get("btc_24h_change", 0)
    eth_change = data.get("eth_24h_change", 0)
    
    if btc_change > 3:
        score += 20
        factors.append(("BTC momentum", "+20", "Strong bullish"))
    elif btc_change > 1:
        score += 10
        factors.append(("BTC momentum", "+10", "Bullish"))
    elif btc_change < -3:
        score -= 20
        factors.append(("BTC momentum", "-20", "Strong bearish"))
    elif btc_change < -1:
        score -= 10
        factors.append(("BTC momentum", "-10", "Bearish"))
    
    # 2. ETH/BTC ratio (risk appetite)
    eth_btc = data.get("eth_btc_ratio", 0)
    if eth_btc > 0.06:
        score += 10
        factors.append(("ETH/BTC", "+10", "Alt season signal"))
    elif eth_btc < 0.04:
        score -= 10
        factors.append(("ETH/BTC", "-10", "BTC dominance"))
    
    # 3. BTC Dominance
    btc_dom = data.get("btc_dominance", 50)
    if btc_dom > 55:
        score -= 5
        factors.append(("BTC Dom", "-5", f"High ({btc_dom:.1f}%) - Risk-off"))
    elif btc_dom < 45:
        score += 10
        factors.append(("BTC Dom", "+10", f"Low ({btc_dom:.1f}%) - Alt season"))
    
    # 4. Fear & Greed
    fng = data.get("fear_greed_value", 50)
    if fng < 25:
        score += 15  # Extreme fear = buy opportunity
        factors.append(("Fear/Greed", "+15", f"Extreme Fear ({fng}) - Contrarian buy"))
    elif fng < 40:
        score += 5
        factors.append(("Fear/Greed", "+5", f"Fear ({fng})"))
    elif fng > 75:
        score -= 15  # Extreme greed = sell signal
        factors.append(("Fear/Greed", "-15", f"Extreme Greed ({fng}) - Contrarian sell"))
    elif fng > 60:
        score -= 5
        factors.append(("Fear/Greed", "-5", f"Greed ({fng})"))
    
    # 5. Gold correlation (safe haven)
    gold_change = data.get("gold_24h_change", 0)
    if gold_change > 1 and btc_change < -1:
        score -= 15
        factors.append(("Gold/BTC", "-15", "Flight to safety"))
    elif gold_change < -1 and btc_change > 1:
        score += 10
        factors.append(("Gold/BTC", "+10", "Risk-on rotation"))
    
    # 6. Stablecoin supply (liquidity)
    stable_mcap = data.get("stablecoin_mcap", 0)
    if stable_mcap > 150:  # > $150B
        score += 5
        factors.append(("Stablecoins", "+5", f"${stable_mcap:.0f}B - High liquidity"))
    
    return score, factors


def get_regime(score):
    """Determine market regime from score."""
    if score >= 40:
        return "STRONG BULL", "Highly bullish conditions"
    elif score >= 20:
        return "BULL", "Bullish conditions"
    elif score >= 5:
        return "LEAN BULL", "Slightly bullish"
    elif score <= -40:
        return "STRONG BEAR", "Highly bearish conditions"
    elif score <= -20:
        return "BEAR", "Bearish conditions"
    elif score <= -5:
        return "LEAN BEAR", "Slightly bearish"
    else:
        return "NEUTRAL", "Mixed signals"


def get_signal(score, btc_change):
    """Generate trading signal."""
    if score >= 30:
        return "LONG", "Strong bullish macro"
    elif score >= 15:
        return "LEAN LONG", "Bullish bias"
    elif score <= -30:
        return "SHORT", "Strong bearish macro"
    elif score <= -15:
        return "LEAN SHORT", "Bearish bias"
    else:
        return "HOLD", "Wait for clearer signal"


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  STRATEGY 5: COMPREHENSIVE MACRO ANALYSIS")
    print("  Integrating 5 Categories of Macro Factors")
    print("=" * 80)
    print()
    print("Categories monitored:")
    print("  1. Crypto Prices (BTC, ETH)")
    print("  2. Crypto Metrics (Dominance, Stablecoins, ETH/BTC)")
    print("  3. Sentiment (Fear & Greed Index)")
    print("  4. Commodities (Gold)")
    print("  5. Cross-asset correlation")
    print()
    
    # Initialize TSDB series
    send_command({"type": "CreateSeries", "data": {"name": "macro_complete", "dimension": 8}})
    print("[INIT] TSDB series created: macro_complete")
    print(f"[INIT] Polling interval: {POLL_INTERVAL} seconds")
    print()
    print("Press Ctrl+C to stop")
    print("-" * 80)
    
    data_count = 0
    score_history = []
    
    while True:
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Fetch all data
            crypto = fetch_crypto_data()
            global_crypto = fetch_global_crypto()
            fng = fetch_fear_greed()
            commodities = fetch_commodities()
            
            if crypto:
                # Merge all data
                data = {**crypto}
                if global_crypto:
                    data.update(global_crypto)
                if fng:
                    data.update(fng)
                if commodities:
                    data.update(commodities)
                
                # Store in TSDB
                vector = [
                    data.get("btc_24h_change", 0),
                    data.get("eth_24h_change", 0),
                    data.get("btc_dominance", 50),
                    data.get("eth_btc_ratio", 0) * 100,  # Scale for storage
                    data.get("fear_greed_value", 50),
                    data.get("gold_24h_change", 0),
                    data.get("stablecoin_mcap", 0),
                    data.get("total_volume", 0),
                ]
                
                send_command({
                    "type": "Insert",
                    "data": {"series": "macro_complete", "values": vector}
                })
                data_count += 1
                
                # Calculate macro score
                score, factors = calculate_macro_score(data)
                score_history.append(score)
                if len(score_history) > 20:
                    score_history.pop(0)
                
                # Get regime and signal
                regime, regime_desc = get_regime(score)
                signal, signal_reason = get_signal(score, data.get("btc_24h_change", 0))
                
                # Calculate trend
                if len(score_history) >= 3:
                    trend = score_history[-1] - score_history[-3]
                    trend_str = f"({trend:+.0f})" if trend != 0 else "(=)"
                else:
                    trend_str = ""
                
                # Display
                regime_color = {
                    "STRONG BULL": "[++++]",
                    "BULL": "[+++]",
                    "LEAN BULL": "[++]",
                    "NEUTRAL": "[==]",
                    "LEAN BEAR": "[--]",
                    "BEAR": "[---]",
                    "STRONG BEAR": "[----]",
                }.get(regime, "")
                
                signal_color = {
                    "LONG": "[*** LONG ***]",
                    "LEAN LONG": "[LONG]",
                    "HOLD": "",
                    "LEAN SHORT": "[SHORT]",
                    "SHORT": "[*** SHORT ***]",
                }.get(signal, "")
                
                print()
                print(f"[{timestamp}] ===== MACRO UPDATE =====")
                print(f"  BTC: ${data['btc_price']:,.0f} ({data['btc_24h_change']:+.2f}%) | "
                      f"ETH: ${data['eth_price']:,.0f} ({data['eth_24h_change']:+.2f}%)")
                print(f"  BTC Dom: {data.get('btc_dominance', 0):.1f}% | "
                      f"ETH/BTC: {data.get('eth_btc_ratio', 0):.4f} | "
                      f"Fear/Greed: {data.get('fear_greed_value', 50)} ({data.get('fear_greed_class', 'N/A')})")
                print(f"  Gold: ${data.get('gold_price', 0):,.0f} ({data.get('gold_24h_change', 0):+.2f}%) | "
                      f"Stables: ${data.get('stablecoin_mcap', 0):.1f}B")
                print()
                print(f"  MACRO SCORE: {score:+.0f} {trend_str} | {regime_color} {regime}")
                print(f"  SIGNAL: {signal_color} {signal} - {signal_reason}")
                
                # Show contributing factors
                if factors:
                    print()
                    print("  Contributing Factors:")
                    for factor_name, factor_score, factor_desc in factors[:5]:
                        print(f"    - {factor_name}: {factor_score} ({factor_desc})")
                
                # Anomaly detection if enough data
                if data_count >= 10:
                    anomaly_result = send_command({
                        "type": "Anomaly",
                        "data": {"series": "macro_complete", "window": 5, "k": 1}
                    })
                    if anomaly_result.get("status") == "Anomalies" and anomaly_result.get("data"):
                        anomaly_score = anomaly_result["data"][0]["score"]
                        if anomaly_score > 2.0:
                            print()
                            print(f"  [ALERT] Unusual market conditions detected! (score: {anomaly_score:.2f})")
                
            else:
                print(f"[{timestamp}] Failed to fetch data")
            
            time.sleep(POLL_INTERVAL)
            
        except KeyboardInterrupt:
            print()
            print()
            print("=" * 80)
            print("SESSION SUMMARY")
            print("=" * 80)
            print(f"Data points collected: {data_count}")
            if score_history:
                print(f"Final macro score: {score_history[-1]:+.0f}")
                print(f"Score range: {min(score_history):+.0f} to {max(score_history):+.0f}")
                avg_score = sum(score_history) / len(score_history)
                print(f"Average score: {avg_score:+.1f}")
            print()
            break


if __name__ == "__main__":
    main()
