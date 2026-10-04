"""CLI and Server entrypoint for Performance Monitor."""
import argparse
import uvicorn
from .service import PerformanceMonitorService


def parse_args():
    parser = argparse.ArgumentParser(description="FSOC Performance Monitor Service")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind REST API")
    parser.add_argument("--port", type=int, default=8012, help="Port to bind REST API")
    return parser.parse_args()


def main():
    args = parse_args()
    print(f"Starting Performance Monitor on {args.host}:{args.port}...")
    uvicorn.run("tools.performance_monitor.api:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
