"""
Central configuration: thresholds, timing rules, lanes, model + API settings.

Every module imports from here rather than hardcoding values, so tuning the
system (e.g. for a different camera framing, or adding a lane) means editing
one file.
"""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT_DIR / "models"
DATA_DIR = ROOT_DIR / "data"

# --- AI Processing -----------------------------------------------------

# COCO class name -> our internal vehicle label
VEHICLE_CLASSES = {
    "car": "car",
    "motorcycle": "bike",
    "bus": "bus",
    "truck": "truck",
}

MODEL_NAME = "yolov8s.pt"  # n = fastest; swap for yolov8s.pt for more accuracy

# How often (in seconds of wall-clock time) the pipeline runs YOLO on the
# latest frame. Detection doesn't need to run every single frame.
DETECTION_INTERVAL_SEC = 1.0

# --- Decision Engine -----------------------------------------------------

# vehicle_count <= LOW           -> "LOW"
# LOW < vehicle_count <= MEDIUM  -> "MEDIUM"
# vehicle_count > MEDIUM         -> "HIGH"
DENSITY_THRESHOLDS = {"LOW": 5, "MEDIUM": 15}

# Density -> green time (seconds), from the design doc
GREEN_TIME_TABLE = {
    "LOW": 20,
    "MEDIUM": 35,
    "HIGH": 60,
    "EMERGENCY": 5,  # short "immediate" pulse, re-evaluated right after
}

# --- Signal Controller -----------------------------------------------------

YELLOW_TIME = 3
MIN_RED_TIME = 5

# --- Lanes -----------------------------------------------------

LANES = ["north", "south", "east", "west"]

# --- Monitoring -----------------------------------------------------

MAX_HISTORY = 200  # how many detection samples to keep in memory for charts

# --- Backend / Dashboard -----------------------------------------------------

API_HOST = "0.0.0.0"
API_PORT = 8000
API_BASE_URL = "http://localhost:8000"
DASHBOARD_PORT = 8501
