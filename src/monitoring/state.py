"""
Monitoring Module — Shared Runtime State
============================================
A thread-safe snapshot of "what's happening right now", written by the
pipeline thread and read by the FastAPI backend (and, through it, the
Streamlit dashboard). Keeping this as one small class is what lets the
API just be a thin read-only wrapper around the pipeline's state.
"""

import threading
import time

from config.settings import MAX_HISTORY


class RuntimeState:
    def __init__(self, max_history: int = MAX_HISTORY):
        self._lock = threading.Lock()
        self.max_history = max_history

        self.running = False
        self.lane_id = None
        self.source = None
        self.started_at = None
        self.error = None

        self.counts = {}
        self.total_vehicles = 0
        self.density = "LOW"
        self.emergency = False
        self.green_time_s = 0

        self.signal_phase = "RED"
        self.signal_phase_duration = 0.0
        self.signal_phase_started_at = time.time()

        self.last_frame_jpeg = None
        self.history = []

    def update_detection(self, counts, total_vehicles, density, emergency, green_time_s):
        with self._lock:
            self.counts = counts
            self.total_vehicles = total_vehicles
            self.density = density
            self.emergency = emergency
            self.green_time_s = green_time_s
            self.history.append({
                "t": time.time(),
                "counts": counts,
                "total_vehicles": total_vehicles,
                "density": density,
                "emergency": emergency,
                "green_time_s": green_time_s,
            })
            if len(self.history) > self.max_history:
                self.history.pop(0)

    def update_signal(self, phase, duration):
        """Called once when the phase CHANGES (e.g. RED -> GREEN), with the
        full duration of the new phase. Remaining time is then computed live
        in snapshot() from the elapsed wall-clock time, so it actually counts
        down instead of showing the same static number for the whole phase."""
        with self._lock:
            self.signal_phase = phase
            self.signal_phase_duration = duration
            self.signal_phase_started_at = time.time()

    def update_frame(self, jpeg_bytes: bytes):
        with self._lock:
            self.last_frame_jpeg = jpeg_bytes

    def snapshot(self) -> dict:
        with self._lock:
            elapsed = time.time() - self.signal_phase_started_at
            remaining = max(0.0, self.signal_phase_duration - elapsed)
            return {
                "running": self.running,
                "lane_id": self.lane_id,
                "source": str(self.source),
                "counts": dict(self.counts),
                "total_vehicles": self.total_vehicles,
                "density": self.density,
                "emergency": self.emergency,
                "signal_phase": self.signal_phase,
                "signal_remaining": round(remaining, 1),
                "green_time_s": self.green_time_s,
                "started_at": self.started_at,
                "error": self.error,
            }

    def history_snapshot(self) -> list:
        with self._lock:
            return list(self.history)
