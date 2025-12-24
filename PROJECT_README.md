# Voice Journal - Full Stack Application

A privacy-first voice journaling application with AI-powered transcription, summarization, and emotion detection.

## Project Structure

```
voice_journal/
├── api/                    # FastAPI Backend
│   ├── auth/              # Authentication (JWT, password hashing)
│   ├── users/             # User management
│   ├── entries/           # Journal entries CRUD
│   ├── ai/                # AI processing (transcription, summarization)
│   ├── db/                # Database (SQLAlchemy, PostgreSQL)
│   └── main.py            # FastAPI application
├── ui/                     # Vanilla JavaScript Frontend
│   ├── api/               # API client and types
│   ├── auth/              # Login/register components
│   ├── recording/         # Web Audio API recording
│   ├── entries/           # Entry list and card components
│   ├── settings/          # User settings
│   ├── components/        # Shared components (toast, header)
│   ├── main.js            # Application entry point
│   ├── router.js          # Client-side routing
│   ├── styles.css         # Global styles
│   └── index.html         # HTML entry point
├── tests/                  # Test suite
│   ├── test_auth.py       # Auth unit tests
│   ├── test_entries.py    # Entries unit tests
│   ├── test_users.py      # Users unit tests
│   ├── test_integration.py # API integration tests
│   ├── test_contracts.py  # Schema contract tests
│   └── conftest.py        # Test configuration
└── README.md
```

## Technology Stack

### Backend
- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: Custom JWT implementation (no external JWT library)
- **Password Hashing**: PBKDF2-SHA256
- **Validation**: Pydantic v2

### Frontend
- **Framework**: Vanilla JavaScript (no React/Vue/Angular)
- **Audio**: Web Audio API for recording
- **Styling**: CSS with CSS Variables
- **Routing**: Custom client-side router

## Quick Start

### Backend Setup

```bash
cd api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r api/requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost:5432/voice_journal"
export SECRET_KEY="your-secret-key-change-in-production"

# Start server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

The frontend is a static site that can be served by any web server. For development:

```bash
# Using Python's built-in server
cd ui
python -m http.server 3000

```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_auth.py -v

# Run with coverage
pytest tests/ --cov=api --cov-report=html
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT token

### Users
- `GET /api/v1/users/me` - Get current user
- `PATCH /api/v1/users/me` - Update current user

### Journal Entries
- `POST /api/v1/entries/upload` - Upload audio entry (multipart/form-data)
- `GET /api/v1/entries` - List all entries (paginated)
- `GET /api/v1/entries/{id}` - Get single entry
- `DELETE /api/v1/entries/{id}` - Delete entry
- `POST /api/v1/entries/{id}/reprocess` - Reprocess failed entry

### Health
- `GET /api/v1/health` - Health check

## Features

### Implemented
- ✅ User registration and authentication
- ✅ JWT-based session management
- ✅ Audio recording with Web Audio API
- ✅ Audio upload and storage
- ✅ Background AI processing (mock implementation)
- ✅ Transcription, summarization, emotion detection
- ✅ Entry listing with pagination
- ✅ Entry playback
- ✅ Entry deletion
- ✅ Reprocess failed entries
- ✅ Privacy settings (AI opt-out)
- ✅ Responsive design

### AI Processing (Mock)
The AI processing module (`api/ai/processing.py`) contains mock implementations for:
- `transcribe_audio()` - Convert audio to text
- `summarize_text()` - Generate summary
- `infer_emotion()` - Detect emotional state

Replace with actual AI service integrations (OpenAI Whisper, etc.) for production.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `SECRET_KEY` | JWT signing secret | Required |
| `UPLOAD_DIR` | Directory for audio files | `./uploads` |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration | `1440` (24h) |

## Security Considerations

1. **Password Storage**: PBKDF2-SHA256 with random salt
2. **JWT Tokens**: Signed with secret key, expire after 24 hours
3. **CORS**: Configured for specific origins in production
4. **File Upload**: Validated content type, size limits
5. **Data Isolation**: Users can only access their own entries

## Development Notes

### Custom JWT Implementation
The JWT implementation in `api/auth/utils.py` is custom (no PyJWT dependency) to meet the "no external dependencies" requirement. It uses:
- Base64url encoding
- HMAC-SHA256 for signatures
- JSON payload with standard claims (sub, exp, iat)

### Database Models
- `User`: id, email, password_hash, created_at
- `JournalEntry`: id, user_id, audio_url, transcript, summary, emotion, status, timestamps
- `Subscription`: id, user_id, plan, status (for future use)

### Entry Processing States
1. `pending` - Just uploaded
2. `processing` - AI processing in progress
3. `processed` - Successfully processed
4. `failed` - Processing failed (can be retried)

## License

MIT License - See LICENSE file for details.
