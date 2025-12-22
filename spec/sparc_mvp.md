# Voice Journal Application 
## 1. Specification
### 1.1 Product Purpose
Enable users to privately capture voice journals and receive structured reflection (transcripts, summaries, emotional signals) with minimal friction and high trust.

### 1.2 Primary User Story
“As a user, I want to speak my thoughts freely, save them securely, and later understand patterns in what I said and how I felt.”

### 1.3 Core Capabilities
- Record audio in-browser
- Upload and store audio securely
- Transcribe speech to text
- Generate AI summaries and emotion labels
- View, replay, edit, and delete journal entries
- Authentication and strict per-user data isolation
- All API inputs and outputs validated using Pydantic schemas

### 1.4 Success Criteria
- AI processing completes asynchronously without blocking UX
- Full data deletion guaranteed within system boundaries
- No unvalidated or malformed data crosses API boundaries

## 2. Pseudocode
### 2.1 Frontend — Voice Recording Flow (ui/, React + TypeScript)
function RecordEntry() {
  const recorder = useAudioRecorder()
  const [isRecording, setRecording] = useState(false)

  onStartClick():
    recorder.start()
    setRecording(true)

  onStopClick():
    audioBlob = recorder.stop()
    setRecording(false)
    uploadAudio(audioBlob)

  uploadAudio(blob):
    POST /entries (multipart/form-data)
    response validated against EntryRead schema
}


Frontend uses TypeScript interfaces aligned with backend Pydantic schemas.

### 2.2 Backend — Entry Creation & Async Processing (api/, FastAPI)
@router.post(
    "/entries",
    response_model=EntryCreateResponse
)
def create_entry(audio_file, user):
    entry = JournalEntry(
        user_id=user.id,
        audio_url=store_audio(audio_file),
        status="uploaded"
    )

    db.save(entry)
    background_tasks.add_task(process_entry, entry.id)

    return entry

### 2.3 Background Processing Pipeline
def process_entry(entry_id):
    entry = db.get_entry(entry_id)

    transcript = transcribe_audio(entry.audio_url)
    summary = summarize_text(transcript)
    emotion = infer_emotion(transcript)

    entry.transcript = transcript
    entry.summary = summary
    entry.emotion = emotion
    entry.status = "processed"

    db.save(entry)

### 2.4 Database Access Pattern
def get_user_entries(user_id):
    return (
        db.query(JournalEntry)
        .filter(user_id=user_id)
        .order_by(created_at DESC)
    )

## 3. Architecture
### 3.1 High-Level Architecture (Monolithic)
[ Browser ]
   |
   | HTTPS (JWT)
   |
[ ui/ React SPA ]
   |
   | REST API
   |
[ api/ FastAPI Monolith ]
   |
   | SQLAlchemy
   |
[ PostgreSQL ]

### 3.2 Frontend Architecture (ui/)
Responsibilities
- Capture audio (Web Audio API)
- Manage UI state
- Call backend APIs
- Display transcripts, summaries, emotions
- Enforce API typing via shared contracts

Modules
ui/
├── auth/
├── recording/
├── entries/
├── settings/
└── api/

### 3.3 Backend Architecture (api/, FastAPI)
Responsibilities
- Authentication & authorization
- Audio ingestion
- Async AI orchestration
- CRUD for journal entries
- Data validation via Pydantic at all boundaries

Modules
api/
├── auth/
├── users/
├── entries/
│   ├── router.py
│   ├── schemas.py   # Pydantic models
│   ├── models.py   # SQLAlchemy models
│   └── service.py  # business logic
├── ai/
├── db/
└── main.py

### 3.4 Database Schema (PostgreSQL)
users (
  id UUID PRIMARY KEY,
  email TEXT UNIQUE,
  password_hash TEXT,
  created_at TIMESTAMP
)

journal_entries (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  audio_url TEXT,
  transcript TEXT,
  summary TEXT,
  emotion TEXT,
  status TEXT,
  created_at TIMESTAMP
)

subscriptions (
  user_id UUID REFERENCES users(id),
  plan TEXT,
  status TEXT
)

## 4. Refinement
### 4.1 Security & Privacy
- JWT authentication
- Audio and derived text encrypted at rest
- Strict per-user access control
- Pydantic validation prevents unexpected or malicious payloads
- AI output labeled as suggestive, not authoritative
- Hard-delete pipeline (no soft deletes)

### 4.2 Performance Considerations
- Audio uploads chunked if needed
- Async background jobs for AI
- Frontend optimistic UI updates
- Index on journal_entries.user_id, created_at

### 4.3 UX Refinements
- Recording starts within <500ms
- AI summaries optional and regenerable
- Emotion labels use soft language
- No streak pressure or gamification

### 4.4 Scalability Within Monolith
- Stateless FastAPI services
- Independently scalable background workers
- DB connection pooling
- Clear seams for future service extraction
- Stable Pydantic schemas enable safe API evolution

## 5. Completion
### 5.1 Definition of Done (MVP)
- User can record, save, replay, and delete entries
- Transcription and summaries work asynchronously
- Entries visible only to owning user
- All API inputs and outputs validated via Pydantic
- AI processing failures handled gracefully
- GDPR-style data deletion supported
- Unit, integration, and contract tests implemented and passing

### 5.2 Unit Test Scenarios

(unchanged — backend + frontend unit tests as previously defined)

### 5.3 Integration Tests
Integration tests verify end-to-end behavior across multiple system components, excluding external third-party services (AI providers, cloud storage), which are mocked.

#### 5.3.1 Backend Integration Tests (api/)
- Tools
- pytest
- fastapi.testclient
- Test PostgreSQL database
- Background task execution enabled
- Core Integration Scenarios
- Entry Lifecycle (Happy Path)
- Upload audio
- Entry stored in DB
- Background task processes entry
- Transcript, summary, emotion persisted

def test_full_entry_lifecycle(client, auth_headers):
    response = client.post(
        "/entries",
        files={"audio": ("test.wav", b"audio")},
        headers=auth_headers
    )
    entry_id = response.json()["id"]

    wait_for_background_tasks()

    entry = client.get(f"/entries/{entry_id}", headers=auth_headers)
    assert entry.json()["status"] == "processed"


- Authentication + Authorization Integration
- JWT required for all protected endpoints
- Cross-user access attempts fail
- Deletion Cascade
- Deleting an entry removes:
- DB record
- Stored audio
- Derived AI artifacts
- Failure Recovery
- AI failure sets entry status to failed
- Entry remains readable and deletable

#### 5.3.2 Frontend Integration Tests (ui/)
Tools
- Jest
- React Testing Library
- Mock Service Worker (MSW)

Scenarios
- Record → Upload → Processing → Display
- Loading and error states rendered correctly
- Optimistic UI updates reconciled with server response

### 5.4 Contract Tests (ui ↔ api)
Contract tests ensure frontend and backend remain compatible, even as each evolves independently.

#### 5.4.1 Contract Ownership
- Backend is the contract source of truth
- Contracts defined by Pydantic schemas
- Frontend TypeScript types generated from schemas

#### 5.4.2 Contract Test Strategy
Approach
- Schema-based contract testing (not mock-driven)
- Contracts versioned (e.g., /api/v1)
- Breaking changes require explicit version bump

#### 5.4.3 Backend Contract Tests (api/)
Purpose
- Ensure API responses conform exactly to declared Pydantic schemas.

def test_entry_response_contract(client, auth_headers):
    response = client.post(
        "/entries",
        files={"audio": ("test.wav", b"audio")},
        headers=auth_headers
    )
    EntryCreateResponse.model_validate(response.json())

#### 5.4.4 Frontend Contract Tests (ui/)
Purpose
- Ensure frontend can safely consume real backend responses.

Mechanism
- Generated TS types checked at compile time
- Runtime validation for critical boundaries (optional)
- expect(response).toMatchSchema(EntryReadSchema)

#### 5.4.5 Contract Test Coverage
- Entry creation
- Entry listing
- Entry detail retrieval
- Error responses (401, 403, 404, 422)
- Pagination & filtering (future-ready)

## 5.5 Test Automation & CI Requirements
- All unit, integration, and contract tests run in CI
- No deploy on failing contract tests
- Test database reset per run

Minimum coverage targets:
- Backend: ≥80%
- Frontend: ≥70%

## 5.6 Launch Readiness Checklist
- Privacy policy & data handling docs
- Load testing for audio uploads
- Error monitoring enabled
- Backup & restore tested
- Clear in-product explanation of AI behavior
- CI pipeline green (unit + integration + contract tests)