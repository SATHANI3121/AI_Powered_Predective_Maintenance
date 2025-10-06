# 🚀 Personal Usage Guide - AI Predictive Maintenance

Quick reference with copy-paste commands for daily use.

---

## 📋 Table of Contents
- [Quick Start](#quick-start)
- [Daily Commands](#daily-commands)
- [Training & Data](#training--data)
- [Testing & Debugging](#testing--debugging)
- [Database Operations](#database-operations)
- [Docker Commands](#docker-commands)
- [Troubleshooting](#troubleshooting)

---

## ⚡ Quick Start

### Start Everything (One Command)
```bash
START_HERE.bat
```

### Manual Start (Step by Step)
```bash
# 1. Activate environment
.venv\Scripts\activate

# 2. Start Docker services (optional)
docker-compose up -d db redis

# 3. Start API
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000

# 4. In new terminal - Start Frontend
cd frontend
python server.py
```

---

## 🎯 Daily Commands

### Start API Server Only
```bash
start_api.bat
```

### Start Frontend Only
```bash
start_frontend.bat
```

### Stop All Services
```bash
# Stop API server (Ctrl+C in terminal)
# Or kill process:
taskkill /F /IM python.exe /FI "WINDOWTITLE eq PDM*"

# Stop Docker
docker-compose down
```

### Restart Everything
```bash
# Kill old processes
taskkill /F /IM python.exe /FI "WINDOWTITLE eq PDM*"

# Restart
START_HERE.bat
```

---

## 🔧 Training & Data

### Generate Training Data
```bash
# Activate environment first
.venv\Scripts\activate

# Generate data (default: 5 machines, 30 days)
python scripts/generate_training_data.py

# Custom data generation
python -c "from scripts.generate_training_data import generate_sensor_data; generate_sensor_data(n_machines=10, days=60, output_file='seed_data/custom_data.csv')"
```

### Train ML Models
```bash
# Train with default data
python -m ai.model_train --data seed_data/training_sensors.csv

# Train with custom data
python -m ai.model_train --data seed_data/custom_data.csv --out ai/artifacts
```

### Upload Data to API
```bash
# Upload training data
python scripts/upload_data.py

# Check if data uploaded successfully
python scripts/check_database.py
```

---

## 🧪 Testing & Debugging

### Test API Endpoints
```bash
# Run full system test
python scripts/test_system.py

# Test single endpoint
python -c "import requests; print(requests.get('http://localhost:8000/healthz').json())"
```

### Check Health
```bash
# API health
curl http://localhost:8000/healthz

# Or with PowerShell
Invoke-WebRequest -Uri "http://localhost:8000/healthz" | Select-Object -Expand Content
```

### Test Prediction
```bash
python -c "
import requests
r = requests.post(
    'http://localhost:8000/api/v1/predict',
    params={'api_key': 'dev-CHANGE-ME'},
    json={'machine_id': 'M-001', 'horizon_hours': 24, 'include_anomaly': True}
)
print(r.json())
"
```

### Test Upload
```bash
# Create test CSV
python -c "
import pandas as pd
from datetime import datetime, timedelta
data = []
for i in range(100):
    ts = datetime.now() - timedelta(minutes=i*5)
    data.append({'timestamp': ts, 'machine_id': 'TEST-001', 'sensor': 'temperature', 'value': 70 + i*0.1})
    data.append({'timestamp': ts, 'machine_id': 'TEST-001', 'sensor': 'vibration', 'value': 0.2 + i*0.001})
df = pd.DataFrame(data)
df.to_csv('test_upload.csv', index=False)
print('Created test_upload.csv')
"

# Upload via curl (PowerShell)
$filePath = "test_upload.csv"
$uri = "http://localhost:8000/api/v1/ingest?api_key=dev-CHANGE-ME"
curl.exe -X POST -F "file=@$filePath" $uri
```

---

## 💾 Database Operations

### Check Database Status
```bash
python scripts/check_database.py
```

### Quick Database Query
```bash
# Check records count
python -c "
from persistence.db import SessionLocal
from persistence.models import SensorReading
db = SessionLocal()
count = db.query(SensorReading).count()
print(f'Total sensor readings: {count}')
db.close()
"
```

### List All Machines
```bash
python -c "
from persistence.db import SessionLocal
from persistence.models import SensorReading
db = SessionLocal()
machines = [m[0] for m in db.query(SensorReading.machine_id).distinct().all()]
print('Machines:', machines)
db.close()
"
```

### Clear Database (SQLite)
```bash
# Stop API first, then delete SQLite file
del pdm.db

# Restart API to recreate tables
start_api.bat
```

### Reset PostgreSQL Database
```bash
# Drop and recreate
docker-compose down -v
docker-compose up -d db redis

# Wait 5 seconds, then restart API
timeout /t 5
start_api.bat
```

---

## 🐳 Docker Commands

### Start Docker Services
```bash
# Start all
docker-compose up -d

# Start specific service
docker-compose up -d db
docker-compose up -d redis
```

### Check Docker Status
```bash
docker-compose ps
```

### View Docker Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs db
docker-compose logs redis

# Follow logs
docker-compose logs -f
```

### Stop Docker Services
```bash
# Stop all
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Connect to PostgreSQL
```bash
# Via Docker
docker-compose exec db psql -U user -d pdm

# Common queries:
# \dt              -- List tables
# SELECT COUNT(*) FROM sensor_readings;
# SELECT DISTINCT machine_id FROM sensor_readings;
# \q               -- Quit
```

---

## 🔍 Troubleshooting

### Port 8000 Already in Use
```bash
# Find process
netstat -ano | findstr :8000

# Kill process (replace PID with actual number)
taskkill /PID <PID> /F

# Or kill all Python processes
taskkill /F /IM python.exe
```

### Port 3000 Already in Use
```bash
# Find process
netstat -ano | findstr :3000

# Kill process
taskkill /PID <PID> /F
```

### Check Which Ports Are Listening
```bash
netstat -ano | findstr LISTENING
```

### Reinstall Dependencies
```bash
# Activate environment
.venv\Scripts\activate

# Reinstall all
pip install --force-reinstall -r requirements.txt

# Or create fresh environment
deactivate
rmdir /s /q .venv
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Clear Python Cache
```bash
# Remove all __pycache__
Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force

# Or use PowerShell one-liner
Get-ChildItem -Path . -Directory -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
```

### View API Logs in Real-time
```bash
# Start API with verbose logging
$env:LOG_LEVEL="DEBUG"
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --log-level debug
```

### Test Individual Components

#### Test Feature Engineering
```bash
python -c "
import pandas as pd
from datetime import datetime, timedelta
from ai.features import build_features

# Create sample data
data = []
for i in range(100):
    ts = datetime.now() - timedelta(minutes=i*5)
    data.append({'timestamp': ts, 'machine_id': 'M-001', 'sensor': 'temperature', 'value': 70 + i*0.1})
    data.append({'timestamp': ts, 'machine_id': 'M-001', 'sensor': 'vibration', 'value': 0.2})

df = pd.DataFrame(data)
features = build_features(df)
print(f'Generated {len(features)} feature rows with {len(features.columns)} columns')
print(features.head())
"
```

#### Test ML Models
```bash
python -c "
import pandas as pd
from datetime import datetime, timedelta
from ai.model_infer import MLService

# Create sample data
data = []
for i in range(100):
    ts = datetime.now() - timedelta(minutes=i*5)
    data.append({'timestamp': ts, 'machine_id': 'M-001', 'sensor': 'temperature', 'value': 70})
    data.append({'timestamp': ts, 'machine_id': 'M-001', 'sensor': 'vibration', 'value': 0.2})

df = pd.DataFrame(data)

# Test inference
ml = MLService()
failure_prob = ml.predict_failure_probability(df)
anomaly_score = ml.detect_anomaly(df)

print(f'Failure Probability: {failure_prob:.2%}')
print(f'Anomaly Score: {anomaly_score:.2f}')
"
```

#### Test RAG System
```bash
python -c "
from rag.retrieve import retrieve_context
results = retrieve_context('bearing maintenance', top_k=3)
for i, result in enumerate(results, 1):
    print(f'{i}. Score: {result[1]:.3f}')
    print(f'   Text: {result[0][:100]}...')
"
```

---

## 📊 Useful Queries

### Get Latest Sensor Reading
```bash
python -c "
from persistence.db import SessionLocal
from persistence.models import SensorReading
db = SessionLocal()
latest = db.query(SensorReading).order_by(SensorReading.ts.desc()).first()
if latest:
    print(f'Latest: {latest.machine_id} - {latest.sensor} = {latest.value} at {latest.ts}')
db.close()
"
```

### Count Records per Machine
```bash
python -c "
from persistence.db import SessionLocal
from persistence.models import SensorReading
from sqlalchemy import func
db = SessionLocal()
counts = db.query(SensorReading.machine_id, func.count(SensorReading.id)).group_by(SensorReading.machine_id).all()
for machine, count in counts:
    print(f'{machine}: {count} readings')
db.close()
"
```

### View Recent Alerts
```bash
python -c "
from persistence.db import SessionLocal
from persistence.models import Alert
db = SessionLocal()
alerts = db.query(Alert).order_by(Alert.ts.desc()).limit(10).all()
for alert in alerts:
    print(f'{alert.ts} - {alert.machine_id}: {alert.message} (Severity: {alert.severity})')
db.close()
"
```

---

## 🎨 Frontend URLs

- **Main Interface**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **API Redoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/healthz
- **Metrics**: http://localhost:8000/metrics

---

## 🔑 API Key

Default API key for local development:
```
dev-CHANGE-ME
```

All API requests need: `?api_key=dev-CHANGE-ME`

---

## 💡 Quick Tips

### Generate Data and Train in One Go
```bash
python scripts/generate_training_data.py && python -m ai.model_train --data seed_data/training_sensors.csv && python scripts/upload_data.py
```

### Full Reset (Clean Slate)
```bash
# Kill all processes
taskkill /F /IM python.exe

# Remove database
del pdm.db

# Remove cache
Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force

# Restart
START_HERE.bat
```

### Quick Performance Test
```bash
# Upload data and test predictions
python scripts/upload_data.py && python scripts/test_system.py
```

### Monitor API in Real-time
```bash
# In one terminal - start API
start_api.bat

# In another terminal - watch logs
Get-Content api_log.txt -Wait -Tail 50
```

---

## 📝 Environment Variables (.env)

```env
# API Settings
API_KEY=dev-CHANGE-ME
API_PORT=8000
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/pdm

# File Upload
MAX_FILE_SIZE_MB=50
ALLOWED_FILE_TYPES=csv,txt

# Redis
REDIS_URL=redis://localhost:6379/0

# Model Settings
MODEL_ARTIFACTS_DIR=ai/artifacts
```

---

## 🎯 Common Workflows

### Workflow 1: Daily Development
```bash
# 1. Start services
START_HERE.bat

# 2. Make changes to code

# 3. Restart API only (faster)
# Press Ctrl+C in API terminal, then:
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# 4. Test changes
python scripts/test_system.py
```

### Workflow 2: Retrain Models
```bash
# 1. Generate new data
python scripts/generate_training_data.py

# 2. Train models
python -m ai.model_train --data seed_data/training_sensors.csv

# 3. Restart API to load new models
taskkill /F /IM python.exe /FI "WINDOWTITLE eq PDM*"
start_api.bat

# 4. Upload fresh data
python scripts/upload_data.py

# 5. Test predictions
python scripts/test_system.py
```

### Workflow 3: Demo Preparation
```bash
# 1. Full reset
taskkill /F /IM python.exe
docker-compose down -v
del pdm.db

# 2. Generate demo data
python scripts/generate_training_data.py

# 3. Train models
python -m ai.model_train --data seed_data/training_sensors.csv

# 4. Start everything
START_HERE.bat

# 5. Verify
python scripts/test_system.py
```

---

## 📞 Quick Reference Card

| Task | Command |
|------|---------|
| Start All | `START_HERE.bat` |
| Start API | `start_api.bat` |
| Start Frontend | `start_frontend.bat` |
| Kill All | `taskkill /F /IM python.exe` |
| Train Models | `python -m ai.model_train --data seed_data/training_sensors.csv` |
| Upload Data | `python scripts/upload_data.py` |
| Test System | `python scripts/test_system.py` |
| Check DB | `python scripts/check_database.py` |
| Health Check | `curl http://localhost:8000/healthz` |
| View Logs | `docker-compose logs -f` |

---

**Last Updated**: October 2025  
**For**: Personal Use - AI Predictive Maintenance System

