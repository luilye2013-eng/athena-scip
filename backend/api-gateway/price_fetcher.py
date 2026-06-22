"""
Commodity Price Fetcher - Multi-Source
Fetches prices from Yahoo Finance, Live-Rates.com, and fallback
"""
import aiohttp
import asyncio
import logging
import yfinance as yf
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# ============================================
# COMMODITY PRICE CONFIGURATION
# ============================================

# Yahoo Finance ticker mapping - verified working tickers
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

# Reference prices from IMF Primary Commodity Markets
REFERENCE_PRICES = {
    "Crude Oil": 77.50,
    "Natural Gas": 3.28,
    "Gold": 2020.00,
    "Silver": 28.50,
    "Copper": 4.70,
    "Wheat": 249.00,
    "Corn": 198.00,
    "Soybeans": 425.00,
    "Steel": 847.50,
    "Iron Ore": 117.20,
    "Lithium": 14750.00,
    "Nickel": 18450.00,
    "Semiconductors": 1248.00,
    "Aluminum": 1.15,
    "Zinc": 1.35,
    "Lead": 0.95,
}

# ============================================
# YAHOO FINANCE
# ============================================

def fetch_from_yahoo_sync():
    """Fetch prices from Yahoo Finance (synchronous version for yfinance)"""
    prices = []
    for name, ticker in YAHOO_TICKERS.items():
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2d")
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
            else:
                logger.warning(f"⚠️ No data for {name} ({ticker})")
        except Exception as e:
            logger.warning(f"⚠️ Yahoo error for {name}: {e}")
            continue
    return prices

# ============================================
# LIVE-RATES.COM
# ============================================

async def fetch_from_live_rates():
    """Fetch commodity prices from Live-Rates.com"""
    try:
        url = "https://www.live-rates.com/rates"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    prices = []
                    for name, symbol in LIVE_RATES_SYMBOLS.items():
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
# MAIN FETCH FUNCTION
# ============================================

async def fetch_commodity_prices() -> Dict[str, Any]:
    """Fetch commodity prices from multiple sources."""
    all_prices = []
    sources_used = []
    
    # 1. Try Live-Rates.com first
    logger.info("📡 Trying Live-Rates.com...")
    live_rates_prices = await fetch_from_live_rates()
    if live_rates_prices and len(live_rates_prices) > 0:
        all_prices.extend(live_rates_prices)
        sources_used.append("Live-Rates.com")
        logger.info(f"✅ Live-Rates.com returned {len(live_rates_prices)} prices")
    
    # 2. Try Yahoo Finance (sync - run in thread pool)
    if len(all_prices) < 8:  # Only try Yahoo if we need more
        logger.info("📡 Trying Yahoo Finance...")
        try:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                yahoo_prices = await asyncio.get_event_loop().run_in_executor(
                    executor, fetch_from_yahoo_sync
                )
                if yahoo_prices and len(yahoo_prices) > 0:
                    # Merge with existing, avoiding duplicates
                    existing_names = {p["commodity_name"] for p in all_prices}
                    for p in yahoo_prices:
                        if p["commodity_name"] not in existing_names:
                            all_prices.append(p)
                            sources_used.append("Yahoo Finance")
                    logger.info(f"✅ Yahoo returned {len(yahoo_prices)} prices")
        except Exception as e:
            logger.warning(f"⚠️ Yahoo error: {e}")
    
    # 3. Fill missing commodities with reference prices
    existing_names = {p["commodity_name"] for p in all_prices}
    for name, price in REFERENCE_PRICES.items():
        if name not in existing_names:
            all_prices.append({
                "commodity_name": name,
                "price_usd": price,
                "unit": "per unit",
                "change_24h": 0.0,
                "source": "IMF Reference",
                "data_type": "reference"
            })
            logger.info(f"📊 Using reference price for {name}: ${price}")
    
    logger.info(f"💰 Total {len(all_prices)} prices from sources: {sources_used}")
    
    return {
        "prices": all_prices,
        "source": sources_used[0] if sources_used else "IMF Reference",
        "count": len(all_prices)
    }