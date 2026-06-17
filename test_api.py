"""
Simple API Test Runner for Athena SCIP
Run with: py test_api.py
"""

import requests
import json
import time

API_URL = "http://localhost:8000"
passed = 0
failed = 0

def test(name, url, expected_status=200, check_key=None):
    global passed, failed
    print(f"Testing {name}...", end=" ")
    try:
        response = requests.get(f"{API_URL}{url}", timeout=5)
        if response.status_code == expected_status:
            data = response.json()
            if check_key and check_key not in data.get("data", {}):
                print(f"❌ Key '{check_key}' not found")
                failed += 1
                return
            print("✅ PASSED")
            passed += 1
        else:
            print(f"❌ FAILED (Status: {response.status_code})")
            failed += 1
    except Exception as e:
        print(f"❌ FAILED: {e}")
        failed += 1

def main():
    print("=" * 50)
    print(" Athena SCIP - API Test Suite")
    print("=" * 50)
    print(f"API URL: {API_URL}")
    print("\nMake sure the API Gateway is running!")
    print("  cd backend\\api-gateway")
    print("  py -m uvicorn main:app --reload --port 8000")
    print("\n" + "=" * 50 + "\n")
    
    # Check if API is running
    try:
        requests.get(f"{API_URL}/health", timeout=2)
        print("✅ API Gateway is running\n")
    except:
        print("❌ ERROR: API Gateway is not running!")
        print("Please start it first.")
        return
    
    # Run tests
    test("Health Check", "/health", check_key="status")
    test("Root Endpoint", "/", check_key="service")
    test("Events", "/events?limit=5", check_key="events")
    test("Events Summary", "/events/summary", check_key="total_events")
    test("Commodities", "/commodities", check_key="commodities")
    test("Recommendations", "/recommendations?limit=5", check_key="recommendations")
    test("Shipping Disruptions", "/shipping/disruptions", check_key="disruptions")
    test("Weather Alerts", "/weather/alerts", check_key="alerts")
    test("Live Prices", "/prices/live", check_key="prices")
    test("Country Risk", "/country-risk/enhanced", check_key="countries")
    test("Price Trends", "/trends/prices?days=7", check_key="trends")
    test("Risk Trends", "/trends/risk?days=7", check_key="trends")
    test("Invalid Endpoint", "/invalid", expected_status=404)
    
    print("\n" + "=" * 50)
    print(f" RESULTS: {passed} passed, {failed} failed")
    print("=" * 50)
    
    if failed == 0:
        print("✅ All tests passed! Your API is working correctly.")
    else:
        print("❌ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()