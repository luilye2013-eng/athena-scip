"""
Athena SCIP - API Gateway
Supply Chain Intelligence Platform - Production Ready
"""
import logging
import os
import csv
import io
import asyncio
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from supabase import create_client, Client
import yfinance as yf
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx
from .commodities import FALLBACK_PRICES
from .price_fetcher import fetch_commodity_prices, REFERENCE_PRICES

# ============================================
# Logging Setup
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# Configuration
# ============================================
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://catpprgdbvenutyyjqbx.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "sb_publishable_ykiqckKEQw2m8XXvX4cGnQ_5ijzb7Py")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080").split(",")

# ============================================
# Supabase Client
# ============================================
class SupabaseClient:
    _instance = None
    _client = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, url, key, max_retries=3):
        if self._client is None:
            self.url = url
            self.key = key
            self.max_retries = max_retries
            self._initialize_client()

    def _initialize_client(self):
        try:
            self._client = create_client(self.url, self.key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.ReadTimeout, httpx.ConnectTimeout, httpx.ConnectError))
    )
    def get_client(self):
        if not self._client:
            self._initialize_client()
        return self._client

# ============================================
# Initialize Supabase
# ============================================
try:
    supabase_client = SupabaseClient(SUPABASE_URL, SUPABASE_KEY)
    supabase = supabase_client.get_client()
    logger.info("✅ Supabase client initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize Supabase client: {e}")
    raise

# ============================================
# FastAPI App
# ============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Athena SCIP API Gateway v2.0...")
    yield
    logger.info("Shutting down Athena SCIP API Gateway...")

app = FastAPI(
    title="Athena SCIP API Gateway",
    description="Supply Chain Intelligence Platform",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Helper Function
# ============================================
def format_response(data=None, error=None):
    if error:
        return {"success": False, "error": error, "timestamp": datetime.utcnow().isoformat()}
    return {"success": True, "data": data, "timestamp": datetime.utcnow().isoformat()}

# ============================================
# Root & Health
# ============================================
@app.get("/")
async def root():
    return format_response({
        "service": "Athena SCIP API Gateway",
        "version": "2.0.0",
        "status": "operational"
    })

@app.get("/health")
async def health_check():
    try:
        result = supabase.table("events").select("id", count="exact").limit(1).execute()
        db_status = True
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        db_status = False
    return format_response({
        "status": "healthy" if db_status else "degraded",
        "database": db_status
    })

# ============================================
# Events
# ============================================
@app.get("/events")
async def get_events(
    event_type: Optional[str] = None,
    min_severity: Optional[int] = None,
    limit: int = 100,
    offset: int = 0
):
    try:
        query = supabase.table("events").select("*").order("created_at", desc=True)
        if event_type and event_type != "all":
            query = query.eq("event_type", event_type)
        if min_severity:
            query = query.gte("severity", min_severity)
        query = query.range(offset, offset + limit - 1)
        result = query.execute()
        return format_response({
            "events": result.data,
            "count": len(result.data),
            "limit": limit,
            "offset": offset
        })
    except Exception as e:
        logger.error(f"Events error: {e}")
        return format_response(error=str(e))

@app.get("/events/summary")
async def get_events_summary():
    try:
        result = supabase.table("events").select("id", count="exact").execute()
        return format_response({"total_events": result.count or 0})
    except Exception as e:
        return format_response(error=str(e))

# ============================================
# Commodities
# ============================================
@app.get("/commodities")
async def get_commodities():
    try:
        result = supabase.table("commodities").select("*").execute()
        return format_response({"commodities": result.data})
    except Exception as e:
        return format_response(error=str(e))

# ============================================
# COMMODITY PRICE CONFIGURATION
# ============================================

# Reference prices from IMF Primary Commodity Markets (last known values)
# These are clearly labeled as REFERENCE prices, not live
REFERENCE_PRICES = {
    "Crude Oil": {"price": 77.50, "unit": "per barrel", "source": "IMF Reference"},
    "Natural Gas": {"price": 3.28, "unit": "per MMBtu", "source": "IMF Reference"},
    "Gold": {"price": 2020.00, "unit": "per ounce", "source": "IMF Reference"},
    "Silver": {"price": 28.50, "unit": "per ounce", "source": "IMF Reference"},
    "Copper": {"price": 4.70, "unit": "per pound", "source": "IMF Reference"},
    "Wheat": {"price": 249.00, "unit": "per bushel", "source": "IMF Reference"},
    "Corn": {"price": 198.00, "unit": "per bushel", "source": "IMF Reference"},
    "Soybeans": {"price": 425.00, "unit": "per bushel", "source": "IMF Reference"},
    "Steel": {"price": 847.50, "unit": "per ton", "source": "IMF Reference"},
    "Iron Ore": {"price": 117.20, "unit": "per ton", "source": "IMF Reference"},
    "Lithium": {"price": 14750.00, "unit": "per ton", "source": "IMF Reference"},
    "Nickel": {"price": 18450.00, "unit": "per ton", "source": "IMF Reference"},
    "Semiconductors": {"price": 1248.00, "unit": "per wafer", "source": "IMF Reference"},
}

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

async def fetch_from_yahoo():
    """Fetch prices from Yahoo Finance"""
    prices = []
    try:
        for name, ticker in YAHOO_TICKERS.items():
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="1d")
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
                    if price > 0:
                        prices.append({
                            "commodity_name": name,
                            "price_usd": round(price, 2),
                            "unit": "per unit",
                            "change_24h": 0.0,
                            "source": "Yahoo Finance",
                            "data_type": "live"
                        })
            except Exception as e:
                continue
        return prices if prices else None
    except Exception as e:
        return None
# ============================================
# Recommendations
# ============================================
@app.get("/recommendations")
async def get_recommendations(limit: int = 50):
    try:
        result = supabase.table("recommendations").select("*, events(*)").order("created_at", desc=True).limit(limit).execute()
        return format_response({"recommendations": result.data, "count": len(result.data)})
    except Exception as e:
        return format_response(error=str(e))

@app.get("/recommendations/summary")
async def get_recommendations_summary():
    try:
        result = supabase.table("recommendations").select("urgency, id").execute()
        urgency_counts = {}
        for rec in result.data:
            urgency = rec.get("urgency", "unknown")
            urgency_counts[urgency] = urgency_counts.get(urgency, 0) + 1
        return format_response({
            "total_recommendations": len(result.data),
            "by_urgency": urgency_counts
        })
    except Exception as e:
        return format_response(error=str(e))

@app.get("/recommendations/improved")
async def get_improved_recommendations(limit: int = 6):
    try:
        events = supabase.table("events").select("*").gte("severity", 3).order("severity", desc=True).limit(limit).execute()
        recommendations = []
        for event in events.data:
            event_type = event.get("event_type", "other")
            severity = event.get("severity", 0)
            title = event.get("title", "")
            country = event.get("location_country") or "unknown"
            if event_type == "war" and severity >= 4:
                actions = [
                    f"Activate business continuity plan for {country}",
                    f"Increase inventory buffer by 60 days",
                    "Reroute shipments away from conflict zone",
                    "Identify alternative suppliers"
                ]
                affected = ["Wheat", "Natural Gas", "Oil", "Steel"]
            elif event_type == "natural_disaster" and severity >= 4:
                actions = [
                    f"Contact suppliers in {country} immediately",
                    "Expedite pending orders",
                    "Activate alternative routes",
                    "Review disaster recovery"
                ]
                affected = ["Semiconductors", "Lithium", "Wheat"]
            else:
                actions = ["Monitor situation", "Review inventory", "Prepare alternatives"]
                affected = ["General"]
            recommendations.append({
                "event_title": title[:100],
                "severity": severity,
                "urgency": "immediate" if severity >= 4 else "short_term",
                "actions": actions,
                "affected_commodities": affected
            })
        return format_response({"recommendations": recommendations})
    except Exception as e:
        return format_response(error=str(e))

@app.get("/supplier/alternatives")
async def get_supplier_alternatives():
    try:
        result = supabase.table("supplier_alternatives").select("*").execute()
        return format_response({"alternatives": result.data})
    except Exception:
        return format_response({"alternatives": []})

# ============================================
# Shipping & Weather
# ============================================
@app.get("/shipping/disruptions")
async def get_shipping_disruptions(status: Optional[str] = None):
    try:
        query = supabase.table("shipping_disruptions").select("*").order("severity", desc=True)
        if status:
            query = query.eq("status", status)
        result = query.execute()
        return format_response({"disruptions": result.data, "count": len(result.data)})
    except Exception as e:
        return format_response(error=str(e))

@app.get("/weather/alerts")
async def get_weather_alerts(severity_min: Optional[int] = None):
    try:
        query = supabase.table("weather_alerts").select("*").order("severity", desc=True)
        if severity_min:
            query = query.gte("severity", severity_min)
        result = query.execute()
        return format_response({"alerts": result.data, "count": len(result.data)})
    except Exception as e:
        return format_response(error=str(e))

# ============================================
# Prices
# ============================================
@app.get("/prices/live")
async def get_live_prices():
    try:
        result = supabase.table("live_commodity_prices").select("*").order("recorded_at", desc=True).execute()
        latest = {}
        for price in result.data:
            if price["commodity_name"] not in latest:
                latest[price["commodity_name"]] = price
        return format_response({"prices": list(latest.values())})
    except Exception as e:
        return format_response(error=str(e))

@app.get("/prices/live-comprehensive")
async def get_live_prices_comprehensive():
    """
    Get commodity prices with clear source labeling.
    Returns ALL commodities with reference prices if live data unavailable.
    """
    result = await fetch_commodity_prices()
    
    if result["prices"] and len(result["prices"]) > 0:
        return format_response({
            "prices": result["prices"],
            "count": result["count"],
            "data_source": result["source"] + (" (Live)" if result["source"] != "IMF Reference" else " (Reference)"),
            "message": f"Prices fetched from {result['source']}"
        })
    
    # If still no prices, return empty
    return format_response({
        "prices": [],
        "count": 0,
        "data_source": "Unavailable",
        "message": "No commodity prices available"
    })

@app.post("/prices/refresh")
async def refresh_prices():
    """Force refresh commodity prices and update database"""
    try:
        logger.info("🔄 Refreshing commodity prices...")
        result = await fetch_commodity_prices()
        
        if result["prices"]:
            # Update live_commodity_prices table
            for price in result["prices"]:
                try:
                    # Check if exists
                    existing = supabase.table("live_commodity_prices") \
                        .select("id") \
                        .eq("commodity_name", price["commodity_name"]) \
                        .execute()
                    
                    if existing.data:
                        # Update
                        supabase.table("live_commodity_prices") \
                            .update({
                                "price_usd": price["price_usd"],
                                "source": price.get("source", "Unknown"),
                                "recorded_at": datetime.utcnow().isoformat()
                            }) \
                            .eq("commodity_name", price["commodity_name"]) \
                            .execute()
                    else:
                        # Insert
                        supabase.table("live_commodity_prices").insert({
                            "commodity_name": price["commodity_name"],
                            "price_usd": price["price_usd"],
                            "unit": price.get("unit", "per unit"),
                            "source": price.get("source", "Unknown"),
                            "recorded_at": datetime.utcnow().isoformat()
                        }).execute()
                except Exception as e:
                    logger.error(f"Error updating {price['commodity_name']}: {e}")
            
            return format_response({
                "status": "success",
                "message": f"Refreshed {len(result['prices'])} commodity prices",
                "count": len(result["prices"]),
                "source": result["source"]
            })
        else:
            return format_response({
                "status": "error",
                "message": "Failed to fetch prices from any source"
            }, error="No prices available")
            
    except Exception as e:
        logger.error(f"Refresh error: {e}")
        return format_response(error=str(e))
# ============================================
# Country Risk
# ============================================
@app.get("/country-risk/enhanced")
async def get_country_risk():
    try:
        events = supabase.table("events").select("location_country, event_type, severity").execute()
        country_data = {}
        for event in events.data:
            country = event.get("location_country")
            if not country or country in ["Unknown", "Unspecified Location", "N/A", "null"]:
                continue
            severity = event.get("severity", 0)
            event_type = event.get("event_type", "other")
            if country not in country_data:
                country_data[country] = {"total_events": 0, "war_count": 0, "disaster_count": 0, "severity_sum": 0}
            country_data[country]["total_events"] += 1
            country_data[country]["severity_sum"] += severity
            if event_type == "war":
                country_data[country]["war_count"] += 1
            elif event_type == "natural_disaster":
                country_data[country]["disaster_count"] += 1
        
        result = []
        for country, data in country_data.items():
            risk_score = min(100, (data["severity_sum"] * 2) + (data["war_count"] * 20))
            risk_level = "Critical" if risk_score >= 70 else "High" if risk_score >= 50 else "Medium" if risk_score >= 30 else "Low"
            result.append({
                "country": country,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "events": data["total_events"],
                "war": data["war_count"],
                "disaster": data["disaster_count"]
            })
        result.sort(key=lambda x: x["risk_score"], reverse=True)
        return format_response({"countries": result[:20]})
    except Exception as e:
        logger.error(f"Country risk error: {e}")
        return format_response(error=str(e))

# ============================================
# Trends
# ============================================
@app.get("/trends/prices")
async def get_price_trends(days: int = 14):
    try:
        # Calculate date range
        from datetime import datetime, timedelta
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        result = supabase.table("price_history") \
            .select("*") \
            .gte("recorded_date", cutoff_date) \
            .order("recorded_date", desc=True) \
            .limit(days * 20) \
            .execute()
        
        if not result.data:
            return format_response({
                "trends": {},
                "days": days,
                "message": "No price history available yet. Data is being collected."
            })

        # Process data
        trends = {}
        for item in result.data:
            commodity = item.get("commodity_name")
            if commodity:
                if commodity not in trends:
                    trends[commodity] = []
                trends[commodity].append({
                    "date": item.get("recorded_date"),
                    "price": float(item.get("price_usd", 0))
                })

        # Sort and limit per commodity
        for commodity in trends:
            trends[commodity].sort(key=lambda x: x["date"])
            trends[commodity] = trends[commodity][-days:]

        return format_response({"trends": trends, "days": days})

    except Exception as e:
        logger.error(f"Price trends error: {e}")
        return format_response(error=str(e))

@app.get("/trends/risk")
async def get_risk_trends(days: int = 14):
    try:
        result = supabase.table("risk_history").select("*").limit(100).execute()
        trends = {}
        for item in result.data:
            country = item.get("country_name")
            if country:
                if country not in trends:
                    trends[country] = []
                trends[country].append({
                    "date": item.get("recorded_date"),
                    "risk": float(item.get("risk_score", 0))
                })
        for country in trends:
            trends[country].sort(key=lambda x: x["date"])
        return format_response({"trends": trends, "days": days})
    except Exception as e:
        logger.error(f"Risk trends error: {e}")
        return format_response({"trends": {}})

# ============================================
# Export CSV
# ============================================
@app.get("/events/export/csv")
async def export_events_csv(event_type: Optional[str] = None, limit: int = 1000):
    try:
        query = supabase.table("events").select("*").order("created_at", desc=True).limit(limit)
        if event_type:
            query = query.eq("event_type", event_type)
        result = query.execute()
        events = result.data
        if not events:
            return JSONResponse(status_code=404, content={"error": "No events to export"})
        
        output = io.StringIO()
        writer = csv.writer(output)
        headers = ["id", "title", "event_type", "severity", "location_country", "location_city", "source", "created_at"]
        writer.writerow(headers)
        for event in events:
            writer.writerow([event.get(k, "") for k in headers])
        
        response = StreamingResponse(iter([output.getvalue()]), media_type="text/csv")
        response.headers["Content-Disposition"] = f"attachment; filename=events_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        return response
    except Exception as e:
        logger.error(f"CSV export error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# ============================================
# Main Entry
# ============================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)