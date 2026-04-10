"""
Portfolio Analytics
===================
Calculates current asset class weights, sector exposures, and aggregate risk metrics.
"""

def generate_analytics_report(portfolio: dict) -> str:
    """
    Generate an analyst-grade text report of the portfolio's exposures.
    """
    total_usd = portfolio.get("total_portfolio_usd", 0.0)
    if total_usd == 0:
        return "Portfolio is currently empty. No analytics available."
        
    categories = {}
    for asset in portfolio.get("assets", []):
        cat = asset.get("category", "other")
        val = asset.get("total_usd", 0.0)
        categories[cat] = categories.get(cat, 0.0) + val
        
    lines = []
    lines.append("=" * 80)
    lines.append("PORTFOLIO ANALYTICS & EXPOSURE")
    lines.append("=" * 80)
    
    lines.append("\n[ASSET CLASS DIVERSIFICATION]")
    for cat, val in sorted(categories.items(), key=lambda item: item[1], reverse=True):
        weight = (val / total_usd) * 100
        # Determine strictness/warning
        warning = ""
        if weight >= 60:
            warning = " [WARNING: Extreme Concentration Risk]"
        elif weight >= 40:
            warning = " [NOTE: High Exposure]"
        elif weight <= 5:
            warning = " [NOTE: Minimal Exposure]"
            
        lines.append(f"  {cat.upper():<25}: {weight:>6.2f}% (Val: {val:,.2f} USD){warning}")
        
    # Risk calculation based on category weights
    equity_weight = categories.get("global_stocks_funds", 0) + categories.get("turkish_stocks_funds", 0)
    equity_pct = (equity_weight / total_usd) * 100
    
    cash_weight = categories.get("cash", 0)
    cash_pct = (cash_weight / total_usd) * 100
    
    metals_weight = categories.get("gold_silver", 0)
    metals_pct = (metals_weight / total_usd) * 100
    
    lines.append("\n[AGGREGATE METRICS]")
    lines.append(f"  Total Equities (Growth):     {equity_pct:>6.2f}%")
    lines.append(f"  Total Metals (Defensive):    {metals_pct:>6.2f}%")
    lines.append(f"  Total Cash (Liquidity):      {cash_pct:>6.2f}%")
    
    lines.append("\n[STRUCTURAL LEAN]")
    if equity_pct >= 70:
        lines.append("  Profile: Aggressive / Growth-Oriented (High Equity Exposure)")
    elif equity_pct <= 30 and metals_pct + cash_pct >= 50:
        lines.append("  Profile: Conservative / Capital Preservation (High Defensive Exposure)")
    else:
        lines.append("  Profile: Balanced / Moderate")
        
    if cash_pct < 5:
        lines.append("  Liquidity Warning: Low cash reserves available for deployment.")
        
    lines.append("=" * 80)
    return "\n".join(lines)
