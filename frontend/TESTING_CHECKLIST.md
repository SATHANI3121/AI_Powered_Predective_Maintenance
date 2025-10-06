# Frontend Refactoring - Testing Checklist

## Architecture & Configuration

- [x] All CSS moved to `styles/app.css`
- [x] All JavaScript moved to `scripts/app.js`
- [x] Configuration loaded from `/config.json` with fallback defaults
- [x] No hardcoded API keys in source code
- [x] CSS variables defined for theme customization

## Accessibility (WCAG 2.1 AA Compliance)

### Semantic HTML
- [ ] Verify `<main>`, `<section>`, `<article>`, `<header>`, `<footer>` tags are used correctly
- [ ] Check heading hierarchy (h1 → h2 → h3)
- [ ] Ensure forms use proper `<label>` associations

### ARIA Implementation
- [ ] Tab navigation implements `role="tablist"`, `role="tab"`, `role="tabpanel"`
- [ ] Tabs have correct `aria-selected`, `aria-controls`, `aria-labelledby`
- [ ] Hidden panels have `aria-hidden="true"`
- [ ] Status regions have `aria-live="polite"` or `aria-live="assertive"`
- [ ] Interactive elements have appropriate `aria-label` or `aria-describedby`

### Keyboard Navigation
- [ ] **Tab key** moves through all interactive elements in logical order
- [ ] **Left/Right arrow keys** switch between tabs
- [ ] **Home key** jumps to first tab
- [ ] **End key** jumps to last tab
- [ ] All buttons and links are keyboard-accessible
- [ ] Focus indicator is visible (2px outline)
- [ ] No keyboard traps exist

### Screen Reader Testing
- [ ] Tab names are announced correctly
- [ ] Tab panel content is announced when switching tabs
- [ ] Status messages are announced via `aria-live` regions
- [ ] Form labels and hints are read correctly
- [ ] Error messages are announced assertively
- [ ] Loading states are announced

**Tools to use:**
- NVDA (Windows): https://www.nvaccess.org/
- JAWS (Windows): https://www.freedomscientific.com/
- VoiceOver (Mac): Cmd+F5
- ChromeVox (Chrome extension)

## UX Enhancements

### Toast System
- [ ] Success toasts appear for successful operations
- [ ] Error toasts appear for failed operations
- [ ] Warning toasts appear for user input issues
- [ ] Toasts auto-dismiss after 5 seconds
- [ ] Close button works on toasts
- [ ] Multiple toasts stack correctly
- [ ] No `alert()` dialogs remain in code

### Formatting
- [ ] Percentages < 0.01% display as "<0.01%"
- [ ] Percentages >= 0.01% show correct decimals
- [ ] Dates are formatted using `toLocaleString()`
- [ ] Feature names are cleaned (no underscores, readable)
- [ ] Feature names have tooltips showing full text

### Risk Thresholds
- [ ] Failure probability thresholds: high > 70%, medium > 30%
- [ ] Anomaly score thresholds: high > 80%, medium > 50%, low > 20%
- [ ] Confidence thresholds: high > 70%, medium > 50%
- [ ] Color coding matches thresholds:
  - 🟢 Green = Low risk / Normal
  - 🟡 Yellow = Medium risk / Warning
  - 🔴 Red = High risk / Alert

### Empty States
- [ ] Prediction panel shows empty state before first prediction
- [ ] Anomaly panel shows empty state before first detection
- [ ] Chat panel shows empty state before first question
- [ ] Alerts panel shows "No active alerts" when empty
- [ ] Empty states have icon, title, and description

### Status Banners
- [ ] Overall status banner appears above horizon tabs
- [ ] Banner shows Normal / Warning / Alert based on thresholds
- [ ] Banner includes short "why" summary
- [ ] Banner color matches severity

### Feature Labels
- [ ] Top factors show shortened names (< 30 chars)
- [ ] Full feature names appear on hover (tooltip)
- [ ] Tooltips are keyboard-accessible
- [ ] Feature names are human-readable (e.g., "Temperature Avg 3 Mean")

## Code Quality

### No Inline Handlers
- [ ] Search HTML for `onclick=` (should be 0 results)
- [ ] Search HTML for `onsubmit=` (should be 0 results)
- [ ] Search HTML for `onchange=` (should be 0 results)
- [ ] All event listeners attached via `addEventListener` in JS

### Network Requests
- [ ] All API calls go through `request()` helper function
- [ ] Errors are caught and displayed via toasts + status areas
- [ ] Timeout is enforced (30 seconds default)
- [ ] JSON responses are automatically parsed
- [ ] API key is appended from config if `USE_API_KEY = true`

### Health Check
- [ ] Health check runs every 30 seconds (debounced)
- [ ] Offline state shows gracefully (🔴 System Offline)
- [ ] Toast appears only when status changes (online ↔ offline)
- [ ] Cache is cleared when coming back online

### Performance
- [ ] Scripts loaded with `defer` attribute
- [ ] No heavy inline styles in HTML
- [ ] CSS transitions used instead of JS animations
- [ ] Responses cached for 30 seconds per machine ID
- [ ] Duplicate API calls within 30s use cached data

## Feature-Specific Tests

### Data Upload
- [ ] File input accepts `.csv` files only
- [ ] Upload shows loading spinner
- [ ] Success toast shows number of records inserted
- [ ] Error toast shows specific error message
- [ ] File input is cleared after successful upload
- [ ] Prediction cache is cleared after upload
- [ ] "Generate Sample Data" downloads a CSV file

### Predictions
- [ ] Machine ID input is required
- [ ] Loading spinner appears during API call
- [ ] Dashboard renders with status banner
- [ ] Multi-horizon tabs appear if multiple predictions
- [ ] Horizon tabs are clickable
- [ ] Metric cards show correct values
- [ ] Top factors are displayed (up to 5)
- [ ] Technical details are collapsible
- [ ] Export JSON button works
- [ ] Export CSV button works
- [ ] Cache prevents duplicate calls within 30s

### Anomaly Detection
- [ ] Machine ID input is required
- [ ] Loading spinner appears during API call
- [ ] Dashboard renders with status banner
- [ ] Anomaly score breakdown is shown
- [ ] Contributing sensors are listed (up to 5)
- [ ] Recommendations match severity level:
  - High anomaly: Stop machine, inspect immediately
  - Moderate: Schedule inspection within 24h
  - Normal: Continue monitoring
- [ ] Technical details are collapsible
- [ ] Export JSON button works
- [ ] Export CSV button works

### AI Chat
- [ ] Question textarea is required
- [ ] Loading spinner appears during API call
- [ ] Answer is displayed in highlighted box
- [ ] Confidence badge shows correct level (High/Medium/Low)
- [ ] Top 3 sources are shown as citations
- [ ] Citation relevance percentage is shown
- [ ] No detailed source content is shown (just citations)

### Alerts
- [ ] "Load Alerts" button triggers API call
- [ ] Loading spinner appears
- [ ] Alerts are rendered with correct severity (🔴🟡🔵)
- [ ] Empty state shows "No Active Alerts" if none
- [ ] Each alert shows: machine ID, message, timestamp
- [ ] Timestamps are formatted correctly

## Browser Compatibility

Test in:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Edge (latest)
- [ ] Safari (latest, if available)

## Responsive Design

- [ ] Mobile (< 768px): Cards stack vertically
- [ ] Tablet (768px - 1024px): Cards show in grid
- [ ] Desktop (> 1024px): Full layout
- [ ] Toast notifications responsive on mobile
- [ ] Tab navigation wraps on narrow screens

## Error Handling

### Network Errors
- [ ] Timeout after 30s shows "Request timeout - please try again"
- [ ] 404 errors show "Not Found" message
- [ ] 500 errors show server error message
- [ ] Connection refused shows "Cannot connect to server"
- [ ] Errors do not crash the page

### Validation Errors
- [ ] Empty machine ID shows warning toast
- [ ] Empty question shows warning toast
- [ ] Invalid file type shows error toast
- [ ] Missing API key (if required) shows error

### Edge Cases
- [ ] Very small failure probability (0.000001) shows as "<0.01%"
- [ ] Missing `top_factors` doesn't break dashboard
- [ ] Missing `predictions` array handles single prediction object
- [ ] Missing `sources` doesn't break chat answer

## Performance Metrics

- [ ] Initial page load < 2 seconds
- [ ] API calls cached (check network tab for cache hits)
- [ ] Health check debounced (not fired on every event)
- [ ] No layout thrashing (check Performance tab)
- [ ] Animations run at 60fps

## Security

- [ ] API key not visible in source code (check Elements tab)
- [ ] API key not logged to console
- [ ] XSS protection: User input is escaped via `escapeHtml()`
- [ ] No `eval()` or `Function()` constructor usage

## Final Checks

- [ ] No console errors
- [ ] No console warnings
- [ ] All TODOs in code are resolved or documented
- [ ] README updated with new architecture
- [ ] Git commit with clear message

---

## Quick Testing Commands

### Test with Keyboard Only
1. Unplug mouse or don't use it
2. Press Tab to navigate through all elements
3. Press Enter/Space to activate buttons
4. Use Arrow keys in tab navigation
5. Verify all features are accessible

### Test with Screen Reader
1. Enable screen reader (NVDA/JAWS/VoiceOver)
2. Navigate through the page with Tab
3. Switch tabs and verify announcements
4. Submit a form and verify status announcements
5. Check that loading states are announced

### Test Network Failures
1. Open DevTools → Network tab
2. Set throttling to "Offline"
3. Try to make API calls
4. Verify graceful error messages
5. Set back to "Online"
6. Verify recovery message

### Test Caching
1. Make a prediction for machine M-001
2. Check Network tab for API call
3. Immediately make the same prediction again
4. Verify no new API call (cached)
5. Wait 31 seconds
6. Make prediction again
7. Verify new API call (cache expired)

---

**✅ All items checked = Frontend refactoring complete and production-ready!**

