"""
Commodity Configuration
Centralized mapping of commodity names to their current ticker symbols
This file is easy to update when tickers change
"""

# Primary commodity list - these are the stable names used throughout the system
COMMODITY_NAMES = [
    "Crude Oil",
    "Brent Oil",
    "Natural Gas",
    "Gasoline",
    "Gold",
    "Silver",
    "Platinum",
    "Palladium",
    "Copper",
    "Aluminum",
    "Zinc",
    "Nickel",
    "Lead",
    "Steel",
    "Iron Ore",
    "Wheat",
    "Corn",
    "Soybeans",
    "Rice",
    "Coffee",
    "Sugar",
    "Cocoa",
    "Cotton",
    "Lumber",
    "Livestock",
    "Lithium",
    "Cobalt",
    "Rare Earth",
    "Semiconductors",
    "Uranium"
]

# Ticker mapping - easily updatable when symbols change
# Format: "Commodity Name": ["primary_ticker", "fallback_ticker1", "fallback_ticker2"]
# The system will try tickers in order until one works
COMMODITY_TICKERS = {
    # Energy
    "Crude Oil": ["CL=F", "USO", "BNO"],
    "Brent Oil": ["BZ=F", "BNO"],
    "Natural Gas": ["NG=F", "UNG", "BOIL"],
    "Gasoline": ["RB=F", "UGA"],

    # Precious Metals
    "Gold": ["GC=F", "GLD", "IAU"],
    "Silver": ["SI=F", "SLV", "PSLV"],
    "Platinum": ["PL=F", "PPLT"],
    "Palladium": ["PA=F", "PALL"],

    # Base Metals
    "Copper": ["HG=F", "CPER", "COPX"],
    "Aluminum": ["JJU"],
    "Zinc": ["ZNC"],
    "Nickel": ["NIKL"],
    "Lead": ["LEAD"],
    "Steel": ["SLX", "X", "STLD"],
    "Iron Ore": ["FEF", "VALE"],

    # Agriculture
    "Wheat": ["ZW=F", "WEAT", "WHT"],
    "Corn": ["ZC=F", "CORN", "C"],
    "Soybeans": ["ZS=F", "SOYB", "SOY"],
    "Rice": ["ZR=F"],
    "Coffee": ["KC=F", "JO", "CAFE"],
    "Sugar": ["SB=F", "SGG", "CANE"],
    "Cocoa": ["CC=F", "NIB"],
    "Cotton": ["CT=F", "BAL"],
    "Lumber": ["LB=F", "WOOD"],
    "Livestock": ["LE=F", "GF=F", "COW"],

    # Specialty Commodities
    "Lithium": ["LIT", "ALB", "SQM"],
    "Cobalt": ["COB", "SCCO"],
    "Rare Earth": ["REMX", "MP"],
    "Semiconductors": ["SOXX", "SMH", "SOX"],
    "Uranium": ["URA", "UROY", "CCJ"],
}

# Default fallback prices when all tickers fail
# These should be updated periodically from a reliable source
FALLBACK_PRICES = {
    "Crude Oil": 77.50,
    "Brent Oil": 81.20,
    "Natural Gas": 3.28,
    "Gasoline": 2.45,
    "Gold": 2020.00,
    "Silver": 28.50,
    "Platinum": 980.00,
    "Palladium": 1050.00,
    "Copper": 4.70,
    "Aluminum": 1.15,
    "Zinc": 1.35,
    "Nickel": 7.25,
    "Lead": 0.95,
    "Steel": 847.50,
    "Iron Ore": 117.20,
    "Wheat": 249.00,
    "Corn": 198.00,
    "Soybeans": 425.00,
    "Rice": 16.50,
    "Coffee": 195.00,
    "Sugar": 22.00,
    "Cocoa": 2800.00,
    "Cotton": 0.85,
    "Lumber": 520.00,
    "Livestock": 185.00,
    "Lithium": 14750.00,
    "Cobalt": 28500.00,
    "Rare Earth": 150.00,
    "Semiconductors": 1248.00,
    "Uranium": 92.00,
}