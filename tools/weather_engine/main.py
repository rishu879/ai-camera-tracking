"""CLI and Server entrypoint for Weather Engine."""
import argparse
import uvicorn
from .service import WeatherEngineService


def parse_args():
    parser = argparse.ArgumentParser(description="FSOC Atmospheric Weather Engine")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind REST API")
    parser.add_argument("--port", type=int, default=8005, help="Port to bind REST API")
    return parser.parse_args()


def main():
    args = parse_args()
    print(f"Starting Atmospheric Weather Engine on {args.host}:{args.port}...")
    uvicorn.run("tools.weather_engine.api:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
