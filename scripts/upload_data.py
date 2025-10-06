"""
Upload training data to the database via the ingest endpoint
"""

import requests
import os
import sys

# Add parent directory to path to import from project
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_BASE = "http://localhost:8000/api/v1"
API_KEY = "dev-CHANGE-ME"

def upload_training_data():
    """Upload the training sensor data to the API"""
    
    training_file = "seed_data/training_sensors.csv"
    
    if not os.path.exists(training_file):
        print(f"❌ Training file not found: {training_file}")
        print(f"   Run: python scripts/generate_training_data.py")
        return False
    
    print(f"📤 Uploading training data from {training_file}...")
    
    with open(training_file, 'rb') as f:
        files = {'file': ('training_sensors.csv', f, 'text/csv')}
        
        response = requests.post(
            f"{API_BASE}/ingest",
            params={"api_key": API_KEY},
            files=files
        )
    
    if response.ok:
        result = response.json()
        print(f"✅ Upload successful!")
        print(f"   Records: {result.get('records_ingested', 0)}")
        print(f"   Machines: {result.get('machines_affected', [])}")
        print(f"   Processing time: {result.get('processing_time_seconds', 0):.2f}s")
        return True
    else:
        print(f"❌ Upload failed: {response.status_code}")
        try:
            error_data = response.json()
            print(f"   Error: {error_data.get('detail', response.text)}")
        except:
            print(f"   Error: {response.text}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Uploading Training Data to API")
    print("=" * 60)
    
    try:
        if upload_training_data():
            print("\n✅ Data upload complete! You can now:")
            print("   - Test predictions: python scripts/test_system.py")
            print("   - Use frontend: http://localhost:3000")
            print("   - View API docs: http://localhost:8000/docs")
        else:
            print("\n❌ Data upload failed. Make sure:")
            print("   - API server is running (python -m uvicorn api.main:app)")
            print("   - Training data exists (python scripts/generate_training_data.py)")
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to API server!")
        print("   Start the server with: python -m uvicorn api.main:app --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

