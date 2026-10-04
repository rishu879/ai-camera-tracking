"""CLI and Server entrypoint for Object Detection Service."""
import argparse
import uvicorn
from .service import ObjectDetectionService


def parse_args():
    parser = argparse.ArgumentParser(description="FSOC Object Detection Service")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind REST API")
    parser.add_argument("--port", type=int, default=8007, help="Port to bind REST API")
    parser.add_argument("--model", default="adaptive", choices=["adaptive", "yolov11", "hybrid"], help="Detector model")
    return parser.parse_args()


def main():
    args = parse_args()
    service = ObjectDetectionService()
    service.set_strategy(args.model)
    print(f"Starting Object Detection Service ({args.model}) on {args.host}:{args.port}...")
    uvicorn.run("tools.object_detection.api:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
