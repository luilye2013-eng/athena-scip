"""
Pytest configuration for Athena SCIP tests
"""

import pytest
import sys
import os

# Add the backend path to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

@pytest.fixture
def test_client():
    """Return a test client for the API"""
    from backend.api_gateway.main import app
    from fastapi.testclient import TestClient
    return TestClient(app)