"""
Signal Controller Module
===========================
A background-thread state machine that cycles GREEN -> YELLOW -> RED for one
lane. The pipeline calls request_green_time() whenever a new density
decision comes in; that value is picked up at the START of the next GREEN
phase (mid-phase changes don't interrupt an in-progress yellow/red, which
mirrors how a real intersection controller behaves).

apply() is the single hook point described in the README for wiring to real
hardware ("Wire TrafficLightController.apply() to GPIO pins") — right now it
just calls the on_change callback so RuntimeState/the API can reflect it.
"""

import threading
import time

from config.settings import GREEN_TIME_TABLE, MIN_RED_TIME, YELLOW_TIME


class TrafficLightController:
    def __init__(self, lane_id: str, on_change=None):
        self.lane_id = lane_id
        self.on_change = on_change  # callback(phase: str, duration: float)

        self.phase = "RED"
        self.phase_started_at = time.time()
        self.phase_duration = MIN_RED_TIME

        self._next_green = GREEN_TIME_TABLE["LOW"]
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread = None

    def request_green_time(self, seconds: int):
        with self._lock:
            self._next_green = seconds

    def start(self):
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)

    @property
    def remaining(self) -> float:
        with self._lock:
            return max(0.0, self.phase_duration - (time.time() - self.phase_started_at))

    def _run(self):
        while not self._stop_event.is_set():
            with self._lock:
                green_seconds = self._next_green
            self._set_phase("GREEN", green_seconds)
            self._sleep_phase()

            self._set_phase("YELLOW", YELLOW_TIME)
            self._sleep_phase()

            self._set_phase("RED", MIN_RED_TIME)
            self._sleep_phase()

    def _sleep_phase(self):
        end = self.phase_started_at + self.phase_duration
        while time.time() < end and not self._stop_event.is_set():
            time.sleep(0.1)

    def _set_phase(self, phase: str, duration: float):
        with self._lock:
            self.phase = phase
            self.phase_duration = duration
            self.phase_started_at = time.time()
        self.apply()

    def apply(self):
        """Hardware hook: wire GPIO output here for a Raspberry Pi deployment."""
        if self.on_change:
            self.on_change(self.phase, self.phase_duration)
