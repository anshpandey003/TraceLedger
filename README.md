# TraceLedger

**An evidence-first AI investigation engine for claim verification, temporal reasoning, and traceable conclusions.**

TraceLedger is an AI-powered investigation platform that evaluates claims against available evidence. It combines hybrid information retrieval, evidence-quality assessment, temporal filtering, and LLM-based verification to produce structured, evidence-grounded investigation results.

Unlike conventional RAG applications that primarily retrieve documents and generate answers, TraceLedger is designed to make the investigation process inspectable: what evidence was retrieved, how reliable it appears, when it was valid, and how it contributed to the result.

**Project status:** Active development. Core backend investigation, retrieval, evidence-quality, and persistence workflows are implemented. Frontend integration, end-to-end validation, and further verification capabilities are ongoing.

---

## Core Capabilities

### Investigation Management
- Create and manage investigations and associated claims.
- Persist investigation lifecycle states: `RUNNING`, `COMPLETED`, and `FAILED`.
- Execute structured, stateful investigation workflows using LangGraph.
- Store structured investigation results.

### Hybrid Evidence Retrieval
- Combine dense semantic retrieval and sparse/lexical retrieval.
- Use Reciprocal Rank Fusion (RRF) to combine retrieval results.
- Perform embedding-based similarity search with PostgreSQL and pgvector.
- Apply similarity thresholds and temporal filtering to retrieved evidence.

### Temporal Evidence Reasoning
- Track publication, observation, and evidence-validity timestamps.
- Evaluate evidence against an investigation's reference time.
- Account for `valid_from` and `valid_to` constraints.
- Exclude evidence that was unavailable or no longer valid at the requested reference time.

### Evidence Quality Assessment
Evaluate evidence across four dimensions:

- **Authority:** Source classification, including official, primary, verified, secondary, and unknown sources.
- **Freshness:** Recency-based scoring using configurable age thresholds.
- **Temporal validity:** Whether evidence was available and valid at the investigation's reference time.
- **Completeness:** Assessment based on metadata and content availability.

### LLM-Based Verification
- Integrate Google Gemini for structured claim and evidence verification.
- Process retrieved evidence through dedicated verification and analysis components.
- Validate structured verification outputs.
- Persist investigation analysis and results.

### Backend Reliability
- PostgreSQL transaction management and row-level locking.
- Protection against concurrent execution of the same investigation.
- Duplicate-result prevention.
- Retry-safe processing for claims with existing results.
- Structured API validation and error handling.

### Frontend
The Next.js application is under active development, with components and pages for:
- Investigation dashboard and listing.
- Investigation creation.
- Investigation detail views.
- Claim creation.
- Evidence-quality presentation.
- Evidence timelines and verdict indicators.

Complete frontend build and end-to-end integration verification are still in progress.

### Contradiction Analysis
Contradiction detection and explanation are part of the broader project direction. Further implementation, integration, and validation are ongoing; these capabilities should not yet be considered fully complete.

---

## Technology Stack

| Component | Technologies |
|---|---|
| Frontend | Next.js, React, TypeScript, Tailwind CSS |
| Backend | Python, FastAPI |
| AI orchestration | LangGraph, LangChain |
| LLM integration | Google Gemini |
| Data validation | Pydantic |
| ORM and persistence | SQLAlchemy |
| Database | PostgreSQL |
| Vector storage | pgvector |
| Retrieval | Dense retrieval, lexical retrieval, hybrid search, RRF |
| Database migrations | Alembic |
| Testing | pytest |
| Frontend quality | ESLint, TypeScript |
| Development environment | Git, Linux/WSL, Docker, Docker Compose |

---

## Architecture

```text
                         TraceLedger
                              |
             +----------------+----------------+
             |                                 |
       Next.js Frontend                   FastAPI Backend
       React + TypeScript                       |
             |                     +------------+------------+
             |                     |            |            |
       Investigation          Investigation  Evidence    Verification
       Dashboard & UI           APIs         Services     & Analysis
                                      |            |
                                      +-----+------+
                                            |
                                    LangGraph Workflow
                                            |
                              +-------------+-------------+
                              |             |             |
                          Retrieval    Quality         Gemini
                           Pipeline   Assessment     Verification
                              |             |             |
                              +-------------+-------------+
                                            |
                                    PostgreSQL Database
                                      + pgvector
                                            |
                              +-------------+-------------+
                              |             |             |
                         Investigations  Evidence      Results
                           & Claims     & Metadata    & Analysis

                              Automated Test Suite
                                     pytest
```

### Investigation Workflow

```text
Claim Submission
       |
       v
Investigation Creation
       |
       v
LangGraph Workflow Execution
       |
       v
Evidence Retrieval
(Dense + Lexical Search)
       |
       v
Hybrid Ranking (RRF)
       |
       v
Temporal Filtering
       |
       v
Evidence Quality Assessment
       |
       v
LLM-Based Verification
       |
       v
Structured Analysis & Result Persistence
```

*The workflow illustrates the intended processing architecture. Individual verification and analysis capabilities are still undergoing integration and validation.*

---

## Getting Started

### Prerequisites

- Python 3.12
- Node.js and npm
- PostgreSQL with pgvector support
- Google Gemini API credentials for LLM-based verification

### 1. Clone the repository

```bash
git clone https://github.com/anshpandey003/TraceLedger.git
cd TraceLedger
```

### 2. Set up the backend

Create and activate a virtual environment.

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS / WSL:**

```bash
python -m venv .venv
source .venv/bin/activate
```

Install backend dependencies:

```bash
python -m pip install -e ./backend
```

Configure the required environment variables and PostgreSQL database connection according to the backend configuration.

Start the API:

```bash
python -m uvicorn backend.app.main:app --reload
```

The backend typically runs at:

`http://127.0.0.1:8000`

### 3. Set up the frontend

Open a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend typically runs at:

`http://localhost:3000`

### 4. Run backend tests

From the repository root:

```bash
python -m pytest backend/tests -q -m "not gemini"
```

The command excludes tests marked `gemini`, which may require external API credentials.

### 5. Validate the frontend

From the frontend directory:

```bash
npm run lint
npm run build
```

---

## Reliability and Testing

TraceLedger includes automated backend tests covering:

- Investigation API workflows.
- Evidence retrieval and temporal filtering.
- Evidence-quality assessment.
- Gemini verifier behavior.
- Investigation analysis and persistence.
- Retry behavior and lifecycle management.
- Concurrent execution and PostgreSQL transaction locking.

The latest completed full backend regression run reported:

| Metric | Result |
|---|---:|
| Passed | 114 |
| Failed | 0 |
| Deselected | 3 |
| Warnings | 10 |
| Execution time | 16.26 seconds |

**Test status note:** This result predates a subsequent modification to `evidence_quality.py`. A fresh full regression run is required before treating these figures as the current test baseline.

---

## Engineering Principles

- **Evidence traceability:** Keep the relationship between claims, evidence, analysis, and citations inspectable.
- **Transparency:** Make the reasoning process and evidence contributions understandable.
- **Uncertainty awareness:** Avoid treating insufficient evidence as conclusive proof.
- **Temporal awareness:** Evaluate evidence in the context of when it was available and valid.
- **Evidence quality:** Distinguish sources using authority, freshness, validity, and completeness.
- **Reliability:** Protect stateful investigation execution against concurrency and duplicate persistence.
- **Modularity:** Separate API, retrieval, verification, analysis, and persistence responsibilities.
- **Testability:** Validate core behavior through automated unit and integration tests.

---

## Development Roadmap

TraceLedger is actively evolving. Current development priorities include:

- Complete frontend implementation and build verification.
- End-to-end frontend/backend workflow validation.
- Further refinement of evidence verification.
- Stronger contradiction detection and handling.
- Expanded temporal reasoning and edge-case coverage.
- Improved citation and source-level traceability.
- Retrieval and verification evaluation using a dedicated benchmark dataset.
- Failure recovery and stale-execution handling.
- Security review and performance evaluation.
- Containerization and deployment.

These are ongoing development goals, not claims of completed functionality.

---

## Contributing

Bug reports, ideas, and contributions are welcome.

Please:
- Keep commits focused.
- Add or update tests for relevant changes.
- Avoid committing credentials, environment files, or generated artifacts.
- Document changes to APIs, schemas, and database migrations.

## License

No license has been specified yet. Reuse and redistribution remain subject to applicable copyright law until a license is added.

---

**TraceLedger — Investigate the evidence. Explain the uncertainty. Make conclusions traceable.**
