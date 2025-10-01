# AI-Powered Predictive Maintenance Platform

A comprehensive predictive maintenance solution built with FastAPI, Azure services, and machine learning models for industrial equipment monitoring.

## 🚀 Features

- **Real-time Sensor Data Ingestion**: CSV upload and processing
- **Failure Prediction**: XGBoost-based 24-72h failure risk scoring
- **Anomaly Detection**: Isolation Forest for equipment anomalies
- **RAG Chat System**: Q&A over maintenance manuals using Azure AI Search
- **Observability**: Prometheus metrics, Azure Monitor, and structured logging
- **Scalable Architecture**: Containerized with Azure Container Apps

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI API   │    │  Background     │    │   Azure AI      │
│   (Container)   │◄──►│  Workers        │◄──►│   Search        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │     Redis       │    │   Azure Key     │
│   (Azure DB)    │    │   (Cache)       │    │     Vault       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Tech Stack

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **ML**: XGBoost, Isolation Forest, scikit-learn
- **Vector Search**: Azure AI Search, FAISS (fallback)
- **Queue**: Redis with RQ workers
- **Monitoring**: Prometheus, Azure Monitor
- **Deployment**: Azure Container Apps, GitHub Actions

## 📋 Prerequisites

- Azure Student Account
- Python 3.11+
- Docker & Docker Compose
- Azure CLI installed

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone and setup
git clone <your-repo>
cd AI_Powered_Predective_Maintenance

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
make install
```

### 2. Configure Azure Services

```bash
# Login to Azure
az login

# Create resource group
az group create --name pdm-rg --location eastus

# Create Azure services (see infra/azure-setup.sh)
./infra/azure-setup.sh
```

### 3. Local Development

```bash
# Copy environment template
cp .env.sample .env
# Edit .env with your Azure credentials

# Seed database and train models
make seed
make train

# Start services
make up

# Visit API docs: http://localhost:8000/docs
```

### 4. Deploy to Azure

```bash
# Deploy infrastructure
make deploy-azure

# Run CI/CD pipeline
git push origin main
```

## 📊 API Endpoints

- `POST /ingest` - Upload sensor CSV data
- `POST /predict` - Get failure predictions
- `POST /chat` - Ask questions about maintenance
- `GET /alerts` - View active alerts
- `GET /healthz` - Health check

## 🧪 Testing

```bash
# Run all tests
make test

# Run specific test suites
pytest tests/unit/
pytest tests/integration/
```

## 📈 Monitoring

- **Metrics**: Prometheus endpoint at `/metrics`
- **Logs**: Structured JSON logging
- **Traces**: OpenTelemetry integration
- **Dashboards**: Azure Monitor workbooks

## 🔧 Development

```bash
# Format code
make fmt

# Lint code
make lint

# Generate synthetic data
python scripts/generate_synth_data.py

# Train models
make train

# Run evaluations
make eval
```

## 📚 Documentation

- [API Documentation](http://localhost:8000/docs)
- [Architecture Guide](docs/architecture.md)
- [Deployment Guide](docs/deployment.md)
- [Contributing](docs/contributing.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.



