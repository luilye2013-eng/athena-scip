"""
Commodity Price Fetcher - Multi-Source
Fetches prices from Yahoo Finance, Live-Rates.com, and other sources
"""
import aiohttp
import asyncio
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# ============================================
# COMMODITY PRICE CONFIGURATION
# ============================================

# Yahoo Finance ticker mapping
YAHOO_TICKERS = {
    "Crude Oil": "CL=F",
    "Natural Gas": "NG=F",
    "Gold": "GC=F",
    "Silver": "SI=F",
    "Copper": "HG=F",
    "Wheat": "ZW=F",
    "Corn": "ZC=F",
    "Soybeans": "ZS=F",
}

# Live-Rates.com symbols
LIVE_RATES_SYMBOLS = {
    "Crude Oil": "WTI",
    "Gold": "XAU",
    "Silver": "XAG",
    "Copper": "HG",
    "Natural Gas": "NG",
}

# ============================================
# YAHOO FINANCE
# ============================================

async def fetch_from_yahoo() -> Optional[List[Dict]]:
    """Fetch prices from Yahoo Finance"""
    import yfinance as yf
    prices = []
    try:
        for name, ticker in YAHOO_TICKERS.items():
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="1d")
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
                    if price and price > 0:
                        prices.append({
                            "commodity_name": name,
                            "price_usd": round(price, 2),
                            "unit": "per unit",
                            "change_24h": 0.0,
                            "source": "Yahoo Finance",
                            "data_type": "live"
                        })
                        logger.info(f"💰 Yahoo: {name} = ${price:.2f}")
            except Exception as e:
                logger.warning(f"⚠️ Yahoo: {name} error: {e}")
                continue
        return prices if prices else None
    except Exception as e:
        logger.error(f"❌ Yahoo Finance error: {e}")
        return None

# ============================================
# LIVE-RATES.COM
# ============================================

async def fetch_from_live_rates() -> Optional[List[Dict]]:
    """Fetch commodity prices from Live-Rates.com"""
    try:
        # Live-Rates.com free endpoint
        url = "https://www.live-rates.com/rates"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    prices = []
                    
                    for name, symbol in LIVE_RATES_SYMBOLS.items():
                        # Find the symbol in the response
                        for item in data:
                            if item.get('symbol') == symbol:
                                price = item.get('rate')
                                if price and price > 0:
                                    prices.append({
                                        "commodity_name": name,
                                        "price_usd": round(price, 2),
                                        "unit": "per unit",
                                        "change_24h": item.get('change', 0),
                                        "source": "Live-Rates.com",
                                        "data_type": "live"
                                    })
                                    logger.info(f"💰 Live-Rates: {name} = ${price:.2f}")
                                break
                    
                    return prices if prices else None
                else:
                    logger.warning(f"⚠️ Live-Rates.com returned status: {response.status}")
                    return None
    except asyncio.TimeoutError:
        logger.warning("⚠️ Live-Rates.com timeout")
        return None
    except Exception as e:
        logger.error(f"❌ Live-Rates.com error: {e}")
        return None

# ============================================
# PITH NETWORK (Future Integration)
# ============================================

async def fetch_from_pyth() -> Optional[List[Dict]]:
    """Fetch prices from Pyth Network (future integration)"""
    # TODO: Implement Pyth Network integration
    # See: https://docs.pyth.network/price-feeds/pro/pyth-terminal
    logger.info("📊 Pyth Network integration coming soon...")
    return None

# ============================================
# MAIN FETCH FUNCTION
# ============================================

async def fetch_commodity_prices() -> Dict[str, Any]:
    """
    Fetch commodity prices from multiple sources.
    Returns first successful source.
    """
    sources = [
        ("Yahoo Finance", fetch_from_yahoo),
        ("Live-Rates.com", fetch_from_live_rates),
        ("Pyth Network", fetch_from_pyth),
    ]
    
    for source_name, fetch_func in sources:
        try:
            logger.info(f"📡 Trying source: {source_name}...")
            prices = await fetch_func()
            if prices and len(prices) > 0:
                logger.info(f"✅ Success from {source_name}: {len(prices)} prices")
                return {
                    "prices": prices,
                    "source": source_name,
                    "count": len(prices)
                }
        except Exception as e:
            logger.warning(f"⚠️ {source_name} failed: {e}")
            continue
    
    # If all sources fail
    logger.warning("⚠️ All price sources failed")
    return {"prices": [], "source": "Unavailable", "count": 0}