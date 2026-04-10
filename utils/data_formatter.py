import json
import os
import random

def format_asset_data(ticker: str, data: dict) -> str:
    """Formats a single asset's dictionary into a concise string."""
    name = data.get("Name", "Unknown")
    
    # Extract key metrics safely
    price = data.get("Price", "N/A")
    pe = data.get("P/E Ratio", "N/A")
    roe = data.get("ROE", "N/A")
    ebitda = data.get("EBITDA", "N/A")
    div_yield = data.get("Dividend Yield", "N/A")
    
    # Build concise string
    metrics = []
    if price != "N/A": metrics.append(f"Price: {price}")
    if pe != "N/A": metrics.append(f"P/E: {pe}")
    if roe != "N/A": metrics.append(f"ROE: {roe}")
    if ebitda != "N/A": metrics.append(f"EBITDA: {ebitda}")
    if div_yield != "N/A": metrics.append(f"Div: {div_yield}")
    
    metrics_str = ", ".join(metrics)
    if not metrics_str:
        metrics_str = "No key metrics available"
        
    return f"{ticker} ({name}) - [{metrics_str}]"


def truncate_and_sample_financial_pool(pool_data_str: str, sample_ratio: float = 0.3) -> str:
    """
    Takes the raw JSON string of the financial pool, flattens it, 
    randomly samples a percentage of assets, and formats them as a concise string list.
    """
    try:
        pool_data = json.loads(pool_data_str)
    except json.JSONDecodeError:
        return "Error: Could not parse financial pool JSON data."

    all_assets = []
    
    # Flatten the categories
    assets_dict = pool_data.get("assets", {})
    if not isinstance(assets_dict, dict):
         return "Error: Invalid format in financial pool data."
         
    for category, tickers in assets_dict.items():
        if isinstance(tickers, dict):
            for ticker, data in tickers.items():
                formatted_str = format_asset_data(ticker, data)
                all_assets.append(f"[{category}] {formatted_str}")
    
    if not all_assets:
        return "No assets found in the financial pool."
        
    # Sample 30%
    sample_size = max(1, int(len(all_assets) * sample_ratio))
    sampled_assets = random.sample(all_assets, sample_size)
    
    # Build the final string
    output_lines = [
        f"--- RANDOMLY SAMPLED ASSETS (Showing {sample_size} of {len(all_assets)}) ---",
        "The following are example assets for investing you can specifically search them and select them for the portfolio.",
        "You need to search if the stock is aligned with our requirements and restrictions.",
        ""
    ]
    
    for asset in sorted(sampled_assets):
        output_lines.append(asset)
        
    return "\n".join(output_lines)
