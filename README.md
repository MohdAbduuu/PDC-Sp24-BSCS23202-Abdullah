# Mohammad Abdullah — BSCS23202

## StudySync: Building Resilient Distributed Systems
**Course:** Parallel and Distributed Computing (PDC)

---

### 📖 Overview

This project implements a **Circuit Breaker** pattern to solve the **Fault Tolerance** problem (Problem 3) in the StudySync application. When the external LLM API goes down, the circuit breaker prevents the entire server from hanging by short-circuiting failed calls and returning instant fallback responses.

### 🏗️ Architecture

```
Frontend (React + Vite)  →  Backend (FastAPI)  →  LLM API (Gemini)
                                  ↓
                          Circuit Breaker
                           ├── CLOSED:    normal operation
                           ├── OPEN:      instant fallback (API is down)
                           └── HALF_OPEN: probe to check recovery
```

---

### 🚀 How to Run

#### Prerequisites
- Python 3.13+
- Node.js 18+
- `uv` package manager (or `pip`)

#### 1. Backend Setup
```bash
cd backend
uv sync                # install dependencies
```

#### 2. Run the Demo (Before vs After)
```bash
cd backend
python demo_fault_tolerance.py
```
This will show:
- **BEFORE**: 5 requests each blocking for 3 seconds (15s total)
- **AFTER**: Circuit trips after 3 failures, remaining requests are instant (~9s total)
- **CONCURRENT**: Side-by-side comparison under parallel load

> **No API keys needed** — the demo mocks the LLM API to simulate downtime.

#### 3. Run the Full Application

> **Note on Excluded Files:** For security and repository size limits, the following are **not included** in this upload:
> - **API Keys & Environment Variables (`.env`):** You will need your own Clerk and Gemini API keys to run the full application.
> - **Database (`database.db`):** The local SQLite database is omitted. It will be created automatically when you run the backend.
> - **Virtual Environments (`.venv`, `.venv_stable`):** Please install Python dependencies manually as shown in step 1.
> - **Node Modules (`node_modules`):** Please run `npm install` in the frontend directory before running the app.

```bash
# Terminal 1 — Backend
cd backend
.\.venv_stable\Scripts\python.exe server.py

# Terminal 2 — Frontend
cd frontend
npm run dev

# Terminal 3 — Ngrok (for webhooks)
ngrok http 8000
```

#### 4. Verify X-Student-ID Header
```bash
curl -I http://localhost:8000/health
# Look for: X-Student-ID: BSCS23202
```

---

### 📁 Project Structure

```
backend/
├── server.py                     # Uvicorn entry point
├── demo_fault_tolerance.py       # ★ Before/After demo script
├── src/
│   ├── app.py                    # FastAPI app + X-Student-ID middleware
│   ├── circuit_breaker.py        # ★ Circuit Breaker implementation
│   ├── ai_generator.py           # ★ Fixed LLM call (with circuit breaker)
│   ├── ai_generator_naive.py     # Original naive version (for comparison)
│   ├── utils.py                  # Clerk authentication
│   ├── database/
│   │   ├── models.py             # SQLAlchemy models
│   │   └── db.py                 # Database CRUD operations
│   └── routes/
│       ├── challenge.py          # Challenge generation endpoints
│       └── webhooks.py           # Clerk webhook handler
frontend/
├── src/                          # React + Vite frontend
└── ...
```

### 🔑 Key Files for Grading

| Requirement | File |
|---|---|
| Circuit Breaker Pattern | `backend/src/circuit_breaker.py` |
| Fixed AI Generator | `backend/src/ai_generator.py` |
| X-Student-ID Middleware | `backend/src/app.py` |
| Before/After Demo | `backend/demo_fault_tolerance.py` |
| Naive Version (before) | `backend/src/ai_generator_naive.py` |

---

### 📝 Custom Header

Every API response includes:
```
X-Student-ID: BSCS23202
```

This is enforced by the `StudentIDMiddleware` class in `backend/src/app.py`.
