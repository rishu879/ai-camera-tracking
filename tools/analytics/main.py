"""CLI and Server entrypoint for Analytics Service."""
import argparse
import uvicorn
from .service import AnalyticsService


def parse_args():
    parser = argparse.ArgumentParser(description="FSOC Analytics Dashboard Service")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind REST API")
    parser.add_argument("--port", type=int, default=8013, help="Port to bind REST API")
    return parser.parse_args()


def main():
    args = parse_args()
    print(f"Starting Analytics Dashboard on {args.host}:{args.port}...")
    uvicorn.run("tools.analytics.api:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
