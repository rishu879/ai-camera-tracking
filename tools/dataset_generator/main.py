"""CLI and Server entrypoint for Dataset Generator."""
import argparse
import uvicorn
from .config import DatasetGenerationRequest
from .service import DatasetGeneratorService


def parse_args():
    parser = argparse.ArgumentParser(description="FSOC Synthetic Dataset Generator Service")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind REST API")
    parser.add_argument("--port", type=int, default=8011, help="Port to bind REST API")
    parser.add_argument("--generate", action="store_true", help="Generate a sample dataset directly via CLI")
    parser.add_argument("--name", default="fsoc_sample_set", help="Dataset name")
    parser.add_argument("--frames", type=int, default=30, help="Number of frames")
    return parser.parse_args()


def main():
    args = parse_args()
    service = DatasetGeneratorService()

    if args.generate:
        print(f"Generating synthetic dataset '{args.name}' ({args.frames} frames)...")
        req = DatasetGenerationRequest(dataset_name=args.name, num_frames=args.frames)
        res = service.generate(req)
        print(f"Dataset generated at: {res['path']}")
        return

    print(f"Starting Dataset Generator on {args.host}:{args.port}...")
    uvicorn.run("tools.dataset_generator.api:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
