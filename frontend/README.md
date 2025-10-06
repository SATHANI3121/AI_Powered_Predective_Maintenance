# AI-Powered Predictive Maintenance - Frontend

Modern, accessible, and maintainable frontend built with **Vanilla JavaScript** (no frameworks) following best practices for performance, accessibility, and code quality.

## 🏗️ Architecture

```
frontend/
├── index.html              # Semantic HTML with ARIA attributes
├── config.json             # Configuration (API base URL, API key, timeouts)
├── styles/
│   └── app.css            # All styles with CSS variables
├── scripts/
│   └── app.js             # All JavaScript with proper structure
├── README.md              # This file
└── TESTING_CHECKLIST.md   # Comprehensive testing guide
```

### Key Design Principles

1. **Separation of Concerns**: HTML, CSS, and JS are completely separated
2. **Accessibility First**: WCAG 2.1 AA compliant with full keyboard navigation
3. **Progressive Enhancement**: Works without JavaScript (forms still submit)
4. **Performance**: Deferred scripts, CSS transitions, request caching
5. **Maintainability**: Centralized configuration, DRY code, clear naming

---

## 🎨 Features

### ✅ Implemented

- **📤 Data Upload**: Upload sensor CSV files or generate sample data
- **🔮 Predictions**: Multi-horizon failure predictions with visual dashboards
- **🔍 Anomaly Detection**: Real-time anomaly scoring with recommendations
- **💬 AI Chat**: Question-answering system with confidence scores and citations
- **🔔 Alerts**: View critical warnings and alerts for all machines
- **🏥 Health Check**: Automatic system status monitoring with graceful offline handling

### 🎯 UI/UX Enhancements

- **Toast Notifications**: Non-blocking, auto-dismissing notifications
- **Empty States**: Clear messages when no data is available
- **Status Banners**: Color-coded alerts (🟢 Normal / 🟡 Warning / 🔴 Alert)
- **Risk Indicators**: Visual badges and progress bars for risk levels
- **Feature Tooltips**: Hover to see full feature names
- **Export Options**: Download JSON/CSV reports
- **Responsive Design**: Mobile-first, works on all screen sizes

---

## 🚀 Quick Start

### 1. Configuration

Create or update `config.json`:

```json
{
  "API_BASE": "/api/v1",
  "API_KEY": "",
  "USE_API_KEY": false,
  "HEALTH_CHECK_INTERVAL": 30000,
  "CACHE_DURATION": 30000,
  "REQUEST_TIMEOUT": 30000
}
```

**For local development with API key:**

```json
{
  "API_BASE": "http://localhost:8000/api/v1",
  "API_KEY": "dev-CHANGE-ME",
  "USE_API_KEY": true,
  "HEALTH_CHECK_INTERVAL": 30000,
  "CACHE_DURATION": 30000,
  "REQUEST_TIMEOUT": 30000
}
```

### 2. Start a Local Server

#### Option A: Python HTTP Server

```bash
cd frontend
python -m http.server 3000
```

Then open: http://localhost:3000

#### Option B: Node.js HTTP Server

```bash
cd frontend
npx http-server -p 3000
```

#### Option C: VS Code Live Server

Install the "Live Server" extension and right-click `index.html` → "Open with Live Server"

---

## 🎹 Keyboard Navigation

All features are fully keyboard-accessible:

| Key | Action |
|-----|--------|
| **Tab** | Move to next interactive element |
| **Shift + Tab** | Move to previous element |
| **Enter / Space** | Activate buttons and links |
| **Arrow Left** | Previous tab |
| **Arrow Right** | Next tab |
| **Home** | First tab |
| **End** | Last tab |

---

## ♿ Accessibility Features

### WCAG 2.1 AA Compliant

- ✅ Semantic HTML (`<main>`, `<section>`, `<article>`)
- ✅ Proper heading hierarchy (h1 → h2 → h3)
- ✅ ARIA roles and attributes (`role="tablist"`, `aria-live`, etc.)
- ✅ Keyboard navigation with focus management
- ✅ Screen reader announcements for status updates
- ✅ Visible focus indicators (2px outline)
- ✅ Sufficient color contrast (4.5:1 for normal text)
- ✅ Alternative text for icons and images
- ✅ Form labels and error associations

### Testing with Screen Readers

**Windows:**
- NVDA (free): https://www.nvaccess.org/
- JAWS (commercial): https://www.freedomscientific.com/

**Mac:**
- VoiceOver: Press `Cmd + F5`

**Chrome Extension:**
- ChromeVox: https://chrome.google.com/webstore

---

## 🎨 Theming & Customization

All theme colors are defined as CSS variables in `styles/app.css`:

```css
:root {
  --color-primary: #667eea;
  --color-success: #48bb78;
  --color-warning: #ed8936;
  --color-error: #f56565;
  /* ... and many more */
}
```

**To customize the theme:**

1. Open `frontend/styles/app.css`
2. Modify the CSS variables in the `:root` selector
3. Refresh the page (no build step required)

### Dark Theme Example

```css
:root {
  --color-bg-body: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
  --color-bg-card: #2d3748;
  --color-gray-700: #e2e8f0;
  /* ... update other colors */
}
```

---

## 🔧 API Integration

### Request Helper

All API calls go through the `request()` helper:

```javascript
// GET request
const data = await request('/alerts?limit=10');

// POST request with JSON body
const prediction = await request('/predict', {
  method: 'POST',
  body: {
    machine_id: 'M-001',
    include_anomaly: true
  }
});

// POST with FormData (file upload)
const formData = new FormData();
formData.append('file', fileInput.files[0]);
const result = await request('/ingest', {
  method: 'POST',
  body: formData
});
```

### Caching

Use `cachedRequest()` to avoid duplicate calls:

```javascript
const cacheKey = `prediction_${machineId}`;
const data = await cachedRequest(cacheKey, '/predict', options);
// Cached for 30 seconds (configurable in config.json)
```

### Error Handling

Errors are automatically caught and displayed via toasts + status areas:

```javascript
try {
  const data = await request('/predict', { method: 'POST', body: { ... } });
  showToast('Prediction successful!', 'success');
} catch (error) {
  showToast(error.message, 'error');
  // Error details shown in status area
}
```

---

## 📊 Risk Thresholds

Centralized in `scripts/app.js`:

```javascript
const RISK_THRESHOLDS = {
  failure: {
    high: 70,    // > 70% = High risk 🔴
    medium: 30   // > 30% = Medium risk 🟡
  },
  anomaly: {
    high: 80,    // > 80% = High anomaly 🔴
    medium: 50,  // > 50% = Moderate anomaly 🟡
    low: 20      // > 20% = Low anomaly 🟢
  },
  confidence: {
    high: 70,    // > 70% = High confidence 🟢
    medium: 50   // > 50% = Medium confidence 🟡
  }
};
```

**To adjust thresholds:**

1. Edit the values in `scripts/app.js`
2. Refresh the page
3. New thresholds apply across all dashboards

---

## 🧪 Testing

See `TESTING_CHECKLIST.md` for a comprehensive testing guide covering:

- ✅ Accessibility (keyboard, screen reader, ARIA)
- ✅ UX enhancements (toasts, empty states, formatting)
- ✅ Code quality (no inline handlers, unified error handling)
- ✅ Performance (caching, debouncing, deferred scripts)
- ✅ Feature-specific tests (upload, prediction, anomaly, chat, alerts)
- ✅ Browser compatibility
- ✅ Responsive design
- ✅ Error handling

### Quick Test Commands

```bash
# Run local server
python -m http.server 3000

# Test keyboard navigation
# (Unplug mouse, use Tab/Arrow keys only)

# Test with screen reader
# (Enable NVDA/JAWS/VoiceOver and navigate)

# Test network failures
# (DevTools → Network → Offline)

# Test caching
# (Make same API call twice within 30s, check Network tab)
```

---

## 📦 Public API

The application exposes a global API for programmatic access:

```javascript
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
```

**Example usage in browser console:**

```javascript
// Show a custom toast
PredictiveMaintenance.showToast('Custom message', 'success');

// Make an API request
const data = await PredictiveMaintenance.request('/alerts');
console.log(data);

// Format a percentage
const formatted = PredictiveMaintenance.formatPercent(0.000005);
// Returns: "<0.01%"
```

---

## 🐛 Troubleshooting

### Issue: "Cannot connect to server"

**Solution:**
1. Ensure the API server is running (`python -m uvicorn api.main:app --host 0.0.0.0 --port 8000`)
2. Check `config.json` → `API_BASE` points to correct URL
3. Check browser console for CORS errors
4. Verify health check endpoint: http://localhost:8000/healthz

### Issue: "Invalid API key"

**Solution:**
1. Check `config.json` → `USE_API_KEY` is `true`
2. Verify `API_KEY` matches your `.env` file
3. Check API server logs for authentication errors

### Issue: "Request timeout"

**Solution:**
1. Increase `REQUEST_TIMEOUT` in `config.json` (default: 30000 ms)
2. Check API server performance (may be processing large datasets)
3. Verify network connection

### Issue: Tabs not switching

**Solution:**
1. Check browser console for JavaScript errors
2. Ensure `scripts/app.js` is loaded (check Network tab)
3. Clear browser cache and reload

### Issue: Styles not applied

**Solution:**
1. Ensure `styles/app.css` exists and is accessible
2. Check Network tab for 404 errors on CSS file
3. Verify relative paths are correct
4. Clear browser cache

---

## 🚀 Performance Tips

1. **Enable HTTP/2**: Faster parallel downloads of CSS/JS
2. **Use CDN**: Host static files on a CDN for global distribution
3. **Gzip/Brotli**: Enable compression on web server
4. **Service Worker**: Cache assets for offline support (future enhancement)
5. **Code Splitting**: Load modules on demand (future enhancement)

---

## 📝 Code Style

- **Indentation**: 2 spaces
- **Quotes**: Single quotes for JS, double for HTML attributes
- **Naming**: camelCase for JS, kebab-case for CSS classes
- **Comments**: JSDoc style for functions, inline for complex logic
- **Max line length**: 120 characters

---

## 🤝 Contributing

1. Follow the existing code style
2. Add tests to `TESTING_CHECKLIST.md` for new features
3. Ensure accessibility compliance (test with keyboard + screen reader)
4. Update this README if adding new features
5. No inline styles or scripts in HTML

---

## 📄 License

Same as parent project.

---

## 🙏 Acknowledgments

- **FastAPI**: Backend framework
- **WCAG**: Web accessibility guidelines
- **WAI-ARIA**: Accessible Rich Internet Applications spec
- **MDN Web Docs**: Excellent documentation and examples

---

**Built with ❤️ by the Senior Frontend Engineering team**
