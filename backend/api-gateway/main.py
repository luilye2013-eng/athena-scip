"""
Athena SCIP - API Gateway
Supply Chain Intelligence Platform - Production Ready (Single File)
"""
import logging
import os
import csv
import io
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from supabase import create_client, Client
import yfinance as yf
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx
from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime

# ============================================
# Pydantic Response Models (Fix Swagger)
# ============================================
class EventResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    event_type: str
    severity: int
    location_country: Optional[str] = None
    location_city: Optional[str] = None
    created_at: str
    confidence_score: Optional[float] = None

class RecommendationResponse(BaseModel):
    id: str
    action_type: str
    urgency: str
    commodity_id: Optional[str] = None
    supplier_id: Optional[str] = None
    estimated_cost_impact: Optional[float] = None

class PriceResponse(BaseModel):
    commodity_name: str
    price_usd: float
    unit: str
    change_24h: float
    source: str

class CountryRiskResponse(BaseModel):
    country: str
    risk_score: int
    risk_level: str
    events: int
    war: int
    disaster: int

class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

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
# Load environment variables
load_dotenv()

# ============================================
# Configuration from Environment Variables
# ============================================
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://catpprgdbvenutyyjqbx.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "sb_publishable_ykiqckKEQw2m8XXvX4cGnQ_5ijzb7Py")
logger.info(f"SUPABASE_URL: {SUPABASE_URL}")
logger.info(f"SUPABASE_KEY exists: {SUPABASE_KEY is not None}")
logger.info(f"SUPABASE_KEY length: {len(SUPABASE_KEY) if SUPABASE_KEY else 0}")
if SUPABASE_KEY:
    logger.info(f"SUPABASE_KEY first 20 chars: {SUPABASE_KEY[:20]}")
    logger.info(f"SUPABASE_KEY repr: {repr(SUPABASE_KEY)}")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080").split(",")

# Use service key for admin operations if available
SUPABASE_KEY_TO_USE = SUPABASE_SERVICE_KEY if SUPABASE_SERVICE_KEY else SUPABASE_KEY

# ============================================
# Supabase Client Class (Directly in main.py)
# ============================================
class SupabaseClient:
    """Thread-safe Supabase client with retry logic"""

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
        """Initialize the Supabase client with retry options"""
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
    def query(self, table: str, operation: str, **kwargs) -> Any:
        """
        Execute a query with automatic retry on failure

        Args:
            table: Table name
            operation: 'select', 'insert', 'update', 'delete'
            **kwargs: Query parameters

        Returns:
            Query result
        """
        if not self._client:
            self._initialize_client()

        try:
            query = self._client.table(table)

            if operation == 'select':
                result = query.select(kwargs.get('columns', '*'))
                if kwargs.get('limit'):
                    result = result.limit(kwargs['limit'])
                if kwargs.get('offset'):
                    result = result.offset(kwargs['offset'])
                if kwargs.get('order_by'):
                    result = result.order(kwargs['order_by'], desc=kwargs.get('desc', True))
                if kwargs.get('filters'):
                    for key, value in kwargs['filters'].items():
                        result = result.eq(key, value)
                return result.execute()

            elif operation == 'insert':
                return query.insert(kwargs.get('data', [])).execute()

            elif operation == 'update':
                return query.update(kwargs.get('data', {})).eq(kwargs.get('eq_field', 'id'), kwargs.get('eq_value')).execute()

            elif operation == 'delete':
                if kwargs.get('filters'):
                    for key, value in kwargs['filters'].items():
                        query = query.eq(key, value)
                return query.delete().execute()

            else:
                raise ValueError(f"Unsupported operation: {operation}")

        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise

    def get_client(self) -> Client:
        """Return the underlying Supabase client"""
        if not self._client:
            self._initialize_client()
        return self._client

# ============================================
# Initialize Supabase Client
# ============================================
supabase_client = SupabaseClient(SUPABASE_URL, SUPABASE_KEY)
try:
    supabase_client = SupabaseClient(SUPABASE_URL, SUPABASE_KEY)
    supabase = supabase_client.get_client()
    logger.info("✅ Supabase client initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize Supabase client: {e}")
    logger.error(f"URL: {SUPABASE_URL}")
    logger.error(f"Key length: {len(SUPABASE_KEY) if SUPABASE_KEY else 0}")
    raise
supabase = supabase_client.get_client()

# ============================================
# Pydantic Models (Validation)
# ============================================
class EventFilter(BaseModel):
    event_type: Optional[str] = Field(None, description="Filter by event type")
    min_severity: Optional[int] = Field(None, ge=1, le=5)
    limit: int = Field(100, ge=1, le=500)
    offset: int = Field(0, ge=0)

# ============================================
# FastAPI Application
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
    docs_url="/docs"
)

# ============================================
# CORS Configuration
# ============================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    max_age=3600,
)

# ============================================
# Helper Functions
# ============================================
def format_response(data: Any = None, error: str = None) -> dict:
    if error:
        return {"success": False, "error": error, "timestamp": datetime.utcnow().isoformat()}
    return {"success": True, "data": data, "timestamp": datetime.utcnow().isoformat()}

# ============================================
# Root & Health Endpoints
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
    return format_response({"status": "healthy" if db_status else "degraded", "database": db_status})

@app.get("/")
async def root():
    return format_response({...})

@app.get("/health")
async def health_check():
    return format_response({...})

@app.get("/events", response_model=APIResponse)
async def get_events(...):
    # existing code

@app.get("/recommendations", response_model=APIResponse)
async def get_recommendations(...):
    # existing code

@app.get("/prices/live", response_model=APIResponse)
async def get_live_prices():
    # existing code

@app.get("/country-risk/enhanced", response_model=APIResponse)
async def get_country_risk():
    # existing code
# ============================================
# Events Endpoints
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
# Commodities Endpoint
# ============================================
@app.get("/commodities")
async def get_commodities():
    try:
        result = supabase.table("commodities").select("*").execute()
        return format_response({"commodities": result.data})
    except Exception as e:
        return format_response(error=str(e))

# ============================================
# Recommendations Endpoints
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
# Shipping & Weather Endpoints
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
# Commodity Prices (Live)
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
# Country Risk & Trends
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

@app.get("/trends/prices")
async def get_price_trends(days: int = 14):
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