# TraceLedger

**Evidence-driven claim verification with transparent, traceable investigations.**

TraceLedger is an investigation platform designed to evaluate claims against available evidence, identify conflicting information, and explain how conclusions are reached.

## Features

- **Claim investigations** — Organize claims and supporting evidence.
- **Evidence management** — Track source material, metadata, and timestamps.
- **Contradiction detection** — Identify conflicting numeric assertions across evidence items.
- **Evidence quality assessment** — Evaluate authority, freshness, temporal validity, and completeness.
- **Verification pipeline** — Validate structured verification outputs.
- **Traceable results** — Associate investigation results with evidence citations.
- **Human-readable explanations** — Explain detected conflicts using recorded assertions and values.
- **Vector retrieval foundation** — Build evidence retrieval capabilities using PostgreSQL and pgvector.
- **Investigation dashboard** — Explore claims, evidence, verdicts, and analysis through a web interface.

*TraceLedger is under active development; feature availability and end-to-end integration may vary.*

## Technology Stack

| Component | Technologies |
|---|---|
| Frontend | Next.js, React, TypeScript |
| Backend | Python, FastAPI |
| Data validation | Pydantic |
| Database | PostgreSQL, SQLAlchemy |
| Vector storage | pgvector |
| Migrations | Alembic |
| Testing | pytest |
| Code quality | ESLint, TypeScript |

## Architecture

```text
TraceLedger
├── Frontend
│   ├── Investigation dashboard
│   ├── Claim and evidence views
│   └── Contradiction explanations
├── FastAPI Backend
│   ├── Investigation and evidence APIs
│   ├── Verification services
│   ├── Evidence quality analysis
│   ├── Contradiction detection
│   └── Retrieval and embedding services
├── PostgreSQL
│   ├── Investigations and claims
│   ├── Evidence and citations
│   └── Analysis results and contradictions
└── Automated Tests
    └── pytest
```

## Getting Started

### Prerequisites

- Python compatible with the backend dependencies
- Node.js and npm
- PostgreSQL with pgvector support

### Clone the repository

```bash
git clone https://github.com/anshpandey003/TraceLedger.git
cd TraceLedger
```

### Backend

Create and activate a virtual environment, then install the backend dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .\backend
```

Configure the required environment variables and database connection before starting the API:

```powershell
python -m uvicorn backend.app.main:app --reload
```

### Frontend

In a separate terminal:

```powershell
cd frontend
npm install
npm run dev
```

The frontend typically runs at `http://localhost:3000`, and the backend at `http://127.0.0.1:8000`.

### Testing

From the repository root:

```powershell
python -m pytest backend/tests -q -m "not gemini"
```

For frontend validation:

```powershell
cd frontend
npm run lint
npm run build
```

## Design Principles

- **Traceability:** Keep evidence and citations inspectable.
- **Transparency:** Explain disagreements rather than hiding them behind a verdict.
- **Uncertainty awareness:** Avoid treating insufficient evidence as proof.
- **Temporal awareness:** Account for evidence timestamps and validity.
- **Modularity:** Separate API, persistence, retrieval, and verification responsibilities.
- **Testability:** Validate core behavior with automated tests.

## Development Status

TraceLedger is actively evolving. Current development focuses on evidence analysis, contradiction explanations, retrieval infrastructure, and frontend integration. Passing automated tests does not guarantee that every external integration or database migration has been validated in a live environment.

## Contributing

Bug reports, ideas, and contributions are welcome. Please test changes, keep commits focused, and never commit credentials, environment files, or generated artifacts.

## License

No license has been specified yet. Reuse and redistribution remain subject to applicable copyright law until a license is added.

---

**TraceLedger — Investigate the evidence. Explain the contradictions. Make conclusions traceable.**
