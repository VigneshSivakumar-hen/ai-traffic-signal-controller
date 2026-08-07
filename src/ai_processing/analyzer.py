"""
AI Processing Module — Traffic Analysis
==========================================
Turns raw per-frame detections into the summary numbers the Decision
Engine needs: counts by vehicle type, total count, and a density band.
"""

from collections import Counter

from config.settings import DENSITY_THRESHOLDS


class TrafficAnalyzer:
    def analyze(self, detections):
        counts = Counter(d["label"] for d in detections)
        total = sum(counts.values())
        return {
            "counts": dict(counts),
            "total_vehicles": total,
            "density": self._classify(total),
        }

    @staticmethod
    def _classify(total: int) -> str:
        if total <= DENSITY_THRESHOLDS["LOW"]:
            return "LOW"
        if total <= DENSITY_THRESHOLDS["MEDIUM"]:
            return "MEDIUM"
        return "HIGH"
