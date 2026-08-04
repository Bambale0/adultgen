from pathlib import Path

CORE_API = Path("src/adultgen/apps/core_api.py")
WORKSPACE_ROUTER = Path("src/adultgen/api/routers/workspace.py")
WORKSPACE_CLIENT = Path("apps/mini_app/src/workspace.ts")
CREATE_FLOW = Path("apps/mini_app/src/createFlow.tsx")
APP_TSX = Path("apps/mini_app/src/App.tsx")


def test_core_api_registers_workspace_router() -> None:
    content = CORE_API.read_text()

    assert "workspace" in content
    assert "workspace.router" in content


def test_workspace_router_exposes_avatar_project_scene_endpoints() -> None:
    content = WORKSPACE_ROUTER.read_text()

    assert "/avatars" in content
    assert "/projects" in content
    assert "/projects/{project_id}/scenes" in content
    assert "get_current_token_claims" in content


def test_mini_app_workspace_client_calls_backend_endpoints() -> None:
    content = WORKSPACE_CLIENT.read_text()

    assert "/workspace/avatars" in content
    assert "/workspace/projects" in content
    assert "/scenes" in content
    assert "Authorization" in content


def test_create_flow_creates_avatar_project_and_scene() -> None:
    content = CREATE_FLOW.read_text()

    assert "createAvatarProfile" in content
    assert "createProject" in content
    assert "createScene" in content


def test_app_wires_create_route_to_create_flow() -> None:
    content = APP_TSX.read_text()

    assert "CreateFlowStarter" in content
    assert "activeRoute.id === 'create'" in content
