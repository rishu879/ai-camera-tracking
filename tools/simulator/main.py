"""CLI and Server entrypoint for Virtual Environment Simulator."""
import argparse
import uvicorn
from .service import SimulatorService


def parse_args():
    parser = argparse.ArgumentParser(description="FSOC Virtual Environment Simulator")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind REST API")
    parser.add_argument("--port", type=int, default=8003, help="Port to bind REST API")
    return parser.parse_args()


def main():
    args = parse_args()
    print(f"Starting Virtual Environment Simulator on {args.host}:{args.port}...")
    uvicorn.run("tools.simulator.api:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
