"""CLI and Server entrypoint for Configuration Manager."""
import argparse
import sys
import uvicorn
from .service import ConfigurationService


def parse_args():
    parser = argparse.ArgumentParser(description="FSOC Configuration Manager Service")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind REST API")
    parser.add_argument("--port", type=int, default=8001, help="Port to bind REST API")
    parser.add_argument("--show", action="store_true", help="Print active configuration to stdout")
    parser.add_argument("--profile", type=str, default=None, help="Load specified profile before running")
    return parser.parse_args()


def main():
    args = parse_args()
    service = ConfigurationService()

    if args.profile:
        print(f"Loading profile: {args.profile}")
        service.load_profile(args.profile)

    if args.show:
        import json
        print(json.dumps(service.get_config_dict(), indent=2))
        sys.exit(0)

    print(f"Starting Configuration Manager on {args.host}:{args.port}...")
    uvicorn.run("tools.configuration.api:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
