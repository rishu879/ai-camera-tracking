"""Unit tests for Dataset Generator."""
from pathlib import Path
from fastapi.testclient import TestClient
from tools.dataset_generator.api import app, service
from tools.dataset_generator.config import DatasetGenerationRequest


def test_dataset_generator_health():
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["data"]["service"] == "dataset_generator"


def test_dataset_generation_pipeline(tmp_path):
    temp_service = service.__class__(root_output_dir=str(tmp_path))
    req = DatasetGenerationRequest(
        dataset_name="unit_test_dataset",
        num_frames=10,
        export_video=True,
    )
    result = temp_service.generate(req)

    assert result["total_frames"] == 10
    dataset_dir = Path(result["path"])
    assert dataset_dir.exists()
    assert (dataset_dir / "images").exists()
    assert (dataset_dir / "labels").exists()
    assert (dataset_dir / "annotations_coco.json").exists()
    assert (dataset_dir / "gt" / "gt.txt").exists()
    assert (dataset_dir / "metadata.json").exists()
    assert (dataset_dir / "unit_test_dataset.mp4").exists()
