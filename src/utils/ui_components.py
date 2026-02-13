"""
UI Components utility for rendering premium HTML elements in Streamlit
"""


def glass_card(content: str, title: str = None):
    """Wraps content in a glassmorphism container"""
    header = f"<h3>{title}</h3>" if title else ""
    return f"""
    <div class="glass-container">
        {header}
        {content}
    </div>
    """


def metric_grid(metrics: list):
    """
    Renders a grid of premium metrics
    metrics: list of dicts with {'label': str, 'value': str}
    """
    items = ""
    for m in metrics:
        items += f"""
        <div class="metric-box">
            <div class="metric-label">{m["label"]}</div>
            <div class="metric-value">{m["value"]}</div>
        </div>
        """
    return f"""<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px;">{items}</div>"""


def listing_card_html(
    title: str, price: str, img_url: str, url: str, sold: bool = False
):
    """Renders a premium eBay listing card"""
    status = "Vendido" if sold else "A la venta"
    return f"""
    <div class="listing-card">
        <img src="{img_url}" class="listing-img" onerror="this.src='https://via.placeholder.com/150?text=No+Image'">
        <div class="listing-info">
            <div class="badge {"badge-sell" if sold else "badge-buy"}">{status}</div>
            <h4>{title}</h4>
            <div class="listing-price">{price}</div>
            <a href="{url}" target="_blank" style="color: #00d4ff; text-decoration: none; font-size: 0.9rem; font-weight: 600;">Ver en eBay →</a>
        </div>
    </div>
    """


def live_ticker_html(player: str, card: str, price: str, time_str: str):
    """Renders a ticker item for the dashboard"""
    return f"""
    <div class="glass-container live-ticker-item" style="padding: 12px; margin-bottom: 8px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-weight: 600; color: white;">{player}</span>
                <span style="color: #94a3b8; font-size: 0.85rem;"> {card}</span>
            </div>
            <div style="text-align: right;">
                <div style="color: #00ff88; font-weight: 700;">{price}</div>
                <div style="color: #64748b; font-size: 0.75rem;">{time_str}</div>
            </div>
        </div>
    </div>
    """
