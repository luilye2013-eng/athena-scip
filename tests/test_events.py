"""
Unit Tests for Athena SCIP API Gateway
Run with: py -m pytest tests/
"""

import pytest
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now import from the correct path
from backend.api_gateway.main import app
from fastapi.testclient import TestClient

# Create test client
client = TestClient(app)

# ============================================
# Health Check Tests
# ============================================

def test_health_check():
    """Test that the health endpoint returns 200 OK"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "status" in data["data"]
    assert "database" in data["data"]

def test_root_endpoint():
    """Test that the root endpoint returns service info"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["data"]["service"] == "Athena SCIP API Gateway"
    assert data["data"]["version"] == "2.0.0"

# ============================================
# Events Tests
# ============================================

def test_get_events():
    """Test that events endpoint returns a list of events"""
    response = client.get("/events?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "events" in data["data"]
    assert isinstance(data["data"]["events"], list)

def test_get_events_summary():
    """Test that events summary returns total count"""
    response = client.get("/events/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "total_events" in data["data"]

def test_get_events_with_filter():
    """Test that event filtering works"""
    response = client.get("/events?event_type=war&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    for event in data["data"]["events"]:
        assert event["event_type"] == "war"

# ============================================
# Commodities Tests
# ============================================

def test_get_commodities():
    """Test that commodities endpoint returns data"""
    response = client.get("/commodities")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "commodities" in data["data"]
    assert isinstance(data["data"]["commodities"], list)

# ============================================
# Shipping Tests
# ============================================

def test_get_shipping_disruptions():
    """Test that shipping disruptions endpoint returns data"""
    response = client.get("/shipping/disruptions")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "disruptions" in data["data"]

# ============================================
# Weather Tests
# ============================================

def test_get_weather_alerts():
    """Test that weather alerts endpoint returns data"""
    response = client.get("/weather/alerts")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "alerts" in data["data"]

# ============================================
# Price Tests
# ============================================

def test_get_live_prices():
    """Test that live prices endpoint returns data"""
    response = client.get("/prices/live")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "prices" in data["data"]

# ============================================
# Country Risk Tests
# ============================================

def test_get_country_risk():
    """Test that country risk endpoint returns data"""
    response = client.get("/country-risk/enhanced")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "countries" in data["data"]

# ============================================
# Trends Tests
# ============================================

def test_get_price_trends():
    """Test that price trends endpoint returns data"""
    response = client.get("/trends/prices?days=14")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "trends" in data["data"]

def test_get_risk_trends():
    """Test that risk trends endpoint returns data"""
    response = client.get("/trends/risk?days=14")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "trends" in data["data"]

# ============================================
# Error Handling Tests
# ============================================

def test_invalid_endpoint():
    """Test that invalid endpoints return 404"""
    response = client.get("/invalid-endpoint")
    assert response.status_code == 404