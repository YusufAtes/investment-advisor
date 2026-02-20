"""
Update Financial Pool
=====================
Script to update the financial data pool using yfinance. 
Gathers metrics such as EBITDA, P/E, ROE, and saves them to a json file
to be used by the Discussion and Decider agents.
"""

import os
import sys
import json
import yfinance as yf
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import PORTFOLIO_DIR

POOL_FILE = os.path.join(PORTFOLIO_DIR, "financial_pool.json")

# Core Assets the user is interested in (Shariah/participation compliant ideally, no Israel connection)
TICKERS_TO_TRACK = {
    "Global Stocks (Halal/Shariah, No Israel)": [
        "AAPL", "MSFT", "NVDA", "GOOGL", "AVGO", "TSLA", "LLY", "XOM", "JNJ", "MU", 
        "ABBV", "HD", "AMD", "CSCO", "MRK", "AMAT", "CVX", "QCOM", "TXN", "NOW", 
        "INTU", "IBM", "AMZN", "CRM", "ACN", "ADBE", "LRCX", "KLAC", "SNPS", "CDNS", 
        "PANW", "FTNT", "TMO", "DHR", "ABT", "PFE", "AMGN", "ISRG", "SYK", "VRTX", 
        "REGN", "BIIB", "LIN", "SHW", "ECL", "APD", "NEM", "FCX", "NUE", "ETN", 
        "EMR", "ROP", "PH", "TT", "CARR", "COP", "EOG", "SLB", "MPC", "PSX", 
        "VLO", "OXY", "HES", "ASML"
    ],
    "Global Funds / ETFs (Islamic)": ["HLAL", "SPUS", "ISUS.L", "SPSK", "UMMA"], 
    "Turkish Stocks (BIST Katilim)": [
        "THYAO.IS", "BIMAS.IS", "TUPRS.IS", "FROTO.IS", "ASELS.IS", "EREGL.IS", 
        "GUBRF.IS", "ENJSA.IS", "ISDMR.IS", "EKGYO.IS", "MPARK.IS", "ALCTL.IS", 
        "ALTNY.IS", "BANVT.IS", "TTRAK.IS", "TOASO.IS", "DOAS.IS", "KORDS.IS", 
        "SOKM.IS", "KRDMD.IS", "CIMSA.IS", "AKSA.IS", "VESBE.IS", "VESTL.IS", 
        "ARCLK.IS", "OTKAR.IS", "TUKAS.IS", "TATGD.IS", "PETKM.IS", "SASA.IS", 
        "HEKTS.IS", "KOZAL.IS", "KOZAA.IS", "IPEKE.IS", "YYLGD.IS", "ASTOR.IS", 
        "ALFAS.IS", "EUPWR.IS", "YEOTK.IS", "KMPUR.IS", "QUAGR.IS", "GWIND.IS", 
        "AYDEM.IS", "ODAS.IS", "CANTE.IS", "ZOREN.IS", "AKSEN.IS", "ENKAI.IS", 
        "TCELL.IS", "TTKOM.IS"
    ],
    "Turkish Funds (Participation)": ["ZPE", "KLU", "MAC", "KPC", "RBH", "HKH", "MPE", "MPS"],
    "Precious Metals / Commodities": ["GLD", "SLV", "IAU", "PPLT", "PALL"]
}

def safe_get(info_dict, keys, default="N/A"):
    """Safely get the first available key from the info dictionary."""
    for key in keys:
        if key in info_dict and info_dict[key] is not None:
            # Format numbers slightly
            val = info_dict[key]
            if isinstance(val, (int, float)):
                if val > 1_000_000_000:
                    return f"{val/1_000_000_000:.2f}B"
                elif val > 1_000_000:
                    return f"{val/1_000_000:.2f}M"
                return round(val, 2)
            return val
    return default

import concurrent.futures

def fetch_ticker_data(ticker):
    print(f"  Fetching {ticker}...")
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # We extract essential data
        price = safe_get(info, ['currentPrice', 'regularMarketPrice', 'previousClose'])
        if price == "N/A":
            price = safe_get(info, ['navPrice'])
        
        pe_ratio = safe_get(info, ['trailingPE', 'forwardPE'])
        roe = safe_get(info, ['returnOnEquity'])
        if roe != "N/A" and isinstance(roe, (float, int)):
            roe = f"{roe*100:.1f}%"
            
        ebitda = safe_get(info, ['ebitda'])
        div_yield = safe_get(info, ['dividendYield', 'trailingAnnualDividendYield'])
        if div_yield != "N/A" and isinstance(div_yield, (float, int)):
            div_yield = f"{div_yield*100:.2f}%"

        high52 = safe_get(info, ['fiftyTwoWeekHigh'])
        low52 = safe_get(info, ['fiftyTwoWeekLow'])
        range52 = f"{low52} - {high52}" if low52 != "N/A" and high52 != "N/A" else "N/A"

        return ticker, {
            "Name": safe_get(info, ['shortName', 'longName'], ticker),
            "Price": price,
            "P/E Ratio": pe_ratio,
            "ROE": roe,
            "EBITDA": ebitda,
            "Dividend Yield": div_yield,
            "52-Week Range": range52,
            "Industry": safe_get(info, ['industry', 'category'], "Unknown")
        }
    except Exception as e:
        print(f"    [!] Error fetching {ticker}: {e}")
        return ticker, {
            "Name": ticker,
            "Error": "Could not fetch data via yfinance."
        }

def update_pool():
    print("==================================================")
    print("UPDATING FINANCIAL POOL VIA YFINANCE (MULTI-THREADED)")
    print("==================================================")
    
    os.makedirs(PORTFOLIO_DIR, exist_ok=True)
    
    financial_data = {
        "metadata": {
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": "yfinance API",
            "asset_count": sum(len(tickers) for tickers in TICKERS_TO_TRACK.values())
        },
        "assets": {}
    }

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for category, tickers in TICKERS_TO_TRACK.items():
            print(f"\nProcessing Category: {category}")
            financial_data["assets"][category] = {}
            
            # Submit all tasks
            future_to_ticker = {executor.submit(fetch_ticker_data, t): t for t in tickers}
            
            for future in concurrent.futures.as_completed(future_to_ticker):
                ticker, data = future.result()
                financial_data["assets"][category][ticker] = data

    # Save to file
    with open(POOL_FILE, "w", encoding="utf-8") as f:
        json.dump(financial_data, f, indent=4)
        
    print(f"\\n[OK] Financial pool saved to: {POOL_FILE}")


if __name__ == "__main__":
    update_pool()
