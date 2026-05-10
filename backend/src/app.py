"""
Student: Mohammad Abdullah (BSCS23202)

Includes:
  - middleware
  - CORS middleware
  - Challenge and Webhook routers
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from .routes import challenge, webhooks


#                 Custom Middleware:
# REQUIREMENT: Every API response must include this header.
STUDENT_ID = "BSCS23202"


class StudentIDMiddleware(BaseHTTPMiddleware):
    """
    Injects X-Student-ID header into every HTTP response.
    """
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Student-ID"] = STUDENT_ID
        return response


# ── App Setup ──────────────────────────────────────────────────
app = FastAPI(
    title="StudySync API",
    description="PDC Assignment — Resilient Distributed Systems",
    version="1.0.0",
)

# Add middlewares (FastAPI adds to the top of the stack, so the LAST added is the outermost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(StudentIDMiddleware)

# ── Routers ────────────────────────────────────────────────────
app.include_router(challenge.router, prefix="/api")
app.include_router(webhooks.router, prefix="/webhooks")


# ── Health Check ───────────────────────────────────────────────
@app.get("/health")
async def health_check():
    """Health check endpoint — also verifies the X-Student-ID header is present."""
    return {
        "status": "healthy",
        "student_id": STUDENT_ID,
        "message": "X-Student-ID header is attached to this response.",
    }
