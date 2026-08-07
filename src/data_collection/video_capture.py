"""
Data Collection Module
=======================
Wraps cv2.VideoCapture in a background thread so frame-reading never blocks
the AI processing loop. Handles three source types the same way:
  - int (e.g. 0)      -> webcam
  - "path/to.mp4"      -> video file (loops back to frame 0 at EOF)
  - "rtsp://..."        -> live IP camera (reconnects on drop)
"""

import logging
import threading
import time

import cv2

logger = logging.getLogger(__name__)


def _is_video_file(source) -> bool:
    return isinstance(source, str) and not source.lower().startswith("rtsp://")


class VideoStream:
    def __init__(self, source):
        self.source = source
        self.is_file = _is_video_file(source)
        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open video source: {source!r}")

        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self._frame = None
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread = None
        self.frame_count = 0

    def start(self) -> "VideoStream":
        self._thread = threading.Thread(target=self._update, daemon=True)
        self._thread.start()
        return self

    def _update(self):
        consecutive_failures = 0
        while not self._stop_event.is_set():
            ret, frame = self.cap.read()

            if not ret:
                consecutive_failures += 1
                if self.is_file:
                    # End of a finite video file: loop back to the start.
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                else:
                    # Webcam/RTSP: transient drop -> back off and retry the
                    # same handle. Live feeds are a later extension point,
                    # but the reconnect loop is already here for it.
                    if consecutive_failures % 20 == 1:
                        logger.warning("Read failed for source=%s, retrying...", self.source)
                    time.sleep(0.3)
                continue

            consecutive_failures = 0
            with self._lock:
                self._frame = frame
                self.frame_count += 1

    def read(self):
        """Returns the latest frame (a copy) or None if nothing has arrived yet."""
        with self._lock:
            return None if self._frame is None else self._frame.copy()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)
        self.cap.release()
