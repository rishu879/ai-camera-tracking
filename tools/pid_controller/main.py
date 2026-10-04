"""CLI and Server entrypoint for PID Camera Controller."""
import argparse
import uvicorn
from .service import PIDCameraControlService


def parse_args():
    parser = argparse.ArgumentParser(description="FSOC PID Camera Controller Service")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind REST API")
    parser.add_argument("--port", type=int, default=8010, help="Port to bind REST API")
    return parser.parse_args()


def main():
    args = parse_args()
    print(f"Starting PID Camera Controller on {args.host}:{args.port}...")
    uvicorn.run("tools.pid_controller.api:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
