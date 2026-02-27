"""
routes.py — AHI Diagnostic Reasoning Engine
FastAPI route handlers. Thin layer: validate, analyze, benchmark, return.
No business logic lives here — it all lives in analyzer.py and hybrid_analyst.py.
"""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from analyzer import analyze_assessment
from hybrid_analyst import generate_hybrid_summary
from schema import EXAMPLE_PAYLOAD, AnalysisResponse, AssessmentPayload

router = APIRouter()


# ---------------------------------------------------------------------------
# POST /api/analyze-assessment
# ---------------------------------------------------------------------------
import os
import tempfile
import whisper

_model = whisper.load_model("base")

@router.post("/transcribe-note")
async def transcribe_note(audio: UploadFile = File(...)) -> JSONResponse:
    tmp_path = None
    try:
        suffix = os.path.splitext(audio.filename or "")[1] or ".m4a" or ".webm"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = tmp.name
            contents = await audio.read()
            print(f"[TRANSCRIBE] filename={audio.filename} content_type={audio.content_type}")
            print(f"[TRANSCRIBE] bytes={len(contents)} suffix={suffix} tmp={tmp_path}")
            tmp.write(contents)

        result = _model.transcribe(
            tmp_path,
            language="en",
            task="transcribe")
        transcript = (result.get("text") or "").strip()
        language = result.get("language")
        segments = result.get("segments")  # list of dicts with start/end/text
        print(f"[TRANSCRIBE] text_len={len(transcript)} lang={language} segs={0 if not segments else len(segments)}")
        return JSONResponse(content={
            "transcript": transcript,
            "language": language,
            "segments": segments,
            "whisper_available": True
        })

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"transcript": None, "whisper_available": True, "error": str(e)},
        )

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
    

@router.post("/analyze-assessment", response_model=AnalysisResponse)
async def analyze_assessment_endpoint(
    payload: AssessmentPayload,
    request: Request,
) -> AnalysisResponse:
    """
    Primary diagnostic endpoint.

    Pipeline:
      1. Validate payload (Pydantic handles this automatically)
      2. Run ReasoningModule (analyzer.py)
      3. Attach HybridAnalystSummary (hybrid_analyst.py, if benchmark data available)
      4. Return AnalysisResponse

    NDA note: No raw text or audio is persisted. Analysis is performed in RAM.
    Justification text is used only for signal extraction and is not logged.
    """
    try:
        # Step 2: Core analysis
        result = analyze_assessment(payload)

        # Step 3: Statistical benchmarking (optional — fails gracefully)
        try:
            hybrid = generate_hybrid_summary(payload, result)
            result = result.model_copy(update={"hybrid_analyst": hybrid})
        except Exception:
            # Benchmark failure is non-fatal — continue without it
            pass

        return result

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis engine error: {type(e).__name__}: {str(e)}"
        )


# ---------------------------------------------------------------------------
# GET /api/schema/example-payload
# ---------------------------------------------------------------------------

@router.get("/schema/example-payload")
async def example_payload() -> JSONResponse:
    """
    Returns a fully valid example payload.
    Useful for frontend developers testing the API without a running assessment.
    """
    return JSONResponse(content=EXAMPLE_PAYLOAD)


# ---------------------------------------------------------------------------
# GET /api/health
# ---------------------------------------------------------------------------

@router.get("/health")
async def health() -> dict:
    """Health check — also reports benchmark data availability."""
    from hybrid_analyst import BENCHMARK_CSV, load_benchmark

    df = load_benchmark()
    benchmark_status = (
        f"loaded ({len(df)} respondents)"
        if not df.empty
        else "not available (run generate_benchmark.py)"
    )

    return {
        "status": "ok",
        "version": "1.0",
        "phase": "phase_1_structured_analyzer",
        "benchmark": benchmark_status,
    }
