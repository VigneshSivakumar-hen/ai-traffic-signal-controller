# AI-Based Traffic Signal Controller

An intelligent traffic signal system that uses **YOLOv8** for vehicle detection, adaptive timing algorithms for signal optimization, and a **FastAPI + React** stack for live monitoring.

## Architecture

```
CCTV / Sensors → Data Collection → AI Processing → Decision Engine → Signal Controller → Traffic Lights
                                                                          ↓
                                                              Monitoring Dashboard
```

| Module | Purpose | Tech |
|--------|---------|------|
| Data Collection | Video frames, vehicle counts | OpenCV |
| AI Processing | Detection, tracking, density | YOLOv8, SimpleTracker |
| Decision Engine | Signal timing, lane priority | Rule-based + ML predictor |
| Signal Controller | Green / Yellow / Red cycles | State machine |
| Dashboard | Live view, stats, alerts | React (built + served by FastAPI) |

## Quick Start

### 1. Install Python dependencies

```bash
cd Projects/ai-traffic-signal-controller
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. Run standalone simulation (webcam or video, no dashboard)

```bash
python run_simulation.py --source 0          # webcam
python run_simulation.py --source path/to/traffic.mp4
```

### 3. Run the full system (API + React dashboard)

Requires [Node.js](https://nodejs.org) (LTS) for a one-time frontend build.

```bash
python run_all.py
```

This builds `frontend/` if it hasn't been built yet, then starts the FastAPI backend, which serves **both** the JSON API and the built dashboard on a single port. Open **http://localhost:8000**, set a video source in the sidebar (`0` for webcam, or a file path), and click **Start Pipeline**.

To edit the dashboard UI with hot-reload instead of the built static version:
```bash
# Terminal 1
python -m uvicorn backend.api:app --reload --port 8000
# Terminal 2
cd frontend && npm install && npm run dev
```
Then open **http://localhost:5173** — Vite proxies API calls to the backend automatically (see `frontend/vite.config.js`).

A legacy Streamlit dashboard is still available at `dashboard/app.py` (`streamlit run dashboard/app.py`, needs the backend running separately) if you'd rather not install Node.js.

## Signal Timing Rules

| Traffic Density | Green Time |
|-----------------|------------|
| Low | 20 sec |
| Medium | 35 sec |
| High | 60 sec |
| Emergency | Immediate green |

## Project Structure

```
ai-traffic-signal-controller/
├── config/settings.py          # Thresholds, lanes, timing
├── src/
│   ├── data_collection/        # Video capture
│   ├── ai_processing/          # YOLO, tracker, analyzer
│   ├── decision_engine/        # Optimizer + predictor
│   ├── signal_controller/      # Light state machine
│   ├── monitoring/             # Shared runtime state
│   └── pipeline.py             # Main orchestrator
├── backend/api.py              # FastAPI REST endpoints + serves the built React app
├── frontend/                   # React dashboard (Vite) — npm run build → dist/, served by FastAPI
├── dashboard/app.py            # Legacy Streamlit UI (optional, needs backend running separately)
├── run_simulation.py
└── run_all.py                  # Builds frontend/ if needed, then starts backend on :8000
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/status` | Full system snapshot |
| GET | `/metrics` | Lane vehicle stats |
| GET | `/signal` | Current signal state |
| GET | `/frame` | Annotated JPEG frame |
| POST | `/pipeline/start` | Start processing |
| POST | `/pipeline/stop` | Stop processing |

## Next Steps

- **Multi-camera**: Assign each lane its own `VideoCapture` source in `config/settings.py`
- **DeepSORT**: Replace `SimpleTracker` with full DeepSORT for robust tracking
- **LSTM / Random Forest**: Train `TrafficPredictor` on historical queue data
- **Reinforcement Learning**: Add Q-learning agent in `decision_engine/`
- **Raspberry Pi**: Wire `TrafficLightController.apply()` to GPIO pins
- **Database**: Persist history to PostgreSQL via SQLAlchemy
- **Emergency vehicles**: Fine-tune YOLO on ambulance/fire truck classes

## Author

Built for VIGNESH — Data Science workflow with Python, OpenCV, and YOLOv8.
