/**
 * AI-Powered Predictive Maintenance Platform
 * Main Application Script
 * @author Senior Frontend Engineer
 */

'use strict';

// ============================================
// Application State & Configuration
// ============================================
window.APP_CONFIG = {
  API_BASE: '/api/v1',
  API_KEY: '',
  USE_API_KEY: false,
  HEALTH_CHECK_INTERVAL: 30000,
  CACHE_DURATION: 30000,
  REQUEST_TIMEOUT: 30000
};

// Request cache
const requestCache = new Map();

// Health check state
let healthCheckTimer = null;
let isOnline = true;

// Risk thresholds (centralized)
const RISK_THRESHOLDS = {
  failure: {
    high: 70,
    medium: 30
  },
  anomaly: {
    high: 80,
    medium: 50,
    low: 20
  },
  confidence: {
    high: 70,
    medium: 50
  }
};

// ============================================
// Configuration Loader
// ============================================
async function loadConfig() {
  try {
    const response = await fetch('/config.json');
    if (response.ok) {
      const config = await response.json();
      Object.assign(window.APP_CONFIG, config);
      console.log('✓ Configuration loaded successfully');
    }
  } catch (error) {
    console.warn('⚠ Could not load config.json, using defaults:', error.message);
  }
}

// ============================================
// Toast Notification System
// ============================================
let toastContainer = null;

function initToastContainer() {
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.className = 'toast-container';
    toastContainer.setAttribute('aria-live', 'polite');
    toastContainer.setAttribute('aria-atomic', 'true');
    document.body.appendChild(toastContainer);
  }
  return toastContainer;
}

function showToast(message, type = 'info', duration = 5000) {
  const container = initToastContainer();
  
  const icons = {
    success: '✓',
    error: '✕',
    warning: '⚠',
    info: 'ℹ'
  };
  
  const titles = {
    success: 'Success',
    error: 'Error',
    warning: 'Warning',
    info: 'Info'
  };
  
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.setAttribute('role', 'alert');
  
  toast.innerHTML = `
    <span class="toast-icon" aria-hidden="true">${icons[type] || 'ℹ'}</span>
    <div class="toast-content">
      <div class="toast-title">${titles[type] || 'Info'}</div>
      <div class="toast-message">${escapeHtml(message)}</div>
    </div>
    <button class="toast-close" aria-label="Close notification">×</button>
  `;
  
  const closeBtn = toast.querySelector('.toast-close');
  closeBtn.addEventListener('click', () => removeToast(toast));
  
  container.appendChild(toast);
  
  // Auto-remove after duration
  if (duration > 0) {
    setTimeout(() => removeToast(toast), duration);
  }
  
  return toast;
}

function removeToast(toast) {
  if (toast && toast.parentNode) {
    toast.style.animation = 'slideInRight 0.3s ease reverse';
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
    }, 300);
  }
}

// ============================================
// Status & Loading Helpers
// ============================================
function showStatus(elementId, message, type = 'info') {
  const element = document.getElementById(elementId);
  if (!element) return;
  
  element.className = `status ${type} show`;
  element.textContent = message;
  element.setAttribute('role', 'status');
  element.setAttribute('aria-live', 'polite');
}

function hideStatus(elementId) {
  const element = document.getElementById(elementId);
  if (!element) return;
  
  element.className = 'status';
  element.textContent = '';
}

function showLoading(elementId, show = true) {
  const element = document.getElementById(elementId);
  if (!element) return;
  
  if (show) {
    element.className = 'loading show';
    element.innerHTML = '<div class="spinner" role="status"><span class="sr-only">Loading...</span></div>';
  } else {
    element.className = 'loading';
    element.innerHTML = '';
  }
}

// ============================================
// Network Request Helper
// ============================================
async function request(url, options = {}) {
  const { API_BASE, API_KEY, USE_API_KEY, REQUEST_TIMEOUT } = window.APP_CONFIG;
  
  // Build full URL
  const fullUrl = url.startsWith('http') ? url : `${API_BASE}${url}`;
  
  // Add API key to URL if enabled
  const urlObj = new URL(fullUrl, window.location.origin);
  if (USE_API_KEY && API_KEY) {
    urlObj.searchParams.set('api_key', API_KEY);
  }
  
  // Set default headers
  const headers = {
    ...options.headers
  };
  
  // Add Content-Type for JSON requests
  if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(options.body);
  }
  
  // Create abort controller for timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);
  
  try {
    const response = await fetch(urlObj.toString(), {
      ...options,
      headers,
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    // Parse response
    const contentType = response.headers.get('content-type');
    let data;
    
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      data = await response.text();
    }
    
    if (!response.ok) {
      const errorMessage = data.detail || data.error || data.message || `HTTP ${response.status}`;
      throw new Error(errorMessage);
    }
    
    return data;
    
  } catch (error) {
    clearTimeout(timeoutId);
    
    if (error.name === 'AbortError') {
      throw new Error('Request timeout - please try again');
    }
    
    throw error;
  }
}

// Cached request wrapper
async function cachedRequest(cacheKey, url, options = {}) {
  const { CACHE_DURATION } = window.APP_CONFIG;
  
  // Check cache
  const cached = requestCache.get(cacheKey);
  if (cached && (Date.now() - cached.timestamp) < CACHE_DURATION) {
    console.log(`✓ Using cached response for: ${cacheKey}`);
    return cached.data;
  }
  
  // Make request
  const data = await request(url, options);
  
  // Store in cache
  requestCache.set(cacheKey, {
    data,
    timestamp: Date.now()
  });
  
  return data;
}

// ============================================
// Formatting Helpers
// ============================================
function formatPercent(value, decimals = 2) {
  const percent = value * 100;
  if (percent < 0.01 && percent > 0) {
    return '<0.01%';
  }
  return `${percent.toFixed(decimals)}%`;
}

function formatDate(date) {
  if (typeof date === 'string') {
    date = new Date(date);
  }
  return date.toLocaleString();
}

function formatFeatureName(feature) {
  return feature
    .replace(/_/g, ' ')
    .replace(/roll/g, 'avg')
    .replace(/lag/g, 'prev')
    .replace(/\b\w/g, l => l.toUpperCase());
}

function getRiskLevel(value, thresholds) {
  if (value > thresholds.high) return { level: 'high', icon: '🔴', text: 'High' };
  if (value > thresholds.medium) return { level: 'medium', icon: '🟡', text: 'Medium' };
  return { level: 'low', icon: '🟢', text: 'Low' };
}

function getConfidenceLevel(confidence) {
  const percent = confidence * 100;
  if (percent > RISK_THRESHOLDS.confidence.high) {
    return { class: 'confidence-high', text: 'High', icon: '🟢' };
  }
  if (percent > RISK_THRESHOLDS.confidence.medium) {
    return { class: 'confidence-medium', text: 'Medium', icon: '🟡' };
  }
  return { class: 'confidence-low', text: 'Low', icon: '🔴' };
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ============================================
// Health Check
// ============================================
async function checkHealth() {
  try {
    const response = await fetch('/healthz', { 
      method: 'GET',
      cache: 'no-cache'
    });
    
    const wasOnline = isOnline;
    isOnline = response.ok;
    
    const indicator = document.getElementById('healthStatus');
    if (indicator) {
      if (isOnline) {
        indicator.className = 'status-indicator online';
        indicator.textContent = '🟢 System Online';
      } else {
        indicator.className = 'status-indicator offline';
        indicator.textContent = '🔴 System Offline';
      }
    }
    
    // Show toast only on status change
    if (wasOnline && !isOnline) {
      showToast('System is offline - some features may not work', 'error', 0);
    } else if (!wasOnline && isOnline) {
      showToast('System is back online', 'success');
      // Clear cached requests on reconnection
      requestCache.clear();
    }
    
  } catch (error) {
    const wasOnline = isOnline;
    isOnline = false;
    
    const indicator = document.getElementById('healthStatus');
    if (indicator) {
      indicator.className = 'status-indicator offline';
      indicator.textContent = '🔴 System Offline';
    }
    
    if (wasOnline) {
      showToast('Cannot connect to server', 'error', 0);
    }
  }
}

// Debounced health check
let healthCheckDebounce = null;
function scheduleHealthCheck() {
  if (healthCheckDebounce) {
    clearTimeout(healthCheckDebounce);
  }
  
  healthCheckDebounce = setTimeout(() => {
    checkHealth();
  }, 1000);
}

function startHealthCheck() {
  checkHealth(); // Initial check
  
  if (healthCheckTimer) {
    clearInterval(healthCheckTimer);
  }
  
  healthCheckTimer = setInterval(() => {
    checkHealth();
  }, window.APP_CONFIG.HEALTH_CHECK_INTERVAL);
}

function stopHealthCheck() {
  if (healthCheckTimer) {
    clearInterval(healthCheckTimer);
    healthCheckTimer = null;
  }
}

// ============================================
// Tab Management (WAI-ARIA compliant)
// ============================================
function initTabs() {
  const tabList = document.querySelector('[role="tablist"]');
  if (!tabList) return;
  
  const tabs = Array.from(tabList.querySelectorAll('[role="tab"]'));
  const panels = Array.from(document.querySelectorAll('[role="tabpanel"]'));
  
  tabs.forEach((tab, index) => {
    tab.addEventListener('click', (e) => {
      e.preventDefault();
      selectTab(tab, tabs, panels);
    });
    
    tab.addEventListener('keydown', (e) => {
      handleTabKeydown(e, tabs, index);
    });
  });
  
  // Activate first tab
  if (tabs.length > 0) {
    selectTab(tabs[0], tabs, panels);
  }
}

function selectTab(selectedTab, allTabs, allPanels) {
  // Deactivate all tabs
  allTabs.forEach(tab => {
    tab.setAttribute('aria-selected', 'false');
    tab.setAttribute('tabindex', '-1');
  });
  
  // Hide all panels
  allPanels.forEach(panel => {
    panel.setAttribute('aria-hidden', 'true');
  });
  
  // Activate selected tab
  selectedTab.setAttribute('aria-selected', 'true');
  selectedTab.setAttribute('tabindex', '0');
  selectedTab.focus();
  
  // Show corresponding panel
  const panelId = selectedTab.getAttribute('aria-controls');
  const panel = document.getElementById(panelId);
  if (panel) {
    panel.setAttribute('aria-hidden', 'false');
  }
}

function handleTabKeydown(event, tabs, currentIndex) {
  let newIndex = currentIndex;
  
  switch (event.key) {
    case 'ArrowLeft':
      event.preventDefault();
      newIndex = currentIndex - 1;
      if (newIndex < 0) newIndex = tabs.length - 1;
      break;
      
    case 'ArrowRight':
      event.preventDefault();
      newIndex = currentIndex + 1;
      if (newIndex >= tabs.length) newIndex = 0;
      break;
      
    case 'Home':
      event.preventDefault();
      newIndex = 0;
      break;
      
    case 'End':
      event.preventDefault();
      newIndex = tabs.length - 1;
      break;
      
    default:
      return;
  }
  
  const allPanels = Array.from(document.querySelectorAll('[role="tabpanel"]'));
  selectTab(tabs[newIndex], tabs, allPanels);
}

// ============================================
// Data Upload
// ============================================
async function handleFileUpload(event) {
  event.preventDefault();
  
  const fileInput = document.getElementById('sensorFile');
  const file = fileInput.files[0];
  
  if (!file) {
    showToast('Please select a file', 'warning');
    return;
  }
  
  showLoading('uploadLoading', true);
  hideStatus('uploadStatus');
  
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    const data = await request('/ingest', {
      method: 'POST',
      body: formData
    });
    
    showToast(`Successfully uploaded ${data.records_inserted || 0} sensor readings`, 'success');
    showStatus('uploadStatus', `✓ ${data.message || 'Upload successful'}`, 'success');
    
    // Clear file input
    fileInput.value = '';
    
    // Clear prediction cache since we have new data
    requestCache.clear();
    
  } catch (error) {
    showToast(error.message, 'error');
    showStatus('uploadStatus', `✕ Upload failed: ${error.message}`, 'error');
  } finally {
    showLoading('uploadLoading', false);
  }
}

function generateSampleData() {
  const machineIds = ['M-001', 'M-002', 'M-003'];
  const sensors = ['temperature', 'vibration', 'pressure', 'current', 'speed'];
  
  let csv = 'timestamp,machine_id,sensor,value\n';
  const now = new Date();
  
  for (let i = 0; i < 1000; i++) {
    const timestamp = new Date(now.getTime() - i * 60000).toISOString();
    const machineId = machineIds[Math.floor(Math.random() * machineIds.length)];
    const sensor = sensors[Math.floor(Math.random() * sensors.length)];
    
    let value;
    switch (sensor) {
      case 'temperature':
        value = (Math.random() * 30 + 50).toFixed(2);
        break;
      case 'vibration':
        value = (Math.random() * 5).toFixed(2);
        break;
      case 'pressure':
        value = (Math.random() * 50 + 100).toFixed(2);
        break;
      case 'current':
        value = (Math.random() * 10 + 5).toFixed(2);
        break;
      case 'speed':
        value = (Math.random() * 1000 + 1000).toFixed(2);
        break;
      default:
        value = (Math.random() * 100).toFixed(2);
    }
    
    csv += `${timestamp},${machineId},${sensor},${value}\n`;
  }
  
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `sample_sensors_${Date.now()}.csv`;
  a.click();
  URL.revokeObjectURL(url);
  
  showToast('Sample data file downloaded', 'success');
}

// ============================================
// Predictions
// ============================================
async function getPrediction(event) {
  event.preventDefault();
  
  const machineId = document.getElementById('predictionMachineId').value.trim();
  
  if (!machineId) {
    showToast('Please enter a machine ID', 'warning');
    return;
  }
  
  showLoading('predictionLoading', true);
  hideStatus('predictionStatus');
  document.getElementById('predictionResult').innerHTML = '';
  
  try {
    const cacheKey = `prediction_${machineId}`;
    const data = await cachedRequest(cacheKey, '/predict', {
      method: 'POST',
      body: {
        machine_id: machineId,
        include_anomaly: true,
        include_factors: true
      }
    });
    
    showStatus('predictionStatus', '✓ Prediction analysis complete!', 'success');
    renderPredictionDashboard(data, machineId);
    
  } catch (error) {
    showToast(error.message, 'error');
    showStatus('predictionStatus', `✕ Prediction failed: ${error.message}`, 'error');
    
    // Show empty state
    const container = document.getElementById('predictionResult');
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">📊</div>
        <div class="empty-state-title">No Prediction Data</div>
        <div class="empty-state-description">${escapeHtml(error.message)}</div>
      </div>
    `;
  } finally {
    showLoading('predictionLoading', false);
  }
}

// ============================================
// Render Prediction Dashboard
// ============================================
function renderPredictionDashboard(data, machineId) {
  const container = document.getElementById('predictionResult');
  const predictions = data.predictions || [data];
  
  // Determine overall status from first prediction
  const firstPred = predictions[0] || data;
  const anomalyScore = (firstPred.anomaly_score || 0) * 100;
  const failureProb = (firstPred.failure_probability || 0) * 100;
  
  let statusClass = 'status-normal';
  let statusIcon = '🟢';
  let statusText = 'NORMAL - Equipment operating within expected parameters';
  
  if (failureProb > RISK_THRESHOLDS.failure.high || anomalyScore > RISK_THRESHOLDS.anomaly.high) {
    statusClass = 'status-alert';
    statusIcon = '🔴';
    statusText = 'ALERT - Immediate attention required';
  } else if (failureProb > RISK_THRESHOLDS.failure.medium || anomalyScore > RISK_THRESHOLDS.anomaly.medium) {
    statusClass = 'status-warning';
    statusIcon = '🟡';
    statusText = 'WARNING - Increased monitoring recommended';
  }
  
  let html = `
    <div class="prediction-dashboard">
      <div class="prediction-header">
        <div class="prediction-title">📊 Failure Prediction: ${escapeHtml(machineId)}</div>
        <div class="model-info">
          Model: ${escapeHtml(data.model_version || 'XGBoost v1.0')} | 
          Generated: ${formatDate(new Date())}
        </div>
      </div>
      
      <div class="status-banner ${statusClass}">
        <span style="font-size: 1.5rem;">${statusIcon}</span>
        <span>${statusText}</span>
      </div>
  `;
  
  // Multi-horizon tabs
  if (predictions.length > 1) {
    html += `<div class="horizon-tabs" role="tablist" aria-label="Prediction horizons">`;
    
    predictions.forEach((pred, idx) => {
      const horizon = pred.horizon || `${(idx + 1) * 24}h`;
      html += `
        <button 
          class="horizon-tab ${idx === 0 ? 'active' : ''}" 
          data-horizon="${idx}"
          role="tab"
          aria-selected="${idx === 0}"
          aria-controls="horizon-panel-${idx}"
        >
          ${horizon}
        </button>
      `;
    });
    
    html += `</div>`;
  }
  
  // Horizon content
  predictions.forEach((pred, idx) => {
    html += renderHorizonPanel(pred, idx, idx === 0);
  });
  
  // Technical details
  html += `
    <div class="technical-details">
      <div class="technical-toggle" id="tech-toggle-pred">
        ▼ Technical Details & Raw Data
      </div>
      <div class="technical-content" id="tech-content-pred">
        <pre>${escapeHtml(JSON.stringify(data, null, 2))}</pre>
      </div>
    </div>
  `;
  
  // Export buttons
  html += `
    <div class="export-buttons">
      <button class="export-btn" id="export-pred-json">
        📄 Download JSON
      </button>
      <button class="export-btn" id="export-pred-csv">
        📊 Download CSV
      </button>
    </div>
  `;
  
  html += `</div>`;
  container.innerHTML = html;
  
  // Attach event listeners
  attachPredictionEventListeners(data, machineId);
  
  // Store data for export
  window.predictionData = data;
}

function renderHorizonPanel(pred, index, isActive) {
  const failureProb = (pred.failure_probability || 0) * 100;
  const anomalyScore = (pred.anomaly_score || 0) * 100;
  const confidence = (pred.confidence || 0) * 100;
  
  const failureRisk = getRiskLevel(failureProb, RISK_THRESHOLDS.failure);
  const confLevel = getConfidenceLevel(pred.confidence || 0);
  
  let html = `
    <div 
      class="horizon-content ${isActive ? 'active' : ''}" 
      id="horizon-panel-${index}"
      role="tabpanel"
      aria-hidden="${!isActive}"
    >
      <div class="metric-grid">
        <div class="metric-card" style="border-left-color: ${failureRisk.level === 'high' ? 'var(--color-risk-high)' : failureRisk.level === 'medium' ? 'var(--color-risk-medium)' : 'var(--color-risk-low)'};">
          <div class="metric-label">Failure Probability</div>
          <div class="metric-value">${formatPercent(pred.failure_probability)}</div>
          <span class="risk-badge risk-${failureRisk.level}">${failureRisk.icon} ${failureRisk.text} Risk</span>
        </div>
        
        <div class="metric-card" style="border-left-color: ${anomalyScore > RISK_THRESHOLDS.anomaly.high ? 'var(--color-risk-high)' : anomalyScore > RISK_THRESHOLDS.anomaly.medium ? 'var(--color-risk-medium)' : 'var(--color-risk-low)'};">
          <div class="metric-label">Anomaly Score</div>
          <div class="metric-value">${anomalyScore.toFixed(1)}%</div>
          <span class="risk-badge risk-${anomalyScore > RISK_THRESHOLDS.anomaly.high ? 'high' : anomalyScore > RISK_THRESHOLDS.anomaly.medium ? 'medium' : 'low'}">
            ${anomalyScore > RISK_THRESHOLDS.anomaly.high ? '🔴' : anomalyScore > RISK_THRESHOLDS.anomaly.medium ? '🟡' : '🟢'} 
            ${anomalyScore > RISK_THRESHOLDS.anomaly.high ? 'High' : anomalyScore > RISK_THRESHOLDS.anomaly.medium ? 'Medium' : 'Normal'}
          </span>
        </div>
        
        <div class="metric-card">
          <div class="metric-label">Confidence</div>
          <div class="metric-value">${confidence.toFixed(0)}%</div>
          <div class="confidence-meter">
            <div class="confidence-bar">
              <div class="confidence-fill ${confLevel.class}" style="width: ${confidence}%"></div>
            </div>
          </div>
        </div>
      </div>
  `;
  
  // Top factors
  if (pred.top_factors && pred.top_factors.length > 0) {
    html += `
      <div class="factors-container">
        <div class="factors-title">🔧 Top Contributing Factors</div>
    `;
    
    pred.top_factors.slice(0, 5).forEach(factor => {
      const fullName = formatFeatureName(factor.feature);
      const shortName = fullName.length > 30 ? fullName.substring(0, 27) + '...' : fullName;
      const importance = factor.importance * 100;
      
      html += `
        <div class="factor-bar">
          <div class="factor-label">
            <span class="tooltip">
              ${escapeHtml(shortName)}
              <span class="tooltip-text">${escapeHtml(fullName)}</span>
            </span>
            <span>${importance.toFixed(1)}%</span>
          </div>
          <div class="factor-progress">
            <div class="factor-fill" style="width: ${importance}%">
              ${importance.toFixed(0)}%
            </div>
          </div>
        </div>
      `;
    });
    
    html += `</div>`;
  }
  
  html += `</div>`;
  return html;
}

function attachPredictionEventListeners(data, machineId) {
  // Horizon tabs
  const horizonTabs = document.querySelectorAll('.horizon-tab');
  const horizonPanels = document.querySelectorAll('.horizon-content');
  
  horizonTabs.forEach((tab, idx) => {
    tab.addEventListener('click', () => {
      horizonTabs.forEach(t => t.classList.remove('active'));
      horizonPanels.forEach(p => p.classList.remove('active'));
      
      tab.classList.add('active');
      const panelId = tab.getAttribute('aria-controls');
      const panel = document.getElementById(panelId);
      if (panel) {
        panel.classList.add('active');
      }
    });
  });
  
  // Technical details toggle
  const techToggle = document.getElementById('tech-toggle-pred');
  const techContent = document.getElementById('tech-content-pred');
  
  if (techToggle && techContent) {
    techToggle.addEventListener('click', () => {
      techContent.classList.toggle('show');
      techToggle.textContent = techContent.classList.contains('show') 
        ? '▲ Technical Details & Raw Data'
        : '▼ Technical Details & Raw Data';
    });
  }
  
  // Export buttons
  const exportJsonBtn = document.getElementById('export-pred-json');
  const exportCsvBtn = document.getElementById('export-pred-csv');
  
  if (exportJsonBtn) {
    exportJsonBtn.addEventListener('click', () => exportPrediction('json', data, machineId));
  }
  
  if (exportCsvBtn) {
    exportCsvBtn.addEventListener('click', () => exportPrediction('csv', data, machineId));
  }
}

function exportPrediction(format, data, machineId) {
  const predictions = data.predictions || [data];
  let content, filename, type;
  
  if (format === 'json') {
    content = JSON.stringify(data, null, 2);
    filename = `prediction_${machineId}_${Date.now()}.json`;
    type = 'application/json';
  } else if (format === 'csv') {
    let csv = 'Timestamp,Machine_ID,Horizon,Failure_Probability,Anomaly_Score,Confidence,Status\n';
    predictions.forEach(pred => {
      const failureProb = (pred.failure_probability || 0) * 100;
      const status = failureProb > RISK_THRESHOLDS.failure.high ? 'High Risk' : 
                    failureProb > RISK_THRESHOLDS.failure.medium ? 'Medium Risk' : 'Low Risk';
      csv += `${new Date().toISOString()},${machineId},${pred.horizon || 'N/A'},${pred.failure_probability},${pred.anomaly_score},${pred.confidence},${status}\n`;
    });
    content = csv;
    filename = `prediction_${machineId}_${Date.now()}.csv`;
    type = 'text/csv';
  }
  
  downloadFile(content, filename, type);
  showToast(`${format.toUpperCase()} file downloaded successfully`, 'success');
}

// ============================================
// Anomaly Detection
// ============================================
async function detectAnomaly(event) {
  event.preventDefault();
  
  const machineId = document.getElementById('anomalyMachineId').value.trim();
  
  if (!machineId) {
    showToast('Please enter a machine ID', 'warning');
    return;
  }
  
  showLoading('anomalyLoading', true);
  hideStatus('anomalyStatus');
  document.getElementById('anomalyResult').innerHTML = '';
  
  try {
    const cacheKey = `anomaly_${machineId}`;
    const data = await cachedRequest(cacheKey, '/predict', {
      method: 'POST',
      body: {
        machine_id: machineId,
        include_anomaly: true,
        include_factors: true
      }
    });
    
    showStatus('anomalyStatus', '✓ Anomaly detection analysis complete!', 'success');
    renderAnomalyDashboard(data, machineId);
    
  } catch (error) {
    showToast(error.message, 'error');
    showStatus('anomalyStatus', `✕ Anomaly detection failed: ${error.message}`, 'error');
    
    // Show empty state
    const container = document.getElementById('anomalyResult');
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">🔍</div>
        <div class="empty-state-title">No Anomaly Data</div>
        <div class="empty-state-description">${escapeHtml(error.message)}</div>
      </div>
    `;
  } finally {
    showLoading('anomalyLoading', false);
  }
}

// ============================================
// Render Anomaly Dashboard
// ============================================
function renderAnomalyDashboard(data, machineId) {
  const container = document.getElementById('anomalyResult');
  const predictions = data.predictions || [data];
  const pred = predictions[0] || data;
  
  const anomalyScore = (pred.anomaly_score || 0) * 100;
  const failureProb = (pred.failure_probability || 0) * 100;
  const confidence = (pred.confidence || 0) * 100;
  
  // Determine overall status
  let statusClass = 'status-normal';
  let statusIcon = '🟢';
  let statusText = 'NORMAL - Equipment operating within expected parameters';
  let anomalyDescription = 'All sensors are operating within normal ranges';
  
  if (anomalyScore > RISK_THRESHOLDS.anomaly.high) {
    statusClass = 'status-alert';
    statusIcon = '🔴';
    statusText = 'HIGH ANOMALY - Immediate investigation required';
    anomalyDescription = 'Significant deviation detected - immediate attention required';
  } else if (anomalyScore > RISK_THRESHOLDS.anomaly.medium) {
    statusClass = 'status-warning';
    statusIcon = '🟡';
    statusText = 'MODERATE ANOMALY - Monitoring recommended';
    anomalyDescription = 'Unusual patterns detected - schedule inspection';
  } else if (anomalyScore > RISK_THRESHOLDS.anomaly.low) {
    anomalyDescription = 'Minor variations detected - continue monitoring';
  }
  
  const anomalyRisk = getRiskLevel(anomalyScore, RISK_THRESHOLDS.anomaly);
  const failureRisk = getRiskLevel(failureProb, RISK_THRESHOLDS.failure);
  const confLevel = getConfidenceLevel(pred.confidence || 0);
  
  let html = `
    <div class="prediction-dashboard">
      <div class="prediction-header">
        <div class="prediction-title">🔍 Anomaly Detection: ${escapeHtml(machineId)}</div>
        <div class="model-info">
          Model: ${escapeHtml(data.model_version || 'Isolation Forest v1.0')} | 
          Analyzed: ${formatDate(new Date())}
        </div>
      </div>
      
      <div class="status-banner ${statusClass}">
        <span style="font-size: 1.5rem;">${statusIcon}</span>
        <span>${statusText}</span>
      </div>
      
      <div class="horizon-content active">
        <div class="metric-grid">
          <div class="metric-card" style="border-left-color: var(--color-risk-${anomalyRisk.level});">
            <div class="metric-label">Anomaly Score</div>
            <div class="metric-value">${anomalyScore.toFixed(1)}%</div>
            <span class="risk-badge risk-${anomalyRisk.level}">${anomalyRisk.icon} ${anomalyRisk.text}</span>
          </div>
          
          <div class="metric-card" style="border-left-color: var(--color-risk-${failureRisk.level});">
            <div class="metric-label">Failure Risk</div>
            <div class="metric-value">${formatPercent(pred.failure_probability)}</div>
            <span class="risk-badge risk-${failureRisk.level}">${failureRisk.icon} ${failureRisk.text} Risk</span>
          </div>
          
          <div class="metric-card">
            <div class="metric-label">Detection Confidence</div>
            <div class="metric-value">${confidence.toFixed(0)}%</div>
            <div class="confidence-meter">
              <div class="confidence-bar">
                <div class="confidence-fill ${confLevel.class}" style="width: ${confidence}%"></div>
              </div>
            </div>
          </div>
        </div>
        
        <div style="background: var(--color-bg-section); padding: 15px; border-radius: var(--radius-md); margin-top: var(--spacing-lg); border-left: 4px solid var(--color-risk-${anomalyRisk.level});">
          <div style="font-weight: var(--font-weight-semibold); color: var(--color-gray-800); margin-bottom: 8px;">
            📋 Assessment
          </div>
          <div style="color: var(--color-gray-700); line-height: 1.6;">
            ${anomalyDescription}
          </div>
        </div>
        
        <div class="factors-container">
          <div class="factors-title">📊 Anomaly Score Breakdown</div>
          <div class="factor-bar">
            <div class="factor-label">
              <span>Overall Anomaly Level</span>
              <span>${anomalyScore.toFixed(1)}%</span>
            </div>
            <div class="factor-progress">
              <div class="factor-fill" style="width: ${anomalyScore}%; background: linear-gradient(90deg, var(--color-risk-${anomalyRisk.level}) 0%, var(--color-risk-${anomalyRisk.level}) 100%);">
                ${anomalyScore.toFixed(1)}%
              </div>
            </div>
          </div>
        </div>
  `;
  
  // Top contributing sensors
  if (pred.top_factors && pred.top_factors.length > 0) {
    html += `
      <div class="factors-container">
        <div class="factors-title">🔧 Sensors Contributing to Anomaly</div>
    `;
    
    pred.top_factors.slice(0, 5).forEach(factor => {
      const fullName = formatFeatureName(factor.feature);
      const shortName = fullName.length > 30 ? fullName.substring(0, 27) + '...' : fullName;
      const importance = factor.importance * 100;
      
      html += `
        <div class="factor-bar">
          <div class="factor-label">
            <span class="tooltip">
              ${escapeHtml(shortName)}
              <span class="tooltip-text">${escapeHtml(fullName)}</span>
            </span>
            <span>${importance.toFixed(1)}%</span>
          </div>
          <div class="factor-progress">
            <div class="factor-fill" style="width: ${importance}%">
              ${importance.toFixed(0)}%
            </div>
          </div>
        </div>
      `;
    });
    
    html += `</div>`;
  }
  
  // Recommendations
  html += `
    <div class="factors-container">
      <div class="factors-title">💡 Recommendations</div>
      <div style="background: white; padding: 15px; border-radius: var(--radius-md);">
  `;
  
  if (anomalyScore > RISK_THRESHOLDS.anomaly.high) {
    html += `
      <div style="margin-bottom: 10px; padding: 10px; background: var(--color-error-light); border-left: 3px solid var(--color-error); border-radius: var(--radius-sm);">
        <strong>🔴 Immediate Action Required:</strong><br>
        • Stop machine and conduct thorough inspection<br>
        • Check sensors listed above for malfunctions<br>
        • Contact maintenance team immediately
      </div>
    `;
  } else if (anomalyScore > RISK_THRESHOLDS.anomaly.medium) {
    html += `
      <div style="margin-bottom: 10px; padding: 10px; background: var(--color-warning-light); border-left: 3px solid var(--color-warning); border-radius: var(--radius-sm);">
        <strong>🟡 Monitoring Required:</strong><br>
        • Schedule inspection within 24 hours<br>
        • Increase monitoring frequency<br>
        • Review sensor data for patterns
      </div>
    `;
  } else {
    html += `
      <div style="margin-bottom: 10px; padding: 10px; background: var(--color-success-light); border-left: 3px solid var(--color-success); border-radius: var(--radius-sm);">
        <strong>🟢 Preventive Measures:</strong><br>
        • Continue regular monitoring schedule<br>
        • Maintain routine maintenance procedures<br>
        • Document any minor variations for trend analysis
      </div>
    `;
  }
  
  html += `
      </div>
    </div>
  `;
  
  // Technical details
  html += `
    <div class="technical-details">
      <div class="technical-toggle" id="tech-toggle-anomaly">
        ▼ Technical Details & Raw Data
      </div>
      <div class="technical-content" id="tech-content-anomaly">
        <pre>${escapeHtml(JSON.stringify(data, null, 2))}</pre>
      </div>
    </div>
  `;
  
  // Export buttons
  html += `
    <div class="export-buttons">
      <button class="export-btn" id="export-anomaly-json">
        📄 Download JSON Report
      </button>
      <button class="export-btn" id="export-anomaly-csv">
        📊 Download CSV Report
      </button>
    </div>
  `;
  
  html += `</div></div>`;
  container.innerHTML = html;
  
  // Attach event listeners
  attachAnomalyEventListeners(data, machineId);
  
  // Store data for export
  window.anomalyData = data;
}

function attachAnomalyEventListeners(data, machineId) {
  // Technical details toggle
  const techToggle = document.getElementById('tech-toggle-anomaly');
  const techContent = document.getElementById('tech-content-anomaly');
  
  if (techToggle && techContent) {
    techToggle.addEventListener('click', () => {
      techContent.classList.toggle('show');
      techToggle.textContent = techContent.classList.contains('show') 
        ? '▲ Technical Details & Raw Data'
        : '▼ Technical Details & Raw Data';
    });
  }
  
  // Export buttons
  const exportJsonBtn = document.getElementById('export-anomaly-json');
  const exportCsvBtn = document.getElementById('export-anomaly-csv');
  
  if (exportJsonBtn) {
    exportJsonBtn.addEventListener('click', () => exportAnomaly('json', data, machineId));
  }
  
  if (exportCsvBtn) {
    exportCsvBtn.addEventListener('click', () => exportAnomaly('csv', data, machineId));
  }
}

function exportAnomaly(format, data, machineId) {
  const pred = (data.predictions && data.predictions[0]) || data;
  let content, filename, type;
  
  if (format === 'json') {
    content = JSON.stringify(data, null, 2);
    filename = `anomaly_detection_${machineId}_${Date.now()}.json`;
    type = 'application/json';
  } else if (format === 'csv') {
    let csv = 'Timestamp,Machine_ID,Anomaly_Score,Failure_Probability,Confidence,Status\n';
    const anomalyScore = (pred.anomaly_score || 0) * 100;
    const status = anomalyScore > RISK_THRESHOLDS.anomaly.high ? 'High Anomaly' : 
                  anomalyScore > RISK_THRESHOLDS.anomaly.medium ? 'Moderate Anomaly' : 'Normal';
    csv += `${new Date().toISOString()},${machineId},${pred.anomaly_score},${pred.failure_probability},${pred.confidence},${status}\n`;
    content = csv;
    filename = `anomaly_detection_${machineId}_${Date.now()}.csv`;
    type = 'text/csv';
  }
  
  downloadFile(content, filename, type);
  showToast(`${format.toUpperCase()} report downloaded successfully`, 'success');
}

// ============================================
// AI Chat
// ============================================
async function askQuestion(event) {
  event.preventDefault();
  
  const question = document.getElementById('chatQuestion').value.trim();
  
  if (!question) {
    showToast('Please enter a question', 'warning');
    return;
  }
  
  showLoading('chatLoading', true);
  hideStatus('chatStatus');
  document.getElementById('chatResult').innerHTML = '';
  
  try {
    const data = await request('/chat', {
      method: 'POST',
      body: { question }
    });
    
    showStatus('chatStatus', '✓ Answer generated successfully', 'success');
    renderChatAnswer(data);
    
  } catch (error) {
    showToast(error.message, 'error');
    showStatus('chatStatus', `✕ Chat failed: ${error.message}`, 'error');
    
    // Show empty state
    const container = document.getElementById('chatResult');
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">💬</div>
        <div class="empty-state-title">No Answer Available</div>
        <div class="empty-state-description">${escapeHtml(error.message)}</div>
      </div>
    `;
  } finally {
    showLoading('chatLoading', false);
  }
}

// ============================================
// Render Chat Answer
// ============================================
function renderChatAnswer(data) {
  const container = document.getElementById('chatResult');
  const confidence = data.confidence || 0;
  const confLevel = getConfidenceLevel(confidence);
  
  let html = `
    <div class="chat-answer-container">
      <div class="chat-answer-header">
        <div class="chat-answer-title">🤖 Answer</div>
        <span class="confidence-badge ${confLevel.class}">
          ${confLevel.icon} ${confLevel.text} Confidence (${(confidence * 100).toFixed(0)}%)
        </span>
      </div>
      
      <div class="chat-answer-text">
        ${escapeHtml(data.answer)}
      </div>
  `;
  
  // Source citations (top 3)
  if (data.sources && data.sources.length > 0) {
    html += `
      <div class="source-citations">
        <div class="citations-title">📚 Sources Referenced:</div>
    `;
    
    data.sources.slice(0, 3).forEach((source, idx) => {
      const relevance = ((source.relevance_score || 0) * 100).toFixed(0);
      html += `
        <div class="citation-item">
          <span class="citation-number">${idx + 1}</span>
          <span class="citation-title">${escapeHtml(source.title || 'Unknown')}</span>
          <span class="citation-relevance">${relevance}%</span>
        </div>
      `;
    });
    
    html += `</div>`;
  }
  
  html += `</div>`;
  container.innerHTML = html;
}

// ============================================
// Alerts
// ============================================
async function getAlerts(event) {
  event.preventDefault();
  
  showLoading('alertsLoading', true);
  hideStatus('alertsStatus');
  document.getElementById('alertsResult').innerHTML = '';
  
  try {
    const data = await request('/alerts?limit=10');
    
    if (data.alerts && data.alerts.length > 0) {
      showStatus('alertsStatus', `✓ Found ${data.alerts.length} alert(s)`, 'success');
      renderAlerts(data.alerts);
    } else {
      showStatus('alertsStatus', '✓ No active alerts', 'success');
      document.getElementById('alertsResult').innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">🔔</div>
          <div class="empty-state-title">No Active Alerts</div>
          <div class="empty-state-description">All systems operating normally</div>
        </div>
      `;
    }
    
  } catch (error) {
    showToast(error.message, 'error');
    showStatus('alertsStatus', `✕ Failed to load alerts: ${error.message}`, 'error');
    
    document.getElementById('alertsResult').innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">⚠️</div>
        <div class="empty-state-title">Unable to Load Alerts</div>
        <div class="empty-state-description">${escapeHtml(error.message)}</div>
      </div>
    `;
  } finally {
    showLoading('alertsLoading', false);
  }
}

function renderAlerts(alerts) {
  const container = document.getElementById('alertsResult');
  
  let html = '<div style="margin-top: 15px;">';
  
  alerts.forEach(alert => {
    const severity = alert.severity || 'info';
    const severityClass = severity === 'critical' ? 'error' : severity;
    const severityIcon = severity === 'critical' ? '🔴' : severity === 'warning' ? '🟡' : '🔵';
    
    html += `
      <div class="status ${severityClass} show" style="margin-bottom: 10px;">
        <div style="display: flex; justify-content: space-between; align-items: start;">
          <div>
            <div style="font-weight: var(--font-weight-semibold); margin-bottom: 5px;">
              ${severityIcon} ${escapeHtml(alert.machine_id || 'Unknown Machine')}
            </div>
            <div>${escapeHtml(alert.message || 'No message')}</div>
            <div style="font-size: var(--font-size-sm); opacity: 0.8; margin-top: 5px;">
              ${formatDate(alert.created_at || new Date())}
            </div>
          </div>
        </div>
      </div>
    `;
  });
  
  html += '</div>';
  container.innerHTML = html;
}

// ============================================
// Utility Functions
// ============================================
function downloadFile(content, filename, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

// ============================================
// Application Initialization
// ============================================
async function initApp() {
  console.log('🚀 Initializing AI-Powered Predictive Maintenance Platform...');
  
  // Load configuration
  await loadConfig();
  
  // Initialize tabs
  initTabs();
  
  // Start health check
  startHealthCheck();
  
  // Attach form event listeners
  const uploadForm = document.getElementById('uploadForm');
  if (uploadForm) {
    uploadForm.addEventListener('submit', handleFileUpload);
  }
  
  const generateBtn = document.getElementById('generateSampleBtn');
  if (generateBtn) {
    generateBtn.addEventListener('click', generateSampleData);
  }
  
  const manualHealthCheck = document.getElementById('manualHealthCheck');
  if (manualHealthCheck) {
    manualHealthCheck.addEventListener('click', () => {
      checkHealth();
      showToast('Health check initiated', 'info', 2000);
    });
  }
  
  const quickPredictBtn = document.getElementById('quickPredictBtn');
  if (quickPredictBtn) {
    quickPredictBtn.addEventListener('click', (e) => {
      const machineId = document.getElementById('quickMachineId').value.trim();
      if (!machineId) {
        showToast('Please enter a machine ID', 'warning');
        return;
      }
      // Copy to prediction form and switch tabs
      document.getElementById('predictionMachineId').value = machineId;
      const predTab = document.getElementById('tab-predictions');
      if (predTab) {
        predTab.click();
      }
      // Trigger prediction
      const predForm = document.getElementById('predictionForm');
      if (predForm) {
        predForm.dispatchEvent(new Event('submit'));
      }
    });
  }
  
  const predictionForm = document.getElementById('predictionForm');
  if (predictionForm) {
    predictionForm.addEventListener('submit', getPrediction);
  }
  
  const anomalyForm = document.getElementById('anomalyForm');
  if (anomalyForm) {
    anomalyForm.addEventListener('submit', detectAnomaly);
  }
  
  const chatForm = document.getElementById('chatForm');
  if (chatForm) {
    chatForm.addEventListener('submit', askQuestion);
  }
  
  const alertsBtn = document.getElementById('getAlertsBtn');
  if (alertsBtn) {
    alertsBtn.addEventListener('click', getAlerts);
  }
  
  console.log('✓ Application initialized successfully');
  showToast('Platform ready', 'success', 3000);
}

// ============================================
// Start Application
// ============================================
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
  stopHealthCheck();
});

// Export public API
window.PredictiveMaintenance = {
  initApp,
  request,
  showToast,
  showStatus,
  showLoading,
  formatPercent,
  formatDate,
  renderPredictionDashboard,
  renderAnomalyDashboard,
  renderChatAnswer
};

