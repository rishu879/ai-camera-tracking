"""CLI and Server entrypoint for Logger Service."""
import argparse
import uvicorn
from .service import LoggingService


def parse_args():
    parser = argparse.ArgumentParser(description="FSOC Structured Logger Service")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind REST API")
    parser.add_argument("--port", type=int, default=8002, help="Port to bind REST API")
    return parser.parse_args()


def main():
    args = parse_args()
    service = LoggingService()
    service.log_event("LOGGER_BOOT", {"host": args.host, "port": args.port}, severity="INFO")
    print(f"Starting Logger Service on {args.host}:{args.port}...")
    uvicorn.run("tools.logging.api:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
