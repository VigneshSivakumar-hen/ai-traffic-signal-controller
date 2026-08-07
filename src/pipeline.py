"""
TrafficPipeline — the main orchestrator
==========================================
Wires together every module in the architecture diagram:

    VideoStream -> VehicleDetector -> SimpleTracker -> TrafficAnalyzer
        -> SignalOptimizer -> TrafficLightController -> RuntimeState

Runs its own background thread so it can be driven either standalone
(run_simulation.py) or from the FastAPI backend (backend/api.py).
"""

import logging
import threading
import time

import cv2

from config.settings import DETECTION_INTERVAL_SEC, MODEL_NAME
from src.ai_processing.analyzer import TrafficAnalyzer
from src.ai_processing.detector import VehicleDetector
from src.ai_processing.tracker import SimpleTracker
from src.data_collection.video_capture import VideoStream
from src.decision_engine.optimizer import SignalOptimizer
from src.monitoring.state import RuntimeState
from src.signal_controller.controller import TrafficLightController

logger = logging.getLogger(__name__)


class TrafficPipeline:
    def __init__(self, video_source, lane_id: str = "north",
                 model_name: str = MODEL_NAME, emergency_flag_fn=None):
        self.video_source = video_source
        self.lane_id = lane_id

        self.state = RuntimeState()
        self.state.lane_id = lane_id
        self.state.source = video_source

        self.detector = VehicleDetector(model_name)
        self.tracker = SimpleTracker()
        self.analyzer = TrafficAnalyzer()
        self.optimizer = SignalOptimizer()
        self.controller = TrafficLightController(lane_id=lane_id, on_change=self._on_signal_change)

        # Hook for a real emergency detector later (see README "Next Steps").
        # Defaults to "never emergency" so the branch is exercised only when
        # something actually wires a detector or a manual trigger in here.
        self.emergency_flag_fn = emergency_flag_fn or (lambda: False)

        self.video = None
        self._stop_event = threading.Event()
        self._thread = None

    def _on_signal_change(self, phase, duration):
        self.state.update_signal(phase, duration)
        logger.info("[%s] signal -> %s (%.0fs)", self.lane_id, phase, duration)

    def start(self):
        self.video = VideoStream(self.video_source).start()
        self.controller.start()
        self.state.running = True
        self.state.started_at = time.time()
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("Pipeline started: lane=%s source=%s", self.lane_id, self.video_source)

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=3)
        self.controller.stop()
        if self.video:
            self.video.stop()
        self.state.running = False
        logger.info("Pipeline stopped: lane=%s", self.lane_id)

    def _run(self):
        last_detect = 0.0
        while not self._stop_event.is_set():
            frame = self.video.read()
            if frame is None:
                time.sleep(0.05)
                continue

            annotated = frame
            now = time.time()
            if now - last_detect >= DETECTION_INTERVAL_SEC:
                last_detect = now
                annotated = self._detect_and_decide(frame)

            ok, buf = cv2.imencode(".jpg", annotated)
            if ok:
                self.state.update_frame(buf.tobytes())

            time.sleep(0.01)

    def _detect_and_decide(self, frame):
        try:
            detections = self.detector.detect(frame)
        except Exception:
            logger.exception("Detection failed on a frame; skipping it")
            detections = []

        # Tracking currently exists to de-duplicate across samples; wire its
        # output into TrafficAnalyzer once you want ID-aware queue length
        # instead of a raw per-sample count.
        self.tracker.update(detections)

        result = self.analyzer.analyze(detections)
        emergency = bool(self.emergency_flag_fn())
        density_used, green_time = self.optimizer.decide(result["density"], emergency)
        self.controller.request_green_time(green_time)

        self.state.update_detection(
            counts=result["counts"],
            total_vehicles=result["total_vehicles"],
            density=density_used,
            emergency=emergency,
            green_time_s=green_time,
        )

        return self._draw(frame, detections, density_used, green_time, emergency)

    @staticmethod
    def _draw(frame, detections, density, green_time, emergency):
        out = frame.copy()
        for d in detections:
            x1, y1, x2, y2 = d["bbox"]
            cv2.rectangle(out, (x1, y1), (x2, y2), (46, 179, 68), 2)
            cv2.putText(out, d["label"], (x1, max(0, y1 - 6)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (46, 179, 68), 1)
        label = f"Density: {density} | Green: {green_time}s"
        if emergency:
            label += " | EMERGENCY"
        cv2.putText(out, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                    (0, 0, 255) if emergency else (255, 255, 0), 2)
        return out
