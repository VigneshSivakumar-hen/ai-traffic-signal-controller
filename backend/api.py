"""
FastAPI backend — REST endpoints matching the README's API table.

Run with:
    python -m uvicorn backend.api:app --reload --port 8000
"""

import logging
import threading
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.pipeline import TrafficPipeline

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Traffic Signal Controller API")

# The React dev server runs on a different port (5173) than the API (8000),
# so the browser blocks requests unless we explicitly allow it here.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_pipeline: Optional[TrafficPipeline] = None
# Guards pipeline creation: FastAPI can run overlapping sync requests in
# separate threads (a fast double-click on "Start Pipeline", or a stale
# request retried while a new one is in flight), and without this lock two
# TrafficPipeline() constructions can race to open yolov8n.pt at the same
# time, which Windows reports as WinError 32 ("used by another process").
_start_lock = threading.Lock()


class StartRequest(BaseModel):
    source: str = "0"   # "0" for webcam, a file path, or an rtsp:// URL
    lane_id: str = "north"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/status")
def status():
    if _pipeline is None:
        return {"running": False}
    return _pipeline.state.snapshot()


@app.get("/metrics")
def metrics():
    if _pipeline is None:
        raise HTTPException(status_code=404, detail="Pipeline not running")
    return {
        "counts": _pipeline.state.snapshot()["counts"],
        "history": _pipeline.state.history_snapshot(),
    }


@app.get("/signal")
def signal():
    if _pipeline is None:
        raise HTTPException(status_code=404, detail="Pipeline not running")
    snap = _pipeline.state.snapshot()
    return {
        "phase": snap["signal_phase"],
        "remaining": snap["signal_remaining"],
        "green_time_s": snap["green_time_s"],
    }


@app.get("/frame")
def frame():
    if _pipeline is None or _pipeline.state.last_frame_jpeg is None:
        raise HTTPException(status_code=404, detail="No frame available yet")
    return Response(content=_pipeline.state.last_frame_jpeg, media_type="image/jpeg")


@app.post("/pipeline/start")
def start_pipeline(req: StartRequest):
    global _pipeline
    with _start_lock:
        if _pipeline is not None and _pipeline.state.running:
            raise HTTPException(status_code=400, detail="Pipeline already running — call /pipeline/stop first")

        source = int(req.source) if req.source.isdigit() else req.source
        try:
            _pipeline = TrafficPipeline(video_source=source, lane_id=req.lane_id)
            _pipeline.start()
        except Exception as exc:
            logger.exception("Failed to start pipeline")
            raise HTTPException(status_code=400, detail=f"Could not start pipeline: {exc}") from exc

        return {"started": True, "source": req.source, "lane_id": req.lane_id}


@app.post("/pipeline/stop")
def stop_pipeline():
    global _pipeline
    if _pipeline is None or not _pipeline.state.running:
        raise HTTPException(status_code=400, detail="Pipeline is not running")
    _pipeline.stop()
    return {"stopped": True}


# --- Serve the built React app -----------------------------------------
# Must be registered LAST: FastAPI matches routes in registration order, so
# every /health, /status, /metrics, etc. route above still takes priority.
# This mount only catches whatever's left (the SPA's index.html + assets).
# run_all.py builds frontend/dist before starting the server; if you run
# `uvicorn backend.api:app` directly without building first, this is
# skipped and only the JSON API is served (useful during frontend dev with
# `npm run dev`, which talks to the API via the vite proxy instead).
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
else:
    logger.warning(
        "frontend/dist not found — only the JSON API is being served. "
        "Run `python run_all.py` (which builds it automatically) or "
        "`npm run build` inside frontend/ first."
    )
