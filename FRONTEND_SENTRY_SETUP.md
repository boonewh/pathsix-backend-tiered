# Frontend Sentry Setup Instructions

We are implementing Sentry for error tracking and performance monitoring. The backend is already configured. Please implement Sentry in the React frontend to enable **Distributed Tracing** (connecting frontend actions to backend errors).

## 1. Get the Frontend DSN
*   Log into Sentry.io
*   Create a new project: **React**
*   Name: `pathsix-frontend`
*   Copy the **DSN** string.

## 2. Install Sentry
```bash
npm install @sentry/react
```

## 3. Initialize in `src/main.tsx` (or `index.tsx`)

Add this code **before** you render the React app.

```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import * as Sentry from "@sentry/react";

// Initialize Sentry
Sentry.init({
  dsn: "YOUR_NEW_FRONTEND_DSN_HERE", // <--- PASTE THE NEW DSN HERE
  
  integrations: [
    Sentry.browserTracingIntegration(),
    Sentry.replayIntegration(),
  ],

  // Performance Monitoring
  tracesSampleRate: 1.0, // Capture 100% of transactions for now
  
  // Set 'tracePropagationTargets' to control for which URLs distributed tracing should be enabled
  // This connects the frontend trace to the backend trace.
  // Add your backend API URL here.
  tracePropagationTargets: [
    "localhost", 
    /^https:\/\/your-backend-api\.com\/api/, // <--- UPDATE THIS with real Prod URL
    /^https:\/\/pathsix-backend\.fly\.dev\/api/ // Example
  ],

  // Session Replay
  replaysSessionSampleRate: 0.1, 
  replaysOnErrorSampleRate: 1.0, 
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

## 4. Verify
1.  Start the app.
2.  Throw a test error in a component (e.g., `<button onClick={() => { throw new Error("Frontend Test Error"); }}>Break me</button>`).
3.  Check Sentry dashboard to see the error.
4.  Make an API call to the backend and check the **Performance** tab in Sentry to see if the transaction links Frontend -> Backend.
