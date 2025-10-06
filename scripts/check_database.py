"""Check database status and contents"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from persistence.db import SessionLocal
from persistence.models import SensorReading, Machine, Alert, Prediction
from sqlalchemy import func

def check_database():
    """Check database status"""
    db = SessionLocal()
    try:
        print("=" * 60)
        print("📊 Database Status Check")
        print("=" * 60)
        
        # Sensor readings
        reading_count = db.query(SensorReading).count()
        machines = db.query(SensorReading.machine_id).distinct().all()
        sensors = db.query(SensorReading.sensor).distinct().all()
        
        print(f"\n📈 Sensor Readings:")
        print(f"   Total: {reading_count:,}")
        print(f"   Machines: {len(machines)} - {[m[0] for m in machines[:10]]}")
        print(f"   Sensors: {[s[0] for s in sensors]}")
        
        if reading_count > 0:
            # Time range
            min_ts = db.query(func.min(SensorReading.ts)).scalar()
            max_ts = db.query(func.max(SensorReading.ts)).scalar()
            print(f"   Time range: {min_ts} to {max_ts}")
            
            # Sample record
            sample = db.query(SensorReading).first()
            print(f"\n📝 Sample Record:")
            print(f"   Machine: {sample.machine_id}")
            print(f"   Sensor: {sample.sensor}")
            print(f"   Value: {sample.value}")
            print(f"   Timestamp: {sample.ts}")
        
        # Machines
        machine_count = db.query(Machine).count()
        print(f"\n🏭 Machines:")
        print(f"   Total: {machine_count}")
        
        # Predictions
        pred_count = db.query(Prediction).count()
        print(f"\n🔮 Predictions:")
        print(f"   Total: {pred_count}")
        
        # Alerts
        alert_count = db.query(Alert).count()
        if alert_count > 0:
            active_alerts = db.query(Alert).filter_by(resolved=False).count()
            print(f"\n🚨 Alerts:")
            print(f"   Total: {alert_count}")
            print(f"   Active: {active_alerts}")
        else:
            print(f"\n🚨 Alerts: None")
        
        print("\n" + "=" * 60)
        if reading_count > 0:
            print("✅ Database is populated and ready!")
        else:
            print("⚠️  Database is empty. Upload data:")
            print("   python scripts/upload_data.py")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Database error: {e}")
        print("\nMake sure:")
        print("   - PostgreSQL is running (docker-compose up -d postgres)")
        print("   - Database URL is correct in .env")
    finally:
        db.close()

if __name__ == "__main__":
    check_database()

