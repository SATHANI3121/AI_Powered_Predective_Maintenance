# 🤖 AI-Powered Predictive Maintenance - Frontend

A modern, interactive web interface for testing the AI-Powered Predictive Maintenance Platform.

## 🚀 Quick Start

### Option 1: Python Server (Recommended)
```bash
# Navigate to frontend directory
cd frontend

# Start the frontend server
python server.py
```

### Option 2: Manual Server
```bash
# Navigate to frontend directory
cd frontend

# Start a simple HTTP server
python -m http.server 3000
```

### Option 3: Open Directly
Simply open `index.html` in your web browser.

## 🌐 Access URLs

- **Frontend Interface**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/healthz

## 📋 Prerequisites

1. **API Server Running**: Make sure the FastAPI server is running on port 8000
2. **Database Services**: Ensure PostgreSQL and Redis are running via Docker

## 🎯 Features

### 📊 Data Upload Tab
- **File Upload**: Drag & drop CSV files or click to browse
- **Sample Data Generator**: Generate test sensor data
- **Real-time Processing**: Upload and process sensor data

### 🔮 Predictions Tab
- **Failure Prediction**: Get ML-based failure probability
- **Anomaly Detection**: Detect unusual patterns in sensor data
- **Risk Assessment**: Visual risk level indicators

### 💬 AI Chat Tab
- **Maintenance Q&A**: Ask questions about equipment maintenance
- **Quick Questions**: Pre-built common maintenance questions
- **AI Assistant**: Get intelligent responses about maintenance

### 🚨 Alerts Tab
- **Active Alerts**: View current system alerts
- **System Health**: Check overall system status
- **Real-time Monitoring**: Live system health indicators

## 🛠️ Technical Features

- **Responsive Design**: Works on desktop, tablet, and mobile
- **Modern UI**: Beautiful gradient design with smooth animations
- **Real-time Updates**: Live status indicators and loading states
- **Error Handling**: Comprehensive error messages and status updates
- **File Upload**: Drag & drop CSV file support
- **JSON Display**: Formatted API response display

## 📁 File Structure

```
frontend/
├── index.html          # Main frontend application
├── server.py          # Python HTTP server
└── README.md          # This file
```

## 🔧 API Integration

The frontend connects to the following API endpoints:

- `POST /ingest` - Upload sensor data
- `POST /predict` - Get failure predictions
- `POST /chat` - AI chat functionality
- `GET /alerts` - Retrieve alerts
- `GET /healthz` - Health check

## 🎨 UI Components

- **Tabbed Interface**: Organized feature sections
- **Card Layout**: Clean, modern card-based design
- **Status Indicators**: Color-coded success/error states
- **Loading States**: Animated spinners and progress indicators
- **File Upload**: Drag & drop interface with visual feedback

## 🚀 Getting Started

1. **Start the API Server**:
   ```bash
   cd ..  # Go back to project root
   python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
   ```

2. **Start the Frontend**:
   ```bash
   cd frontend
   python server.py
   ```

3. **Open Browser**: The frontend will automatically open at http://localhost:3000

## 🧪 Testing Features

### Sample Data Generation
- Click "Generate Sample Data" to create test CSV files
- Upload the generated files to test the API
- Use different machine IDs for multiple tests

### Quick Questions
- Try the pre-built maintenance questions
- Test the AI chat functionality
- Experiment with different query types

### Prediction Testing
- Use sample data to test failure predictions
- Try different prediction horizons (24h, 48h, 72h)
- Test anomaly detection with various scenarios

## 🎉 Enjoy Testing!

The frontend provides a complete testing environment for your AI-Powered Predictive Maintenance Platform. All features are interactive and provide real-time feedback from the API.

