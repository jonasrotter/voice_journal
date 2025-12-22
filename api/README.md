# Voice Journal API

## Requirements

- Python 3.10+
- PostgreSQL

## Installation

```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic[email] python-multipart
```

## Environment Variables

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/voice_journal
SECRET_KEY=your-secret-key-change-in-production
UPLOAD_DIR=./uploads
```

## Running

```bash
# Development
uvicorn api.main:app --reload --port 8000

# Production
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## API Documentation

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Endpoints

### Auth
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT token

### Users
- `GET /api/v1/users/me` - Get current user profile
- `PATCH /api/v1/users/me` - Update current user
- `DELETE /api/v1/users/me` - Delete account (GDPR)

### Entries
- `POST /api/v1/entries` - Upload audio and create entry
- `GET /api/v1/entries` - List all entries (paginated)
- `GET /api/v1/entries/{id}` - Get specific entry
- `PATCH /api/v1/entries/{id}` - Update entry
- `DELETE /api/v1/entries/{id}` - Delete entry
- `POST /api/v1/entries/{id}/reprocess` - Rerun AI analysis
