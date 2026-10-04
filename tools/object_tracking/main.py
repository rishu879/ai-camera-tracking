"""CLI and Server entrypoint for Object Tracking Service."""
import argparse
import uvicorn
from .service import ObjectTrackingService


def parse_args():
    parser = argparse.ArgumentParser(description="FSOC Object Tracking Service")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind REST API")
    parser.add_argument("--port", type=int, default=8008, help="Port to bind REST API")
    return parser.parse_args()


def main():
    args = parse_args()
    print(f"Starting Object Tracking Service on {args.host}:{args.port}...")
    uvicorn.run("tools.object_tracking.api:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
