# AI-Powered Predictive Maintenance Platform

A comprehensive predictive maintenance solution built with FastAPI, machine learning models, and RAG for industrial equipment monitoring.

## 🚀 Features

- **Real-time Sensor Data Ingestion**: CSV upload and processing
- **Failure Prediction**: XGBoost-based 24-72h failure risk scoring
- **Anomaly Detection**: Isolation Forest for equipment anomalies
- **RAG Chat System**: Q&A over maintenance manuals
- **Web Interface**: Modern frontend for testing and visualization
- **Observability**: Prometheus metrics and structured logging

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI API   │    │  Background     │
│   (Port 3000)   │◄──►│   (Port 8000)   │◄──►│  Workers        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   PostgreSQL    │    │     Redis       │
                       │   (via Docker)  │    │   (Cache)       │
                       └─────────────────┘    └─────────────────┘
```

## 🛠️ Tech Stack

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL/SQLite
- **ML**: XGBoost, Isolation Forest, scikit-learn
- **Vector Search**: FAISS, sentence-transformers
- **Queue**: Redis with RQ workers
- **Frontend**: HTML5, JavaScript, modern CSS
- **Monitoring**: Prometheus, OpenTelemetry

## 📋 Prerequisites

- Python 3.12+
- Docker & Docker Compose (optional - will use SQLite if not available)

## 🚀 Quick Start (Windows)

### **Option 1: One-Click Start** ⚡
Double-click `START_HERE.bat` - it does everything automatically!

### **Option 2: Manual Start** 🔧

#### 1. Setup Environment
```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Train ML Models
```bash
# Generate training data
python scripts/generate_training_data.py

# Train models
python -m ai.model_train --data seed_data/training_sensors.csv
```

#### 3. Start Services
```bash
# Start Docker (optional - for PostgreSQL and Redis)
docker-compose up -d db redis

# Start API server
start_api.bat

# In another terminal, start frontend
start_frontend.bat
```

#### 4. Upload Data & Test
```bash
# Upload training data
python scripts/upload_data.py

# Test predictions
python scripts/test_system.py
```

#### 5. Access the Application
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/healthz

## 📊 API Endpoints

All endpoints require `?api_key=dev-CHANGE-ME`

- `POST /api/v1/ingest` - Upload sensor CSV data
- `POST /api/v1/predict` - Get failure predictions
- `POST /api/v1/chat` - Ask questions about maintenance
- `GET /api/v1/alerts` - View active alerts
- `GET /healthz` - Health check

## 📁 Project Structure

```
AI_Powered_Predective_Maintenance/
├── api/              # FastAPI application
│   ├── routes/       # API endpoints
│   ├── main.py       # Application entry point
│   ├── deps.py       # Settings and dependencies
│   └── schemas.py    # Pydantic models
├── ai/               # Machine learning
│   ├── features.py   # Feature engineering
│   ├── model_train.py # Training pipeline
│   └── model_infer.py # Inference service
├── persistence/      # Database layer
│   ├── db.py         # Database connection
│   └── models.py     # SQLAlchemy models
├── rag/              # RAG system
│   ├── index.py      # Index builder
│   └── retrieve.py   # Retrieval logic
├── frontend/         # Web interface
├── workers/          # Background tasks
├── scripts/          # Utility scripts
└── seed_data/        # Training data
```

## 🔑 Configuration

Edit `.env` file:

```env
# API Settings
API_KEY=dev-CHANGE-ME
API_PORT=8000

# Database (auto-fallback to SQLite if PostgreSQL unavailable)
DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/pdm

# File Upload
MAX_FILE_SIZE_MB=50
ALLOWED_FILE_TYPES=csv,txt
```

## 🎯 Usage Examples

### Upload Sensor Data (Frontend)
1. Go to http://localhost:3000
2. Click "Generate Sample Data" (100-1000 rows)
3. Upload the CSV file
4. View ingestion results

### Get Predictions
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/predict",
    params={"api_key": "dev-CHANGE-ME"},
    json={
        "machine_id": "M-001",
        "horizon_hours": 24,
        "include_anomaly": True
    }
)
print(response.json())
```

### Chat with RAG System
```python
response = requests.post(
    "http://localhost:8000/api/v1/chat",
    params={"api_key": "dev-CHANGE-ME"},
    json={"query": "How to maintain bearings?"}
)
print(response.json())
```

## 🐛 Troubleshooting

### Port 8000 already in use
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID)
taskkill /PID <process_id> /F
```

### PostgreSQL connection failed
- No problem! The system automatically falls back to SQLite (`pdm.db`)
- Start Docker if you want to use PostgreSQL: `docker-compose up -d db`

### No predictions returned
- Ensure you uploaded data: `python scripts/upload_data.py`
- Use correct machine IDs: `M-001` to `M-005` (from training data)
- Check that models are trained: `ai/artifacts/` should contain `.joblib` files

### Import errors
- Activate virtual environment: `.venv\Scripts\activate`
- Install dependencies: `pip install -r requirements.txt`

## 📈 Monitoring

- **Prometheus Metrics**: http://localhost:8000/metrics
- **API Logs**: Structured JSON in console
- **Database Check**: `python scripts/check_database.py`

## 🧪 Testing

```bash
# System end-to-end test
python scripts/test_system.py

# Check database status
python scripts/check_database.py

# Generate new training data
python scripts/generate_training_data.py
```

## 🔧 Development

### Retrain Models
```bash
# Generate fresh data
python scripts/generate_training_data.py --days 60 --machines 10

# Train models
python -m ai.model_train --data seed_data/training_sensors.csv

# Verify artifacts
dir ai\artifacts\
```

### Add New Sensor Types
1. Add to `api/routes/ingest.py` in `valid_sensors` list
2. Update `ai/features.py` to process new sensor
3. Retrain models with new data

## 📚 Machine IDs

The system includes data for these machines:
- **M-001** to **M-005** (training data)
- You can generate data for any machine ID using the frontend

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - see LICENSE for details.

---

## 💡 Quick Tips

- **First time setup**: Just run `START_HERE.bat` and wait
- **Frontend not loading**: Check if API is running on port 8000
- **API not starting**: Kill old processes on port 8000
- **No predictions**: Upload data first via frontend or `scripts/upload_data.py`
- **Docker issues**: System works fine with SQLite, no Docker needed!

## 📞 Support

For issues, check the console logs for detailed error messages. Most issues are:
1. Port conflicts (kill old processes)
2. Missing data (upload training data)
3. Wrong machine IDs (use M-001 to M-005)
