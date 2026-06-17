"""
Athena SCIP - API Gateway
Supply Chain Intelligence Platform - Production Ready
"""
import logging
import os
import csv
import io
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from supabase import create_client, Client
import yfinance as yf
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx

# Import Pydantic models
from models import (
    StandardResponse,
    EventResponse,
    EventsListResponse,
    RecommendationResponse,
    PriceResponse,
    CountryRiskResponse,
    HealthResponse
)

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
    _instance: Optional['SupabaseClient'] = None
    _client: Optional[Client] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, url: str, key: str, max_retries: int = 3):
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
    def get_client(self) -> Client:
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
    description="Supply Chain Intelligence Platform - Monitor markets, identify risks, and get actionable recommendations",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Athena SCIP Team",
        "email": "support@athena-scip.com",
    },
    license_info={
        "name": "Proprietary",
    }
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
# Helper Functions
# ============================================
def format_response(data: Any = None, error: str = None) -> StandardResponse:
    """Create a properly formatted API response"""
    if error:
        return StandardResponse(success=False, error=error)
    return StandardResponse(success=True, data=data)

# ============================================
# Root & Health
# ============================================
@app.get(
    "/",
    response_model=StandardResponse,
    summary="API Root",
    description="Returns API information and status"
)
async def root():
    return format_response({
        "service": "Athena SCIP API Gateway",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs",
        "redoc": "/redoc"
    })

@app.get(
    "/health",
    response_model=StandardResponse,
    summary="Health Check",
    description="Check API and database connectivity"
)
async def health_check():
    try:
        result = supabase.table("events").select("id", count="exact").limit(1).execute()
        db_status = True
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        db_status = False
    return format_response({
        "status": "healthy" if db_status else "degraded",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    })

# ============================================
# Events
# ============================================
@app.get(
    "/events",
    response_model=StandardResponse,
    summary="Get Events",
    description="Retrieve events with optional filtering and pagination"
)
async def get_events(
    event_type: Optional[str] = Query(None, description="Filter by event type (war, natural_disaster, strike, sanctions, pandemic, other)"),
    min_severity: Optional[int] = Query(None, ge=1, le=5, description="Minimum severity level (1-5)"),
    limit: int = Query(100, ge=1, le=500, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Pagination offset")
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

@app.get(
    "/events/summary",
    response_model=StandardResponse,
    summary="Events Summary",
    description="Get total count of events"
)
async def get_events_summary():
    try:
        result = supabase.table("events").select("id", count="exact").execute()
        return format_response({
            "total_events": result.count or 0,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return format_response(error=str(e))

# ============================================
# Commodities
# ============================================
@app.get(
    "/commodities",
    response_model=StandardResponse,
    summary="Get Commodities",
    description="Retrieve list of all commodities"
)
async def get_commodities():
    try:
        result = supabase.table("commodities").select("*").execute()
        return format_response({"commodities": result.data})
    except Exception as e:
        return format_response(error=str(e))

# ============================================
# Recommendations
# ============================================
@app.get(
    "/recommendations",
    response_model=StandardResponse,
    summary="Get Recommendations",
    description="Retrieve supply chain risk recommendations"
)
async def get_recommendations(
    limit: int = Query(50, ge=1, le=200, description="Number of recommendations to return")
):
    try:
        result = supabase.table("recommendations").select("*, events(*)").order("created_at", desc=True).limit(limit).execute()
        return format_response({
            "recommendations": result.data,
            "count": len(result.data),
            "limit": limit
        })
    except Exception as e:
        return format_response(error=str(e))

@app.get(
    "/recommendations/summary",
    response_model=StandardResponse,
    summary="Recommendations Summary",
    description="Get summary of recommendations by urgency"
)
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

@app.get(
    "/recommendations/improved",
    response_model=StandardResponse,
    summary="Enhanced Recommendations",
    description="Get AI-generated recommendations with mitigation actions"
)
async def get_improved_recommendations(
    limit: int = Query(6, ge=1, le=20, description="Number of recommendations to return")
):
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

@app.get(
    "/supplier/alternatives",
    response_model=StandardResponse,
    summary="Supplier Alternatives",
    description="Get alternative supplier recommendations"
)
async def get_supplier_alternatives():
    try:
        result = supabase.table("supplier_alternatives").select("*").execute()
        return format_response({"alternatives": result.data})
    except Exception:
        return format_response({"alternatives": []})

# ============================================
# Shipping & Weather
# ============================================
@app.get(
    "/shipping/disruptions",
    response_model=StandardResponse,
    summary="Shipping Disruptions",
    description="Get shipping route disruptions"
)
async def get_shipping_disruptions(
    status: Optional[str] = Query(None, description="Filter by status")
):
    try:
        query = supabase.table("shipping_disruptions").select("*").order("severity", desc=True)
        if status:
            query = query.eq("status", status)
        result = query.execute()
        return format_response({"disruptions": result.data, "count": len(result.data)})
    except Exception as e:
        return format_response(error=str(e))

@app.get(
    "/weather/alerts",
    response_model=StandardResponse,
    summary="Weather Alerts",
    description="Get severe weather alerts"
)
async def get_weather_alerts(
    severity_min: Optional[int] = Query(None, ge=1, le=5, description="Minimum severity level")
):
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
@app.get(
    "/prices/live",
    response_model=StandardResponse,
    summary="Live Prices",
    description="Get latest commodity prices from Supabase"
)
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

@app.get(
    "/prices/live-comprehensive",
    response_model=StandardResponse,
    summary="Comprehensive Live Prices",
    description="Get live commodity prices from Yahoo Finance with static fallback"
)
async def get_live_prices_comprehensive():
    tickers = {
        'Crude Oil': 'CL=F', 'Natural Gas': 'NG=F', 'Gold': 'GC=F',
        'Copper': 'HG=F', 'Corn': 'ZC=F', 'Wheat': 'ZW=F', 'Soybeans': 'ZS=F'
    }
    unit_map = {
        'Crude Oil': 'per barrel', 'Natural Gas': 'per MMBtu', 'Gold': 'per ounce',
        'Copper': 'per pound', 'Corn': 'per bushel', 'Wheat': 'per bushel', 'Soybeans': 'per bushel'
    }
    prices = []
    for name, ticker in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")
            if len(hist) >= 2:
                current = hist['Close'].iloc[-1]
                previous = hist['Close'].iloc[-2]
                change = ((current - previous) / previous) * 100
                prices.append({
                    "commodity_name": name,
                    "price_usd": round(current, 2),
                    "unit": unit_map[name],
                    "change_24h": round(change, 1),
                    "source": "Yahoo Finance"
                })
        except Exception as e:
            logger.error(f"Error fetching {name}: {e}")
    
    static_prices = [
        {"commodity_name": "Steel", "price_usd": 847.50, "unit": "per ton", "change_24h": -0.8, "source": "Static"},
        {"commodity_name": "Semiconductors", "price_usd": 1248.00, "unit": "per wafer", "change_24h": -0.2, "source": "Static"},
        {"commodity_name": "Lithium", "price_usd": 14750.00, "unit": "per ton", "change_24h": 1.5, "source": "Static"},
        {"commodity_name": "Nickel", "price_usd": 18450.00, "unit": "per ton", "change_24h": -0.5, "source": "Static"},
        {"commodity_name": "Iron Ore", "price_usd": 117.20, "unit": "per ton", "change_24h": -0.5, "source": "Static"}
    ]
    prices.extend(static_prices)
    return format_response({"prices": prices, "count": len(prices)})

# ============================================
# Country Risk
# ============================================
@app.get(
    "/country-risk/enhanced",
    response_model=StandardResponse,
    summary="Country Risk Analysis",
    description="Get comprehensive country risk scores based on events"
)
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
@app.get(
    "/trends/prices",
    response_model=StandardResponse,
    summary="Price Trends",
    description="Get historical commodity price trends"
)
async def get_price_trends(
    days: int = Query(14, ge=1, le=365, description="Number of days to analyze")
):
    try:
        result = supabase.table("price_history").select("*").limit(100).execute()
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
        for commodity in trends:
            trends[commodity].sort(key=lambda x: x["date"])
        return format_response({"trends": trends, "days": days})
    except Exception as e:
        logger.error(f"Price trends error: {e}")
        return format_response({"trends": {}})

@app.get(
    "/trends/risk",
    response_model=StandardResponse,
    summary="Risk Trends",
    description="Get historical country risk trends"
)
async def get_risk_trends(
    days: int = Query(14, ge=1, le=365, description="Number of days to analyze")
):
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
@app.get(
    "/events/export/csv",
    summary="Export Events CSV",
    description="Export events data as CSV file"
)
async def export_events_csv(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum number of events to export")
):
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