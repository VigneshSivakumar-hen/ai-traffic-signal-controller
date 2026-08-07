"""
Decision Engine — Signal Optimizer
=====================================
Rule-based decision: density -> green time, with an emergency override.

Kept deliberately dumb and swappable: decide() is the exact seam where a
Q-Learning agent or a trained predictor would plug in later (see README
"Next Steps" -> Reinforcement Learning). Anything that calls this class
only needs decide(density, emergency) -> (density_label, green_seconds).
"""

from config.settings import GREEN_TIME_TABLE


class SignalOptimizer:
    def decide(self, density: str, emergency: bool = False) -> tuple[str, int]:
        if emergency:
            return "EMERGENCY", GREEN_TIME_TABLE["EMERGENCY"]
        return density, GREEN_TIME_TABLE[density]
