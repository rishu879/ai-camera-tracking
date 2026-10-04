"""CLI and Server entrypoint for Replay System and Benchmark-2 Runner."""
import argparse
import sys
import uvicorn
from .config import Benchmark2Request
from .service import ReplayService


def parse_args():
    parser = argparse.ArgumentParser(description="FSOC Replay System & Benchmark-2 Evaluation Runner")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind REST API")
    parser.add_argument("--port", type=int, default=8014, help="Port to bind REST API")
    parser.add_argument("--benchmark2", type=str, default=None, help="Directly run Benchmark-2 on input .mp4 video file")
    parser.add_argument("--gt", type=str, default=None, help="Ground-truth file (.csv or .json)")
    return parser.parse_args()


def main():
    args = parse_args()
    service = ReplayService()

    if args.benchmark2:
        print(f"Running ISRO Benchmark-2 evaluation on video: {args.benchmark2}")
        req = Benchmark2Request(video_path=args.benchmark2, ground_truth_path=args.gt)
        results = service.run_benchmark_2(req)
        print("Benchmark-2 Evaluation Complete:")
        import json
        print(json.dumps(results["summary_metrics"], indent=2))
        return

    print(f"Starting Replay System & Benchmark Runner on {args.host}:{args.port}...")
    uvicorn.run("tools.replay_system.api:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
