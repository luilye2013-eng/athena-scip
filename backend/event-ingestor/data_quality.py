"""
Athena SCIP - Data Quality Module
Improves event data quality through enrichment, filtering, and classification
"""
import re
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ============================================
# SUPPLY CHAIN KEYWORDS (Filtering)
# ============================================
SUPPLY_CHAIN_KEYWORDS = [
    # Logistics & Transportation
    'ship', 'port', 'container', 'freight', 'cargo', 'vessel', 'tanker',
    'rail', 'truck', 'warehouse', 'inventory', 'distribution',
    
    # Manufacturing
    'production', 'factory', 'plant', 'assembly', 'manufacturing',
    'semiconductor', 'chip', 'auto', 'automotive', 'steel',
    
    # Raw Materials
    'oil', 'gas', 'wheat', 'corn', 'soy', 'copper', 'aluminum',
    'lithium', 'nickel', 'iron ore', 'rare earth', 'commodity',
    
    # Supply Chain Disruptions
    'shortage', 'surplus', 'disruption', 'delay', 'backlog',
    'bottleneck', 'strike', 'sanctions', 'embargo', 'tariff',
    
    # Geopolitical (Supply Chain Relevant)
    'canal', 'strait', 'blockade', 'border', 'customs', 'quarantine'
]

# ============================================
# LOCATION ENRICHMENT
# ============================================
LOCATION_KEYWORDS = {
    'Russia': ['russia', 'moscow', 'kremlin', 'volgograd', 'siberia'],
    'Ukraine': ['ukraine', 'kyiv', 'kiev', 'kharkiv', 'odessa', 'lviv'],
    'USA': ['usa', 'united states', 'america', 'washington', 'new york', 'california', 'texas'],
    'China': ['china', 'beijing', 'shanghai', 'guangzhou', 'shenzhen'],
    'India': ['india', 'mumbai', 'delhi', 'bangalore', 'chennai'],
    'Japan': ['japan', 'tokyo', 'osaka', 'nagoya'],
    'Germany': ['germany', 'berlin', 'munich', 'frankfurt', 'hamburg'],
    'France': ['france', 'paris', 'lyon', 'marseille'],
    'UK': ['uk', 'united kingdom', 'britain', 'london', 'manchester'],
    'Iran': ['iran', 'tehran', 'persian', 'hormuz'],
    'Israel': ['israel', 'tel aviv', 'jerusalem', 'gaza'],
    'Saudi Arabia': ['saudi', 'riyadh', 'aramco'],
    'UAE': ['uae', 'dubai', 'abu dhabi', 'emirates'],
    'Turkey': ['turkey', 'istanbul', 'ankara', 'bosphorus'],
    'Indonesia': ['indonesia', 'jakarta', 'java', 'sumatra'],
    'Philippines': ['philippines', 'manila', 'davao'],
    'Australia': ['australia', 'sydney', 'melbourne', 'perth'],
    'Brazil': ['brazil', 'sao paulo', 'rio de janeiro', 'brasilia'],
    'South Africa': ['south africa', 'johannesburg', 'cape town'],
    'Nigeria': ['nigeria', 'lagos', 'abuja']
}

# ============================================
# EVENT CLASSIFICATION IMPROVEMENT
# ============================================
SUPPLY_CHAIN_EVENT_TYPES = {
    'war': {
        'keywords': ['war', 'conflict', 'attack', 'invasion', 'missile', 'drone strike', 'troops', 'casualties'],
        'supply_chain_impact': ['Military conflict disrupting supply routes', 'Trade restrictions', 'Sanctions']
    },
    'natural_disaster': {
        'keywords': ['earthquake', 'flood', 'hurricane', 'typhoon', 'cyclone', 'wildfire', 'drought', 'tsunami', 'storm'],
        'supply_chain_impact': ['Disruption to manufacturing', 'Logistics delays', 'Infrastructure damage']
    },
    'sanctions': {
        'keywords': ['sanctions', 'embargo', 'trade ban', 'tariff', 'restrictions'],
        'supply_chain_impact': ['Trade restrictions', 'Alternative sourcing required', 'Price volatility']
    },
    'strike': {
        'keywords': ['strike', 'walkout', 'labor dispute', 'union', 'protest', 'blockade'],
        'supply_chain_impact': ['Port/warehouse closures', 'Logistics delays', 'Production slowdown']
    },
    'shipping': {
        'keywords': ['shipping', 'canal', 'strait', 'vessel', 'tanker', 'port', 'cargo'],
        'supply_chain_impact': ['Shipping route disruption', 'Increased freight costs', 'Delivery delays']
    },
    'pandemic': {
        'keywords': ['outbreak', 'epidemic', 'pandemic', 'virus', 'disease', 'quarantine'],
        'supply_chain_impact': ['Workforce shortages', 'Factory closures', 'Border closures']
    }
}

# ============================================
# DATA QUALITY FUNCTIONS
# ============================================

def is_supply_chain_related(title: str, description: str) -> bool:
    """
    Determine if an event is supply chain related
    Returns True if event affects supply chains
    """
    text = (title + " " + (description or "")).lower()
    
    # Check for supply chain keywords
    for keyword in SUPPLY_CHAIN_KEYWORDS:
        if keyword.lower() in text:
            return True
    
    # Check for event types that affect supply chains
    for event_type, data in SUPPLY_CHAIN_EVENT_TYPES.items():
        if any(kw in text for kw in data['keywords']):
            return True
    
    return False

def enrich_location(title: str, description: str, current_country: Optional[str] = None) -> Optional[str]:
    """
    Enrich location information using keyword matching
    """
    # If already has a valid country, keep it
    if current_country and current_country not in ['Unknown', 'null', 'N/A', None]:
        return current_country
    
    text = (title + " " + (description or "")).lower()
    
    # Try to find location from keywords
    for country, keywords in LOCATION_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return country
    
    return "Unknown"

def classify_event_type(title: str, description: str) -> str:
    """
    Improved event classification focusing on supply chain impact
    """
    text = (title + " " + (description or "")).lower()
    
    # Check each event type
    for event_type, data in SUPPLY_CHAIN_EVENT_TYPES.items():
        if any(kw in text for kw in data['keywords']):
            return event_type
    
    # If not classified, check if supply chain related
    if is_supply_chain_related(title, description):
        return "supply_chain_other"
    
    return "non_supply_chain"

def calculate_supply_chain_impact(title: str, description: str, severity: int) -> Dict[str, Any]:
    """
    Calculate supply chain impact score and affected areas
    """
    text = (title + " " + (description or "")).lower()
    
    # Base impact from severity
    impact_score = severity * 10
    
    # Additional impact factors
    impact_factors = {
        'shipping': 15 if any(kw in text for kw in ['ship', 'port', 'canal', 'strait']) else 0,
        'manufacturing': 15 if any(kw in text for kw in ['factory', 'plant', 'production']) else 0,
        'raw_materials': 15 if any(kw in text for kw in ['oil', 'gas', 'wheat', 'copper']) else 0,
        'logistics': 10 if any(kw in text for kw in ['truck', 'rail', 'warehouse']) else 0,
        'geopolitical': 20 if any(kw in text for kw in ['war', 'sanctions', 'conflict']) else 0
    }
    
    total_impact = impact_score + sum(impact_factors.values())
    
    # Determine affected supply chain areas
    affected_areas = []
    if impact_factors['shipping'] > 0:
        affected_areas.append('Logistics & Transportation')
    if impact_factors['manufacturing'] > 0:
        affected_areas.append('Manufacturing')
    if impact_factors['raw_materials'] > 0:
        affected_areas.append('Raw Materials')
    if impact_factors['logistics'] > 0:
        affected_areas.append('Warehousing & Distribution')
    if impact_factors['geopolitical'] > 0:
        affected_areas.append('Trade & Geopolitical')
    
    return {
        'impact_score': min(100, total_impact),
        'affected_areas': affected_areas if affected_areas else ['General Supply Chain'],
        'severity_boosted': impact_score
    }