"""
AI Processing Module — Vehicle Detection
==========================================
Thin wrapper around Ultralytics YOLOv8, filtered to the vehicle classes we
care about (see config.settings.VEHICLE_CLASSES).
"""

from config.settings import VEHICLE_CLASSES, MODEL_NAME


class VehicleDetector:
    def __init__(self, model_name: str = MODEL_NAME):
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise SystemExit(
                "ultralytics is not installed. Run: pip install -r requirements.txt"
            ) from exc
        self.model = YOLO(model_name)

    def detect(self, frame):
        """
        Returns a list of dicts: {"label": str, "conf": float, "bbox": (x1,y1,x2,y2)}
        restricted to car/bike/bus/truck.
        """
        results = self.model(frame, verbose=False)[0]
        detections = []
        for box in results.boxes:
            cls_id = int(box.cls[0])
            cls_name = self.model.names[cls_id]
            if cls_name not in VEHICLE_CLASSES:
                continue
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            detections.append({
                "label": VEHICLE_CLASSES[cls_name],
                "conf": float(box.conf[0]),
                "bbox": (x1, y1, x2, y2),
            })
        return detections
