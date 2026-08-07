"""Run the traffic pipeline standalone (no API)."""

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.pipeline import TrafficPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main():
    parser = argparse.ArgumentParser(description="AI Traffic Signal Controller — Simulation")
    parser.add_argument("--source", default="0", help="Webcam index, video path, or RTSP URL")
    parser.add_argument("--lane", default="north", help="Primary lane ID")
    args = parser.parse_args()

    source: str | int = args.source
    if source.isdigit():
        source = int(source)

    pipeline = TrafficPipeline(video_source=source, lane_id=args.lane)
    pipeline.start()

    print("Pipeline running. Press Ctrl+C to stop.")
    try:
        while True:
            import time

            time.sleep(1)
    except KeyboardInterrupt:
        pipeline.stop()
        print("Stopped.")


if __name__ == "__main__":
    main()
