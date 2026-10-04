"""CLI and Server entrypoint for Noise Generator."""
import argparse
import uvicorn
from .service import NoiseGeneratorService


def parse_args():
    parser = argparse.ArgumentParser(description="FSOC Sensor Noise Generator")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind REST API")
    parser.add_argument("--port", type=int, default=8006, help="Port to bind REST API")
    return parser.parse_args()


def main():
    args = parse_args()
    print(f"Starting Sensor Noise Generator on {args.host}:{args.port}...")
    uvicorn.run("tools.noise_generator.api:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
