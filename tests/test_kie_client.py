import pytest

from adultgen.integrations.kie.client import KieClientError, extract_kie_task_id


def test_extract_kie_task_id_from_nested_task_id() -> None:
    assert extract_kie_task_id({"data": {"taskId": "task_123"}}) == "task_123"


def test_extract_kie_task_id_from_top_level_task_id() -> None:
    assert extract_kie_task_id({"task_id": "task_456"}) == "task_456"


def test_extract_kie_task_id_rejects_missing_id() -> None:
    with pytest.raises(KieClientError, match="task id"):
        extract_kie_task_id({"code": 200, "data": {"status": "created"}})
