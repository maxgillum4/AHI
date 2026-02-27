from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from routes import router
from phase2.api import router as v2_router

FRONTEND_FILE = Path(__file__).parent / "app.py"

app = FastAPI(
    title="AHI Diagnostic Reasoning Engine",
    description=(
        "Phase 1: Structured Analyzer + Phase 2: Conversational Interview Engine. "
        "Processes AI maturity assessments with hybrid heuristic + statistical analysis. "
        "NDA-compliant: no raw audio or transcripts are persisted."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(router,    prefix="/api")
app.include_router(v2_router, prefix="/api/v2", tags=["v2-interview"])


@app.get("/", response_class=HTMLResponse)
async def serve_frontend() -> HTMLResponse:
    html = FRONTEND_FILE.read_text(encoding="utf-8")
    return HTMLResponse(content=html)


@app.on_event("startup")
async def startup_event() -> None:
    from hybrid_analyst import load_benchmark
    df = load_benchmark()
    n = len(df) if not df.empty else 0
    print(f"[AHI] Benchmark dataset: {n} respondents loaded.")
    print("[AHI] Whisper model loaded in routes.py.")
    print("[AHI] Phase 2 conversational engine: /api/v2/")
    print("[AHI] Diagnostic Reasoning Engine ready on http://127.0.0.1:8001")
    print("[AHI] API docs: http://127.0.0.1:8001/docs")
