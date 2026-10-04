"""CLI and Server entrypoint for Virtual Camera."""
import argparse
import uvicorn
from .service import VirtualCameraService


def parse_args():
    parser = argparse.ArgumentParser(description="FSOC Virtual PTZ Camera Service")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind REST API")
    parser.add_argument("--port", type=int, default=8004, help="Port to bind REST API")
    return parser.parse_args()


def main():
    args = parse_args()
    print(f"Starting Virtual PTZ Camera on {args.host}:{args.port}...")
    uvicorn.run("tools.virtual_camera.api:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
