# TraceLedger

**An evidence-driven AI investigation engine for claim verification, temporal reasoning, and traceable conclusions.**

TraceLedger is an AI-powered investigation platform designed to evaluate claims against available evidence, assess source reliability, identify conflicting information, and explain how conclusions are reached.

Unlike conventional RAG-based question-answering systems, TraceLedger focuses on the reliability and traceability of the investigation process. It combines hybrid information retrieval, evidence-quality assessment, temporal filtering, and structured LLM-based verification to support evidence-grounded analysis.

> **Development status:** Actively under development. Core backend investigation workflows, retrieval, evidence-quality assessment, persistence, and automated testing are implemented. Frontend integration and advanced verification capabilities continue to evolve.

## Key Capabilities

### Investigation Management
- Create and manage investigations containing multiple claims.
- Execute structured investigation workflows.
- Track investigation lifecycle states, including running, completed, and failed.
- Persist investigation results and analysis.

### Hybrid Evidence Retrieval
- Semantic retrieval using vector embeddings.
- Lexical retrieval for keyword-oriented evidence discovery.
- Reciprocal Rank Fusion (RRF) for combining retrieval results.
- PostgreSQL and pgvector-based retrieval infrastructure.
- Temporal filtering to exclude evidence unavailable at the investigation's reference time.

### Evidence Quality Assessment
Evaluate retrieved evidence across four dimensions:

- **Authority:** Assess source credibility and authority.
- **Freshness:** Evaluate how recently evidence was observed or published.
- **Temporal validity:** Determine whether evidence was available at the investigation's reference time.
- **Completeness:** Assess the availability of meaningful source information.

### AI-Powered Verification
- Google Gemini integration for LLM-based verification.
- Structured investigation and analysis workflows.
- LangGraph-based orchestration.
- Evidence-grounded claim analysis.

### Traceability and Persistence
- Associate claims with supporting evidence.
- Persist structured investigation results.
- Maintain evidence-to-result citation relationships.
- Store investigation analysis and evidence-quality assessments.

### Backend Reliability
- PostgreSQL transaction management.
- Row-level locking for concurrent investigation execution.
- Protection against duplicate result persistence.
- Investigation execution lifecycle tracking.
- Automated unit, API, and integration testing.

*Advanced contradiction handling, comprehensive evaluation, and complete end-to-end integration remain active development areas.*

## Architecture

```text
                         TraceLedger
                              |
             +----------------+----------------+
             |                                 |
         Frontend                         Backend API
      Next.js / React                      FastAPI
             |                                 |
             |                      Investigation Workflow
             |                          LangGraph
             |                                 |
             |                +----------------+----------------+
             |                |                |                |
             |           Retrieval       Verification       Analysis
             |                |                |                |
             |          Hybrid Search     Google Gemini    Evidence Quality
             |                |                |                |
             |                +----------------+----------------+
             |                                 |
             |                           Persistence
             |                                 |
             |                         PostgreSQL
             |                            pgvector
             |                                 |
             +------------------------- Investigation Results
                                               |
                                      Claims / Evidence /
                                      Analysis / Citations
```

## Technology Stack

| Component | Technologies |
|---|---|
| Frontend | Next.js, React, TypeScript, Tailwind CSS |
| Backend | Python, FastAPI |
| AI Orchestration | LangGraph, LangChain |
| LLM Integration | Google Gemini |
| Retrieval | Hybrid Search, Dense Retrieval, Lexical Retrieval, RRF |
| Database | PostgreSQL, SQLAlchemy |
| Vector Storage | pgvector |
| Data Validation | Pydantic |
| Database Migrations | Alembic |
| Testing | pytest |
| Code Quality | ESLint, TypeScript |

## Project Structure

```text
TraceLedger/
│
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── evaluation/
│   │   ├── models/
│   │   ├── retrieval/
│   │   ├── schemas/
│   │   └── services/
│   │
│   ├── alembic/
│   └── tests/
│
├── frontend/
│   ├── app/
│   ├── components/
│   └── lib/
│
├── docs/
├── evaluation/
├── infrastructure/
│
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.12
- Node.js and npm
- PostgreSQL with pgvector support
- Google Gemini API credentials

### 1. Clone the repository

```bash
git clone https://github.com/anshpandey003/TraceLedger.git
cd TraceLedger
```

### 2. Backend Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Linux / WSL:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies:

```bash
python -m pip install -e ./backend
```

Configure the required environment variables, including database connection details and Gemini API credentials, according to the backend configuration.

Apply database migrations:

```bash
alembic upgrade head
```

Start the backend:

```bash
python -m uvicorn backend.app.main:app --reload
```

The API is available at:

`http://127.0.0.1:8000`

Interactive API documentation:

`http://127.0.0.1:8000/docs`

### 3. Frontend Setup

Open a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend is available at:

`http://localhost:3000`

### 4. Running Backend Tests

From the repository root, with the backend virtual environment activated:

```bash
PYTHONPATH=.:backend pytest backend/tests/ -q
```

The test suite includes coverage for:

- API workflows.
- Evidence retrieval and temporal filtering.
- Evidence-quality assessment.
- LLM verification.
- Investigation analysis.
- Database persistence.
- Retry behavior.
- Concurrent execution and transaction locking.

### 5. Frontend Validation

From the frontend directory:

```bash
npm run lint
npm run build
```

## Engineering Principles

- **Evidence before conclusions:** Ground verification in retrieved evidence.
- **Traceability:** Preserve relationships between claims, evidence, analysis, and citations.
- **Temporal awareness:** Evaluate information against the investigation's reference time.
- **Uncertainty awareness:** Avoid treating insufficient evidence as proof.
- **Transparency:** Make the reasoning and supporting evidence inspectable.
- **Reliability:** Protect investigation execution and persistence against concurrency issues.
- **Modularity:** Separate retrieval, verification, analysis, APIs, and persistence.
- **Testability:** Validate critical application behavior through automated tests.

## Development Roadmap

TraceLedger is actively evolving. Current and planned areas of development include:

- [x] Investigation and claim management.
- [x] Evidence persistence and retrieval.
- [x] Evidence-quality assessment.
- [x] Temporal evidence filtering.
- [x] Dense and lexical retrieval foundations.
- [x] Reciprocal Rank Fusion.
- [x] LangGraph-based investigation orchestration.
- [x] Gemini-based verification components.
- [x] Investigation persistence and concurrency protection.
- [x] Backend API and integration test coverage.
- [ ] Advanced contradiction detection and resolution.
- [ ] Comprehensive retrieval and verification evaluation.
- [ ] Complete frontend/backend end-to-end validation.
- [ ] Improved failure recovery and stale-execution handling.
- [ ] Security hardening and deployment.
- [ ] Performance benchmarking.

## Contributing

Bug reports, ideas, and contributions are welcome.

Please keep changes focused, test modifications before submitting them, and never commit credentials, environment files, or generated artifacts.

## License

No license has been specified yet. Reuse and redistribution remain subject to applicable copyright law until a license is added.

---

**TraceLedger — Investigate the evidence. Explain the contradictions. Make conclusions traceable.**
