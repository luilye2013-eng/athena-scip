"""
Athena SCIP - Recommendation Engine
Generates supply chain mitigation recommendations based on events
SECURE VERSION: Uses environment variables for all secrets
Runs continuously with configurable interval
"""

import os
import uuid
import logging
import sys
import time
from datetime import datetime, timedelta
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

RECOMMEND_INTERVAL = int(os.getenv("RECOMMEND_INTERVAL", "600"))  # Default: 10 minutes

# ============================================
# Setup Logging
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
# Supabase Client
# ============================================
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("✅ Supabase client created successfully")
except Exception as e:
    logger.error(f"❌ Failed to create Supabase client: {e}")
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
            "🚚 Reroute shipments away from conflict zone",
            "🔍 Identify alternative suppliers outside region"
        ]
    },
    "natural_disaster": {
        "commodities": ["Semiconductors", "Lithium", "Wheat", "Logistics"],
        "risk_multiplier": 8,
        "base_actions": [
            "⚠️ Contact suppliers in affected region immediately",
            "📦 Expedite pending orders before logistics congestion",
            "🚢 Activate alternative transportation routes",
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
            "🔍 Identify alternative sourcing countries",
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
        logger.info("📝 No organization found. Creating default...")
        new_org = supabase.table("organizations").insert({"name": "Athena SCIP Default"}).execute()
        return new_org.data[0]["id"]
    except Exception as e:
        logger.error(f"❌ Error getting organization: {e}")
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

def get_commodities_for_event(event_type):
    """Get affected commodities for an event type"""
    risk_profile = COMMODITY_RISK_MAP.get(event_type, COMMODITY_RISK_MAP.get("war"))
    return risk_profile.get("commodities", ["General"])

def get_actions_for_event(event_type):
    """Get recommended actions for an event type"""
    risk_profile = COMMODITY_RISK_MAP.get(event_type, COMMODITY_RISK_MAP.get("war"))
    return risk_profile.get("base_actions", ["Monitor situation", "Review supply chain impact"])

# ============================================
# Main Recommendation Generation
# ============================================

def generate_recommendations():
    """Main function to generate recommendations for all events"""
    logger.info("🔄 Starting recommendation generation...")

    # Get organization ID
    org_id = get_organization_id()
    if not org_id:
        logger.error("❌ No organization available. Cannot generate recommendations.")
        return 0

    logger.info(f"🏢 Using organization: {org_id}")

    # Get events that don't have recommendations yet
    try:
        events = supabase.table("events") \
            .select("*") \
            .is_("has_recommendation", "null") \
            .gte("severity", 2) \
            .order("created_at", desc=True) \
            .limit(50) \
            .execute()
        
        logger.info(f"📋 Found {len(events.data)} events needing recommendations")
    except Exception as e:
        logger.error(f"❌ Error fetching events: {e}")
        return 0

    if not events.data:
        logger.info("✅ No new events requiring recommendations")
        return 0

    count = 0
    for event in events.data:
        event_id = event.get("id")
        event_type = event.get("event_type", "other")
        severity = event.get("severity", 2)
        title = event.get("title", "Unknown event")
        location_country = event.get("location_country") or "Global"

        # Get risk profile
        urgency, days = get_urgency(severity)
        commodities = get_commodities_for_event(event_type)
        actions = get_actions_for_event(event_type)

        # Build description
        description = f"[{event_type.upper()}] {title[:100]}. Affected: {', '.join(commodities[:4])}. {actions[0]}"

        # Create recommendation
        rec = {
            "id": str(uuid.uuid4()),
            "organization_id": org_id,
            "event_id": event_id,
            "action_type": "mitigation",
            "description": description,
            "urgency": urgency,
            "estimated_time_to_implement_days": days,
            "commodity_id": None,
            "supplier_id": None,
            "estimated_cost_impact": None,
            "created_at": datetime.utcnow().isoformat()
        }

        try:
            result = supabase.table("recommendations").insert(rec).execute()
            
            # Mark event as having recommendation
            supabase.table("events") \
                .update({"has_recommendation": True}) \
                .eq("id", event_id) \
                .execute()
            
            count += 1
            logger.info(f"✅ Created recommendation for: {title[:50]}...")
        except Exception as e:
            logger.error(f"❌ Failed for {title[:30]}: {e}")

    # Cleanup old recommendations (7+ days old)
    try:
        cutoff_date = (datetime.now() - timedelta(days=7)).isoformat()
        result = supabase.table("recommendations") \
            .delete() \
            .lt("created_at", cutoff_date) \
            .execute()
        deleted_count = len(result.data) if result.data else 0
        if deleted_count > 0:
            logger.info(f"🧹 Cleaned up {deleted_count} old recommendations")
    except Exception as e:
        logger.warning(f"⚠️ Cleanup warning: {e}")

    logger.info(f"✅ Done! Generated {count} new recommendations.")
    return count

# ============================================
# MAIN LOOP
# ============================================

def run_continuous():
    """Run the recommender continuously with the configured interval"""
    logger.info(f"🚀 Starting continuous recommender (interval: {RECOMMEND_INTERVAL}s)")
    
    while True:
        try:
            generate_recommendations()
            logger.info(f"⏳ Sleeping for {RECOMMEND_INTERVAL} seconds...")
            time.sleep(RECOMMEND_INTERVAL)
        except KeyboardInterrupt:
            logger.info("🛑 Shutting down Recommender Service...")
            break
        except Exception as e:
            logger.error(f"❌ Error in main loop: {e}")
            logger.info(f"⏳ Retrying in {RECOMMEND_INTERVAL} seconds...")
            time.sleep(RECOMMEND_INTERVAL)

# ============================================
# ENTRY POINT
# ============================================

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("🤖 Athena SCIP - Recommendation Engine")
    logger.info("Running with secure environment variables")
    logger.info("=" * 50)
    
    # Check if running in one-off mode
    if os.getenv("RUN_ONCE", "false").lower() == "true":
        generate_recommendations()
    else:
        run_continuous()