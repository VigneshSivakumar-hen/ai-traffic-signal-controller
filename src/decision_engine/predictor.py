"""
Decision Engine — Traffic Predictor (stub)
=============================================
Placeholder for an LSTM / Random Forest model that predicts near-future
congestion from historical density/queue data, per the README's Next
Steps. Not wired into the live decision loop yet — train()/predict() are
stubs so the interface is ready once you have enough logged history
(pull it from RuntimeState.history_snapshot() via the /metrics endpoint,
or the CSV export in the earlier standalone script).
"""


class TrafficPredictor:
    def __init__(self):
        self.is_trained = False

    def train(self, history: list[dict]):
        """
        history: list of samples like
            {"t": <unix_ts>, "total_vehicles": int, "density": str, ...}
        Fit an LSTM (time-series) or Random Forest (tabular features:
        hour-of-day, rolling averages, etc.) here.
        """
        raise NotImplementedError(
            "Train on historical density/queue data here (see README 'Next Steps')."
        )

    def predict(self, recent_history: list[dict]):
        """Return a predicted density/queue length for the next interval."""
        raise NotImplementedError("Wire in a trained model here.")
