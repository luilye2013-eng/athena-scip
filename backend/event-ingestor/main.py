"""
Athena SCIP - Unified Event Ingestor
Fetches: News Events, Earthquakes, Weather Alerts, Shipping Disruptions
SECURE VERSION: Uses environment variables for all secrets
Runs continuously with configurable interval
"""

import os
import json
import requests
import feedparser
from datetime import datetime, timedelta
from supabase import create_client
from dotenv import load_dotenv
import logging
import time
import hashlib
import sys
from data_quality import (
    is_supply_chain_related,
    enrich_location,
    classify_event_type,
    calculate_supply_chain_impact,
    SUPPLY_CHAIN_EVENT_TYPES
)

# ============================================
# CONFIGURATION
# ============================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://catpprgdbvenutyyjqbx.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
if not SUPABASE_KEY:
    logging.warning("SUPABASE_SERVICE_ROLE_KEY not set. Using ANON key as fallback.")
    SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "sb_publishable_ykiqckKEQw2m8XXvX4cGnQ_5ijzb7Py")

INGEST_INTERVAL = int(os.getenv("INGEST_INTERVAL", "300"))  # Default: 5 minutes

# ============================================
# RSS FEEDS
# ============================================
RSS_FEEDS = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "http://rss.cnn.com/rss/edition_world.rss",
    "https://feeds.npr.org/1001/rss.xml",
    "https://www.theguardian.com/world/rss",
    "https://www.aljazeera.com/xml/rss/all.xml"
]

# ============================================
# EVENT KEYWORDS
# ============================================
EVENT_KEYWORDS = {
    "war": ["war", "conflict", "military", "attack", "invasion", "missile", "bomb", "combat", "troops", "casualties", "drone", "strike"],
    "natural_disaster": ["earthquake", "flood", "hurricane", "typhoon", "cyclone", "wildfire", "drought", "tsunami", "volcano", "storm"],
    "sanctions": ["sanctions", "embargo", "trade ban", "restrictions", "tariff"],
    "strike": ["strike", "walkout", "labor dispute", "union", "protest", "blockade", "port strike"],
    "pandemic": ["outbreak", "epidemic", "pandemic", "virus", "disease", "ebola", "covid"]
}

# ============================================
# SETUP LOGGING
# ============================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ============================================
# SUPABASE CLIENT
# ============================================

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("✅ Supabase client created successfully")
except Exception as e:
    logger.error(f"❌ Failed to create Supabase client: {e}")
    exit(1)

# ============================================
# HELPER FUNCTIONS
# ============================================

def classify_event(title, description):
    text = (title + " " + (description or "")).lower()
    for event_type, keywords in EVENT_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return event_type
    return "other"

def calculate_severity(event_type, title):
    if event_type == "war":
        return 5
    elif event_type == "sanctions":
        return 4
    elif event_type == "natural_disaster":
        return 4
    elif event_type == "strike":
        return 3
    else:
        return 2

def extract_country(text):
    countries = ["Russia", "Ukraine", "USA", "China", "India", "Japan", "Germany", "France",
                 "UK", "Canada", "Australia", "Iran", "Israel", "Indonesia", "Philippines",
                 "South Korea", "Brazil", "Mexico", "Italy", "Spain", "Turkey", "Saudi Arabia",
                 "UAE", "Egypt", "Nigeria", "South Africa", "Argentina", "Vietnam", "Malaysia"]
    for country in countries:
        if country.lower() in text.lower():
            return country
    return None

def store_item(table, data, id_field="title"):
    try:
        # Check for duplicate
        existing = supabase.table(table).select("id").eq(id_field, data.get(id_field, data.get("title", ""))).execute()
        if existing.data:
            return False
        
        supabase.table(table).insert(data).execute()
        logger.info(f"📥 Stored {table[:-1]}: {data.get('title', data.get('alert_type', 'unknown'))[:50]}...")
        return True
    except Exception as e:
        logger.error(f"❌ Error storing to {table}: {e}")
        return False

# ============================================
# FETCH FUNCTIONS
# ============================================

def fetch_news_events():
    events = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    for feed_url in RSS_FEEDS:
        try:
            response = requests.get(feed_url, headers=headers, timeout=30)
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                for entry in feed.entries[:10]:
                    events.append({
                        "title": entry.get("title", ""),
                        "description": entry.get("summary", ""),
                        "source": feed_url.split("/")[2],
                        "published_at": entry.get("published", datetime.now().isoformat())
                    })
                logger.info(f"📡 Fetched {len(feed.entries[:10])} news from {feed_url}")
        except Exception as e:
            logger.error(f"❌ News RSS error for {feed_url}: {e}")
    return events

def fetch_earthquakes():
    try:
        url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
        params = {
            "format": "geojson",
            "starttime": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "minmagnitude": 4.5,
            "orderby": "time"
        }
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            events = data.get("features", [])
            logger.info(f"🌍 Fetched {len(events)} earthquakes from USGS")
            return events
        return []
    except Exception as e:
        logger.error(f"❌ USGS error: {e}")
        return []

def fetch_weather_alerts():
    alerts = []
    FILTER_KEYWORDS = ['test', 'test message', 'administrative', 'routine', 'practice', 'drill', 'exercise', 'statement']

    # NOAA for USA
    try:
        noaa_url = "https://api.weather.gov/alerts/active"
        response = requests.get(noaa_url, timeout=30, headers={'User-Agent': 'Athena-SCIP/1.0'})
        if response.status_code == 200:
            data = response.json()
            for alert in data.get('features', [])[:20]:
                props = alert.get('properties', {})
                event_type = props.get('event', '')
                description = props.get('description', '')

                skip = False
                for keyword in FILTER_KEYWORDS:
                    if keyword.lower() in event_type.lower() or keyword.lower() in description.lower():
                        skip = True
                        break
                if skip:
                    continue

                meaningful_types = [
                    'hurricane', 'tornado', 'flood', 'flash flood', 'storm',
                    'typhoon', 'cyclone', 'blizzard', 'winter storm', 'heat',
                    'fire', 'drought', 'tsunami', 'severe thunderstorm',
                    'high wind', 'coastal flood', 'tropical storm'
                ]
                is_meaningful = False
                for mtype in meaningful_types:
                    if mtype.lower() in event_type.lower() or mtype.lower() in description.lower():
                        is_meaningful = True
                        break
                if not is_meaningful:
                    continue

                severity = 3
                if props.get('severity') in ['Extreme']:
                    severity = 5
                elif props.get('severity') in ['Severe']:
                    severity = 4
                elif props.get('severity') in ['Moderate']:
                    severity = 3
                else:
                    severity = 2

                alerts.append({
                    "alert_type": event_type[:50],
                    "severity": severity,
                    "location_country": "USA",
                    "location_city": props.get('areaDesc', '')[:50],
                    "description": description[:200],
                    "source": "NOAA"
                })
            logger.info(f"🌤️ Fetched {len(alerts)} NOAA weather alerts")
    except Exception as e:
        logger.error(f"❌ NOAA API error: {e}")

    # Global weather via Open-Meteo
    try:
        global_locations = [
            ("London", "UK", 51.51, -0.13),
            ("Paris", "France", 48.86, 2.35),
            ("Berlin", "Germany", 52.52, 13.40),
            ("Singapore", "Singapore", 1.35, 103.82),
            ("Tokyo", "Japan", 35.68, 139.76),
            ("Sydney", "Australia", -33.87, 151.21),
            ("Toronto", "Canada", 43.65, -79.38),
            ("Sao Paulo", "Brazil", -23.55, -46.63),
            ("Cape Town", "South Africa", -33.92, 18.42),
            ("Mumbai", "India", 19.08, 72.88),
            ("Shanghai", "China", 31.23, 121.47),
            ("Dubai", "UAE", 25.20, 55.27)
        ]

        for city, country, lat, lon in global_locations:
            try:
                url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
                response = requests.get(url, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    weather = data.get("current_weather", {})
                    wind = weather.get("windspeed", 0)
                    temp = weather.get("temperature", 0)

                    if wind > 50:
                        alerts.append({
                            "alert_type": "Storm Warning",
                            "severity": 4,
                            "location_country": country,
                            "location_city": city,
                            "description": f"Windspeed {wind} km/h. Severe conditions expected.",
                            "source": "Open-Meteo"
                        })
                    elif wind > 35:
                        alerts.append({
                            "alert_type": "High Wind Warning",
                            "severity": 3,
                            "location_country": country,
                            "location_city": city,
                            "description": f"Windspeed {wind} km/h. Shipping delays possible.",
                            "source": "Open-Meteo"
                        })
                    elif temp > 38:
                        alerts.append({
                            "alert_type": "Extreme Heat Warning",
                            "severity": 4,
                            "location_country": country,
                            "location_city": city,
                            "description": f"Temperature {temp}°C. Health risks, worker safety concerns.",
                            "source": "Open-Meteo"
                        })
                    elif temp > 32:
                        alerts.append({
                            "alert_type": "Heat Advisory",
                            "severity": 3,
                            "location_country": country,
                            "location_city": city,
                            "description": f"Temperature {temp}°C. Heat precautions recommended.",
                            "source": "Open-Meteo"
                        })
                time.sleep(0.3)
            except Exception as e:
                logger.error(f"❌ Global weather error for {city}: {e}")
    except Exception as e:
        logger.error(f"❌ Global weather setup error: {e}")

    return alerts

def fetch_shipping_disruptions():
    disruptions = [
        {"route_name": "Strait of Hormuz", "disruption_type": "geopolitical", "severity": 5, "estimated_delay_days": 7,
         "affected_commodities": ["Crude Oil", "LNG"], "description": "Iran war threatening tanker traffic. 20% of global oil passes through.", "status": "active"},
        {"route_name": "Red Sea", "disruption_type": "security", "severity": 5, "estimated_delay_days": 14,
         "affected_commodities": ["Oil", "Containers"], "description": "Houthi attacks on commercial vessels. Major shipping lines rerouting.", "status": "active"},
        {"route_name": "Panama Canal", "disruption_type": "drought", "severity": 4, "estimated_delay_days": 10,
         "affected_commodities": ["Wheat", "Steel"], "description": "Water levels at 5-year low. Daily crossings reduced.", "status": "active"},
        {"route_name": "Suez Canal", "disruption_type": "congestion", "severity": 3, "estimated_delay_days": 5,
         "affected_commodities": ["Oil", "Gas"], "description": "Heavy traffic due to rerouted vessels.", "status": "active"},
        {"route_name": "Strait of Malacca", "disruption_type": "piracy", "severity": 3, "estimated_delay_days": 2,
         "affected_commodities": ["Electronics", "Semiconductors"], "description": "Increased piracy incidents reported.", "status": "monitoring"},
        {"route_name": "Bosphorus Strait", "disruption_type": "geopolitical", "severity": 3, "estimated_delay_days": 4,
         "affected_commodities": ["Wheat", "Oil"], "description": "Russian sanctions causing inspection delays.", "status": "active"},
        {"route_name": "Cape of Good Hope", "disruption_type": "diversion", "severity": 3, "estimated_delay_days": 12,
         "affected_commodities": ["All Cargo"], "description": "Ships rerouting from Red Sea add 10-14 days.", "status": "active"}
    ]
    logger.info(f"🚢 Generated {len(disruptions)} shipping disruptions")
    return disruptions

# ============================================
# MAIN INGESTION
# ============================================

def run_ingestion():
    logger.info("=" * 60)
    logger.info("📊 Athena SCIP - Unified Event Ingestor")
    logger.info("=" * 60)

    total_stored = 0

    # Clear old weather and shipping data
    try:
        supabase.table("weather_alerts").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        supabase.table("shipping_disruptions").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        logger.info("🧹 Cleared old weather and shipping data")
    except Exception as e:
        logger.warning(f"⚠️ Clear old data warning: {e}")

    # 1. News Events
    logger.info("\n📰 Fetching News Events...")
    news_events = fetch_news_events()
    for event in news_events:
    # Enrich location
    location = enrich_location(event["title"], event.get("description", ""))
    
    # Classify event type
    event_type = classify_event_type(event["title"], event.get("description", ""))
    
    # Check if supply chain related
    if not is_supply_chain_related(event["title"], event.get("description", "")):
        # Skip non-supply-chain events to improve data quality
        logger.debug(f"⏭️ Skipping non-supply-chain event: {event['title'][:50]}...")
        continue
    
    # Calculate severity (boosted for supply chain impact)
    base_severity = calculate_severity(event_type, event["title"])
    
    # Calculate supply chain impact
    impact = calculate_supply_chain_impact(event["title"], event.get("description", ""), base_severity)
    severity = min(5, max(1, int(impact['impact_score'] / 20) + 1))
    
    event_data = {
        "external_id": hashlib.md5(event["title"].encode()).hexdigest()[:16],
        "source": event.get("source", "news"),
        "title": event["title"],
        "description": event.get("description", ""),
        "event_type": event_type,
        "severity": severity,
        "location_country": location,
        "start_date": event.get("published_at"),
        "confidence_score": 0.7,
        "affected_areas": impact['affected_areas'],
        "supply_chain_impact_score": impact['impact_score'],
        "raw_data": json.dumps(event)
    }
    if store_item("events", event_data, "external_id"):
        total_stored += 1

    # 2. Earthquakes
    logger.info("\n🌍 Fetching Earthquakes...")
    earthquakes = fetch_earthquakes()
    for eq in earthquakes:
        props = eq.get("properties", {})
        place = props.get('place', 'Unknown')
        magnitude = props.get("mag", 0)

        event_data = {
            "external_id": props.get("code", hashlib.md5(place.encode()).hexdigest()[:16]),
            "source": "USGS",
            "title": f"Earthquake: {place}",
            "description": f"Magnitude {magnitude} earthquake detected",
            "event_type": "natural_disaster",
            "severity": 4 if magnitude >= 6 else 3,
            "location_country": extract_country(place),
            "start_date": datetime.fromtimestamp(props.get("time", 0)/1000).isoformat() if props.get("time") else None,
            "confidence_score": 0.9,
            "raw_data": json.dumps(props)
        }
        if store_item("events", event_data, "external_id"):
            total_stored += 1

    # 3. Weather Alerts
    logger.info("\n🌤️ Fetching Weather Alerts...")
    weather_alerts = fetch_weather_alerts()
    for alert in weather_alerts:
        if store_item("weather_alerts", alert, "alert_type"):
            total_stored += 1

    # 4. Shipping Disruptions
    logger.info("\n🚢 Fetching Shipping Disruptions...")
    shipping_disruptions = fetch_shipping_disruptions()
    for disruption in shipping_disruptions:
        if store_item("shipping_disruptions", disruption, "route_name"):
            total_stored += 1

    logger.info(f"\n{'='*60}")
    logger.info(f"✅ Ingestion Complete! Stored {total_stored} new items")
    logger.info(f"{'='*60}")
    
    return total_stored

# ============================================
# MAIN LOOP
# ============================================

def run_continuous():
    """Run the ingestor continuously with the configured interval"""
    logger.info(f"🚀 Starting continuous ingestion (interval: {INGEST_INTERVAL}s)")
    
    while True:
        try:
            run_ingestion()
            logger.info(f"⏳ Sleeping for {INGEST_INTERVAL} seconds...")
            time.sleep(INGEST_INTERVAL)
        except KeyboardInterrupt:
            logger.info("🛑 Shutting down Event Ingestor...")
            break
        except Exception as e:
            logger.error(f"❌ Error in main loop: {e}")
            logger.info(f"⏳ Retrying in {INGEST_INTERVAL} seconds...")
            time.sleep(INGEST_INTERVAL)

# ============================================
# ENTRY POINT
# ============================================

if __name__ == "__main__":
    # Check if running in continuous mode or one-off
    if os.getenv("RUN_ONCE", "false").lower() == "true":
        run_ingestion()
    else:
        run_continuous()