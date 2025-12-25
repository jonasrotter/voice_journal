# Voice Journal UI

Vanilla JavaScript frontend with Web Audio API recording and custom SPA routing.

## Quick Start

```bash
# Development (with API on localhost:8000)
python -m http.server 3000

# Or with hot reload
npx live-server --port=3000
```

**App**: http://localhost:3000

## Architecture

```
ui/
├── api/
│   ├── client.js          # HTTP client, auth headers, token management
│   └── types.js           # JSDoc type definitions
├── auth/
│   ├── Login.js           # Login/register form component
│   └── state.js           # Auth state management
├── components/
│   ├── Header.js          # Navigation header
│   └── toast.js           # Toast notifications
├── entries/
│   ├── EntriesList.js     # Paginated entry list with polling
│   └── EntryCard.js       # Entry display (transcript, summary, emotion)
├── recording/
│   ├── recorder.js        # Web Audio API recording
│   ├── RecordingPanel.js  # Record button & controls
│   └── Waveform.js        # Audio waveform visualization
├── settings/
│   └── Settings.js        # User preferences
├── router.js              # Client-side SPA router
├── main.js                # App entry point
├── styles.css             # Global styles (CSS variables)
├── index.html             # HTML shell
├── nginx.conf             # Production proxy config
└── Dockerfile             # Container image
```

## Key Features

| Feature | Implementation |
|---------|----------------|
| Recording | Web Audio API + MediaRecorder |
| Waveform | Canvas + AnalyserNode |
| Routing | Custom pushState router |
| Auth | JWT in localStorage |
| Styling | CSS Variables theming |

## API Configuration

**Development**: Auto-detects port 3000/5173 → proxies to `localhost:8000`

**Production**: Nginx proxies `/api/*` to backend Container App

## Docker

```bash
# Build
docker build -t voice-journal-ui .

# Run (set API backend URL)
docker run -p 80:80 \
  -e API_URL=https://your-api.azurecontainerapps.io \
  -e API_HOST=your-api.azurecontainerapps.io \
  voice-journal-ui
```

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `API_URL` | Backend API base URL | `https://ca-api.azurecontainerapps.io` |
| `API_HOST` | Backend hostname (for Host header) | `ca-api.azurecontainerapps.io` |

## Component Usage

### Recording
```javascript
import { startRecording, stopRecording } from './recording/recorder.js';

await startRecording();
const blob = await stopRecording(); // Returns audio Blob
```

### API Client
```javascript
import { api } from './api/client.js';

await api.auth.login(email, password);
await api.entries.upload(audioBlob);
const entries = await api.entries.list(page, pageSize);
```

### Router
```javascript
import { navigateTo, registerRoutes } from './router.js';

registerRoutes({
  '/': renderHome,
  '/login': renderLogin,
  '/settings': renderSettings
});

navigateTo('/login');
```
