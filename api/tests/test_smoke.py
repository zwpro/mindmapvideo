"""健康检查与基础冒烟测试。"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"


@pytest.mark.asyncio
async def test_create_and_get_project() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create = await client.post("/api/v1/projects", json={"topic": "人工智能发展史"})
        assert create.status_code == 201
        project_id = create.json()["id"]

        detail = await client.get(f"/api/v1/projects/{project_id}")
        assert detail.status_code == 200
        assert detail.json()["topic"] == "人工智能发展史"


@pytest.mark.asyncio
async def test_scenes_preview() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/scenes", params={"topic": "人工智能"})
    assert resp.status_code == 200
    scenes = resp.json()
    assert isinstance(scenes, list)
    assert len(scenes) >= 5
    assert {"id", "index", "title", "content"} <= set(scenes[0].keys())
