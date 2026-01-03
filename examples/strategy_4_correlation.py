"""
Strategy 4: Crypto-Gold Correlation Trading
Analyzes BTC-Gold relationship for risk-on/risk-off signals

Run: python strategy_4_correlation.py
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
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,tether-gold&vs_currencies=usd&include_24hr_change=true"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            return {
                "btc": data.get("bitcoin", {}).get("usd", 0),
                "btc_change": data.get("bitcoin", {}).get("usd_24h_change", 0),
                "eth": data.get("ethereum", {}).get("usd", 0),
                "eth_change": data.get("ethereum", {}).get("usd_24h_change", 0),
                "gold": data.get("tether-gold", {}).get("usd", 0),
                "gold_change": data.get("tether-gold", {}).get("usd_24h_change", 0),
            }
    except:
        return None


def calculate_correlation(x_values, y_values):
    """Calculate Pearson correlation coefficient."""
    if len(x_values) < 5:
        return None
    
    n = len(x_values)
    mean_x = sum(x_values) / n
    mean_y = sum(y_values) / n
    
    numerator = sum((x_values[i] - mean_x) * (y_values[i] - mean_y) for i in range(n))
    denom_x = sum((x - mean_x) ** 2 for x in x_values) ** 0.5
    denom_y = sum((y - mean_y) ** 2 for y in y_values) ** 0.5
    
    if denom_x == 0 or denom_y == 0:
        return 0
    
    return numerator / (denom_x * denom_y)


def analyze_regime(btc_change, gold_change, correlation):
    """
    Determine market regime based on BTC-Gold relationship.
    """
    if btc_change > 0.5 and gold_change < -0.1:
        return "RISK-ON", "BTC up, Gold down - Risk appetite increasing"
    
    elif btc_change < -0.5 and gold_change > 0.1:
        return "RISK-OFF", "BTC down, Gold up - Flight to safety"
    
    elif btc_change > 0.3 and gold_change > 0.3:
        return "LIQUIDITY EXPANSION", "Both rising - Money flowing into assets"
    
    elif btc_change < -0.3 and gold_change < -0.3:
        return "LIQUIDITY CONTRACTION", "Both falling - Cash is king"
    
    else:
        return "NEUTRAL", "No clear regime signal"


def get_trading_signal(regime, correlation, btc_change, gold_change, regime_history):
    """
    Generate trading signal based on regime and correlation.
    """
    # Count recent regimes
    if len(regime_history) >= 3:
        risk_on_count = sum(1 for r in regime_history[-5:] if r == "RISK-ON")
        risk_off_count = sum(1 for r in regime_history[-5:] if r == "RISK-OFF")
        liquidity_count = sum(1 for r in regime_history[-5:] if r == "LIQUIDITY EXPANSION")
    else:
        risk_on_count = risk_off_count = liquidity_count = 0
    
    # Strong correlation signals
    if correlation is not None:
        if correlation < -0.5:
            # Strong inverse correlation - classic risk-on/off dynamic
            if regime == "RISK-ON" and risk_on_count >= 2:
                return "LONG CRYPTO", f"Strong risk-on trend (correlation: {correlation:.2f})"
            elif regime == "RISK-OFF" and risk_off_count >= 2:
                return "SHORT CRYPTO", f"Strong risk-off trend (correlation: {correlation:.2f})"
        
        elif correlation > 0.5:
            # Positive correlation - unusual
            if regime == "LIQUIDITY EXPANSION" and liquidity_count >= 2:
                return "LONG BOTH", f"Liquidity wave (correlation: {correlation:.2f})"
            elif regime == "LIQUIDITY CONTRACTION":
                return "CASH", f"Deleveraging in progress (correlation: {correlation:.2f})"
    
    # Regime-based signals
    if regime == "RISK-ON":
        return "LEAN LONG", "Risk-on environment favors crypto"
    elif regime == "RISK-OFF":
        return "LEAN SHORT", "Risk-off environment, caution on crypto"
    elif regime == "LIQUIDITY EXPANSION":
        return "BULLISH", "Expanding liquidity supports all assets"
    elif regime == "LIQUIDITY CONTRACTION":
        return "BEARISH", "Contracting liquidity hurts all assets"
    
    return "HOLD", "Wait for clear regime signal"


def main():
    print("=" * 70)
    print("  STRATEGY 4: CRYPTO-GOLD CORRELATION TRADING")
    print("  Analyzes BTC-Gold relationship for macro signals")
    print("=" * 70)
    print()
    
    # Initialize series
    send_command({"type": "CreateSeries", "data": {"name": "macro_correlation", "dimension": 3}})
    print("[INIT] Series created: macro_correlation (BTC%, ETH%, Gold%)")
    print(f"[INIT] Polling interval: {POLL_INTERVAL} seconds")
    print()
    print("Press Ctrl+C to stop")
    print("-" * 70)
    
    data_count = 0
    btc_history = []
    gold_history = []
    regime_history = []
    
    while True:
        try:
            prices = fetch_prices()
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            if prices:
                # Insert data
                send_command({
                    "type": "Insert",
                    "data": {
                        "series": "macro_correlation",
                        "values": [prices["btc_change"], prices["eth_change"], prices["gold_change"]]
                    }
                })
                data_count += 1
                
                # Track history
                btc_history.append(prices["btc_change"])
                gold_history.append(prices["gold_change"])
                if len(btc_history) > 30:
                    btc_history.pop(0)
                    gold_history.pop(0)
                
                # Calculate rolling correlation
                correlation = calculate_correlation(btc_history[-20:], gold_history[-20:])
                
                # Determine regime
                regime, regime_desc = analyze_regime(
                    prices["btc_change"], 
                    prices["gold_change"],
                    correlation
                )
                regime_history.append(regime)
                if len(regime_history) > 10:
                    regime_history.pop(0)
                
                # Get trading signal
                signal, signal_reason = get_trading_signal(
                    regime, correlation, 
                    prices["btc_change"], prices["gold_change"],
                    regime_history
                )
                
                # Display
                regime_indicator = {
                    "RISK-ON": "[R+]",
                    "RISK-OFF": "[R-]",
                    "LIQUIDITY EXPANSION": "[L+]",
                    "LIQUIDITY CONTRACTION": "[L-]",
                    "NEUTRAL": "[==]"
                }.get(regime, "")
                
                signal_indicator = {
                    "HOLD": "",
                    "LEAN LONG": "[+]",
                    "LEAN SHORT": "[-]",
                    "BULLISH": "[++]",
                    "BEARISH": "[--]",
                    "LONG CRYPTO": "[LONG]",
                    "SHORT CRYPTO": "[SHORT]",
                    "LONG BOTH": "[LONG ALL]",
                    "CASH": "[CASH]"
                }.get(signal, "")
                
                corr_str = f"{correlation:.2f}" if correlation else "N/A"
                
                print(f"[{timestamp}] BTC: ${prices['btc']:,.0f} ({prices['btc_change']:+.2f}%) | "
                      f"Gold: ${prices['gold']:,.0f} ({prices['gold_change']:+.2f}%) | "
                      f"Corr: {corr_str} | {regime_indicator} {regime}")
                
                if signal not in ["HOLD", "NEUTRAL"]:
                    print(f"         Signal: {signal_indicator} {signal} - {signal_reason}")
                
                # Special alerts
                if correlation is not None and abs(correlation) > 0.7:
                    print(f"         [ALERT] Strong correlation detected: {correlation:.2f}")
                
                if regime in ["LIQUIDITY EXPANSION", "LIQUIDITY CONTRACTION"]:
                    print(f"         [MACRO] {regime_desc}")
                
            else:
                print(f"[{timestamp}] Failed to fetch prices")
            
            time.sleep(POLL_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n[STOP] Strategy stopped by user")
            
            # Print summary
            if btc_history and gold_history:
                final_corr = calculate_correlation(btc_history, gold_history)
                print()
                print("=" * 70)
                print("SESSION SUMMARY")
                print("=" * 70)
                print(f"Data points collected: {data_count}")
                print(f"Final BTC-Gold correlation: {final_corr:.3f}" if final_corr else "Insufficient data")
                print(f"Regime history: {' -> '.join(regime_history[-5:])}")
            break


if __name__ == "__main__":
    main()
