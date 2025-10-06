"""
Complete system test - tests all API endpoints
"""

import requests
import json
from datetime import datetime, timedelta

API_BASE = "http://localhost:8000/api/v1"
API_KEY = "dev-CHANGE-ME"

def test_failure_prediction():
    """Test failure prediction endpoint"""
    print("🔮 Testing Failure Prediction...")
    
    request_data = {
        "machine_id": "M-001",
        "horizon_hours": 24,
        "include_anomaly": True,
        "include_factors": True
    }
    
    response = requests.post(
        f"{API_BASE}/predict",
        params={"api_key": API_KEY},
        json=request_data
    )
    
    if response.ok:
        result = response.json()
        predictions = result.get('predictions', [])
        if predictions:
            pred = predictions[0]
            print(f"✅ Success!")
            print(f"   Machine: {pred.get('machine_id')}")
            print(f"   Failure Probability: {pred.get('failure_probability', 0)*100:.1f}%")
            print(f"   Anomaly Score: {pred.get('anomaly_score', 0)*100:.1f}%")
            print(f"   Horizon: {pred.get('horizon_hours')} hours")
            print(f"   Confidence: {pred.get('confidence', 0)*100:.1f}%")
        else:
            print(f"✅ Response received but no predictions")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   {response.text}")
    
    return response.ok

def test_anomaly_detection():
    """Test anomaly detection"""
    print("\n🔍 Testing Anomaly Detection...")
    
    request_data = {
        "machine_id": "M-002",
        "horizon_hours": 24,
        "include_anomaly": True,
        "include_factors": False
    }
    
    response = requests.post(
        f"{API_BASE}/predict",
        params={"api_key": API_KEY},
        json=request_data
    )
    
    if response.ok:
        result = response.json()
        predictions = result.get('predictions', [])
        if predictions:
            pred = predictions[0]
            print(f"✅ Success!")
            print(f"   Machine: {pred.get('machine_id')}")
            print(f"   Anomaly Score: {pred.get('anomaly_score', 0)*100:.1f}%")
            print(f"   Is Anomaly: {'Yes' if pred.get('anomaly_score', 0) > 0.5 else 'No'}")
        else:
            print(f"✅ Response received but no predictions")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   {response.text}")
    
    return response.ok

def test_health():
    """Test health endpoint"""
    print("\n🏥 Testing Health Endpoint...")
    
    response = requests.get("http://localhost:8000/healthz")
    
    if response.ok:
        result = response.json()
        print(f"✅ API is {result.get('status')}")
    else:
        print(f"❌ API health check failed")
    
    return response.ok

def test_alerts():
    """Test alerts endpoint"""
    print("\n🚨 Testing Alerts...")
    
    response = requests.get(
        f"{API_BASE}/alerts",
        params={"api_key": API_KEY, "limit": 5}
    )
    
    if response.ok:
        result = response.json()
        alerts = result.get('alerts', [])
        print(f"✅ Retrieved {len(alerts)} alerts")
        for alert in alerts[:3]:
            print(f"   - {alert.get('severity')}: {alert.get('message')}")
    else:
        print(f"❌ Failed: {response.status_code}")
    
    return response.ok

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Testing AI-Powered Predictive Maintenance System")
    print("=" * 60)
    
    health_ok = test_health()
    failure_ok = test_failure_prediction()
    anomaly_ok = test_anomaly_detection()
    alerts_ok = test_alerts()
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print("=" * 60)
    print(f"   Health Check:        {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"   Failure Prediction:  {'✅ PASS' if failure_ok else '❌ FAIL'}")
    print(f"   Anomaly Detection:   {'✅ PASS' if anomaly_ok else '❌ FAIL'}")
    print(f"   Alerts:              {'✅ PASS' if alerts_ok else '❌ FAIL'}")
    
    all_passed = health_ok and failure_ok and anomaly_ok and alerts_ok
    
    if all_passed:
        print("\n🎉 All tests passed! System is fully operational.")
        print("\n📚 Next Steps:")
        print("   1. Open frontend: http://localhost:3000")
        print("   2. API docs: http://localhost:8000/docs")
        print("   3. Upload your own data and get predictions!")
    else:
        print("\n⚠️ Some tests failed. Check:")
        print("   - Is the API server running?")
        print("   - Has training data been uploaded?")
        print("   - Check server logs for errors")

