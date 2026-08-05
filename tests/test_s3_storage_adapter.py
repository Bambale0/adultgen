from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
ENV_EXAMPLE = ROOT / ".env.example"
CONFIG = ROOT / "src" / "adultgen" / "config.py"
STORAGE_FACTORY = ROOT / "src" / "adultgen" / "api" / "storage.py"
S3_ADAPTER = ROOT / "src" / "adultgen" / "storage" / "s3.py"


def test_s3_dependency_and_env_are_declared() -> None:
    pyproject = PYPROJECT.read_text(encoding="utf-8")
    env_example = ENV_EXAMPLE.read_text(encoding="utf-8")
    config = CONFIG.read_text(encoding="utf-8")

    assert "boto3" in pyproject
    assert "OBJECT_STORAGE_BACKEND=local" in env_example
    assert "S3_REGION_NAME=us-east-1" in env_example
    assert "object_storage_backend" in config
    assert "s3_region_name" in config


def test_s3_adapter_implements_object_storage_methods() -> None:
    content = S3_ADAPTER.read_text(encoding="utf-8")

    assert "class S3ObjectStorage" in content
    assert "boto3.client" in content
    assert "asyncio.to_thread" in content
    assert "def put_object" in content
    assert "def copy_object" in content
    assert "def delete_object" in content
    assert "def get_object" in content
    assert "StoredObject" in content


def test_storage_factory_supports_local_and_s3_backends() -> None:
    content = STORAGE_FACTORY.read_text(encoding="utf-8")

    assert 'backend == "local"' in content
    assert 'backend == "s3"' in content
    assert "LocalObjectStorage" in content
    assert "S3ObjectStorage" in content
    assert "Unsupported object storage backend" in content
