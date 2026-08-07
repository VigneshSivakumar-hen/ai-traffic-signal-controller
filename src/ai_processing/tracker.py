"""
AI Processing Module — Tracking
=================================
SimpleTracker: a minimal centroid tracker that assigns persistent IDs to
detections across frames by nearest-centroid matching. It's not as robust
as DeepSORT (README's suggested upgrade — it'll lose IDs on occlusion or
fast motion), but it needs zero extra dependencies and is enough to reduce
double-counting between consecutive detection samples.

Swap this class out for a DeepSORT-based tracker later without touching
anything else — analyzer.py only relies on the list-of-dicts shape returned
by update().
"""

import math


class SimpleTracker:
    def __init__(self, max_distance: float = 80.0, max_missed: int = 5):
        self.next_id = 0
        self.objects = {}  # id -> {"centroid": (x, y), "label": str, "missed": int}
        self.max_distance = max_distance
        self.max_missed = max_missed

    @staticmethod
    def _centroid(bbox):
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    def update(self, detections):
        input_centroids = [self._centroid(d["bbox"]) for d in detections]

        if not self.objects:
            for det, c in zip(detections, input_centroids):
                self._register(det, c)
            return self._as_tracks()

        object_ids = list(self.objects.keys())
        object_centroids = [self.objects[i]["centroid"] for i in object_ids]

        unmatched_objects = set(range(len(object_centroids)))
        unmatched_inputs = set(range(len(input_centroids)))

        candidate_pairs = []
        for oi, oc in enumerate(object_centroids):
            for ii, ic in enumerate(input_centroids):
                candidate_pairs.append((math.dist(oc, ic), oi, ii))
        candidate_pairs.sort(key=lambda p: p[0])

        for dist, oi, ii in candidate_pairs:
            if oi not in unmatched_objects or ii not in unmatched_inputs:
                continue
            if dist > self.max_distance:
                continue
            obj_id = object_ids[oi]
            self.objects[obj_id]["centroid"] = input_centroids[ii]
            self.objects[obj_id]["label"] = detections[ii]["label"]
            self.objects[obj_id]["missed"] = 0
            unmatched_objects.discard(oi)
            unmatched_inputs.discard(ii)

        for oi in unmatched_objects:
            obj_id = object_ids[oi]
            self.objects[obj_id]["missed"] += 1
            if self.objects[obj_id]["missed"] > self.max_missed:
                del self.objects[obj_id]

        for ii in unmatched_inputs:
            self._register(detections[ii], input_centroids[ii])

        return self._as_tracks()

    def _register(self, det, centroid):
        self.objects[self.next_id] = {
            "centroid": centroid, "label": det["label"], "missed": 0,
        }
        self.next_id += 1

    def _as_tracks(self):
        return [
            {"id": obj_id, "centroid": o["centroid"], "label": o["label"]}
            for obj_id, o in self.objects.items() if o["missed"] == 0
        ]
