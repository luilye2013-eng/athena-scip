"""
Athena SCIP - Recommendation Engine
Generates supply chain mitigation recommendations based on events
SECURE VERSION: Uses environment variables for all secrets
"""

import os
import uuid
import logging
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv

# ============================================
# Load Environment Variables
# ============================================
load_dotenv()

# ============================================
# Configuration from Environment Variables
# ============================================
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://catpprgdbvenutyyjqbx.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

if not SUPABASE_KEY:
    logging.warning("SUPABASE_SERVICE_ROLE_KEY not set. Using ANON key as fallback.")
    SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "sb_publishable_ykiqckKEQw2m8XXvX4cGnQ_5ijzb7Py")

# ============================================
# Setup Logging
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# Supabase Client
# ============================================
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Supabase client created successfully")
except Exception as e:
    logger.error(f"Failed to create Supabase client: {e}")
    exit(1)

# ============================================
# Commodity Risk Mapping
# ============================================
COMMODITY_RISK_MAP = {
    "war": {
        "commodities": ["Wheat", "Natural Gas", "Crude Oil", "Nickel", "Steel", "Semiconductors"],
        "risk_multiplier": 15,
        "base_actions": [
            "🛡️ Activate business continuity plan for affected region",
            "📦 Increase inventory buffer by 60-90 days",
            "🚢 Reroute shipments away from conflict zone",
            "🔄 Identify alternative suppliers outside region"
        ]
    },
    "natural_disaster": {
        "commodities": ["Semiconductors", "Lithium", "Wheat", "Logistics"],
        "risk_multiplier": 8,
        "base_actions": [
            "⚠️ Contact suppliers in affected region immediately",
            "📦 Expedite pending orders before logistics congestion",
            "🚛 Activate alternative transportation routes",
            "📋 Review disaster recovery procedures"
        ]
    },
    "strike": {
        "commodities": ["Logistics", "Transportation", "Manufacturing"],
        "risk_multiplier": 6,
        "base_actions": [
            "🚚 Reroute shipments to alternative ports",
            "📦 Increase inventory at distribution centers",
            "🤝 Negotiate with alternative logistics providers",
            "📢 Communicate potential delays to customers"
        ]
    },
    "sanctions": {
        "commodities": ["Oil", "Gas", "Technology", "Rare Earth"],
        "risk_multiplier": 10,
        "base_actions": [
            "⚖️ Review legal compliance for affected jurisdictions",
            "🔄 Identify alternative sourcing countries",
            "📦 Consider inventory stockpiling",
            "🏭 Explore domestic supplier alternatives"
        ]
    },
    "pandemic": {
        "commodities": ["Medical Supplies", "Semiconductors", "Logistics"],
        "risk_multiplier": 8,
        "base_actions": [
            "🦠 Implement health and safety protocols",
            "🌍 Diversify supplier base geographically",
            "📦 Increase safety stock of critical components",
            "📋 Review business continuity plan"
        ]
    }
}

# ============================================
# Helper Functions
# ============================================

def get_organization_id():
    """Get the first organization ID from the database"""
    try:
        result = supabase.table("organizations").select("id").limit(1).execute()
        if result.data:
            return result.data[0]["id"]
        
        # Create default organization if none exists
        logger.info("No organization found. Creating default...")
        new_org = supabase.table("organizations").insert({"name": "Athena SCIP Default"}).execute()
        return new_org.data[0]["id"]
    except Exception as e:
        logger.error(f"Error getting organization: {e}")
        return None

def get_urgency(severity):
    """Determine urgency based on severity score"""
    if severity >= 5:
        return "immediate", 3
    elif severity >= 4:
        return "immediate", 5
    elif severity >= 3:
        return "short_term", 7
    else:
        return "long_term", 30

# ============================================
# Main Recommendation Generation
# ============================================

def generate_recommendations():
    """Main function to generate recommendations for all events"""
    logger.info("Starting recommendation generation...")
    
    # Get organization ID
    org_id = get_organization_id()
    if not org_id:
        logger.error("No organization available. Cannot generate recommendations.")
        return 0
    
    logger.info(f"Using organization: {org_id}")
    
    # Get all events
    try:
        events = supabase.table("events").select("*").execute()
        logger.info(f"Found {len(events.data)} events")
    except Exception as e:
        logger.error(f"Error fetching events: {e}")
        return 0
    
    # Get existing recommendations to avoid duplicates
    try:
        existing = supabase.table("recommendations").select("event_id").execute()
        existing_ids = set([e["event_id"] for e in existing.data]) if existing.data else set()
        logger.info(f"Found {len(existing_ids)} existing recommendations")
    except Exception as e:
        logger.error(f"Error fetching existing recommendations: {e}")
        existing_ids = set()
    
    count = 0
    for event in events.data:
        event_id = event.get("id")
        
        # Skip if already has recommendations
        if event_id in existing_ids:
            continue
        
        event_type = event.get("event_type", "other")
        severity = event.get("severity", 2)
        title = event.get("title", "")
        
        # Get risk profile for event type
        risk_profile = COMMODITY_RISK_MAP.get(event_type, COMMODITY_RISK_MAP.get("war"))
        urgency, days = get_urgency(severity)
        
        # Create recommendation
        rec = {
            "id": str(uuid.uuid4()),
            "organization_id": org_id,
            "event_id": event_id,
            "action_type": "mitigation",
            "description": f"[{event_type.upper()}] {title[:100]}. Affected: {', '.join(risk_profile['commodities'][:4])}. {risk_profile['base_actions'][0]}",
            "urgency": urgency,
            "estimated_time_to_implement_days": days,
            "created_at": datetime.utcnow().isoformat()
        }
        
        try:
            result = supabase.table("recommendations").insert(rec).execute()
            count += 1
            logger.info(f"✓ Created recommendation for: {title[:50]}...")
        except Exception as e:
            logger.error(f"✗ Failed for {title[:30]}: {e}")
    
    logger.info(f"✅ Done! Generated {count} new recommendations.")
    return count

# ============================================
# Entry Point
# ============================================

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("Athena SCIP - Recommendation Engine")
    logger.info("Running with secure environment variables")
    logger.info("=" * 50)
    generate_recommendations()