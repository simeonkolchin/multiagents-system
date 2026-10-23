import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        reg = await ac.post(
            "/api/auth/register",
            json={"email": "test@example.com", "password": "secret123"},
        )
        token = reg.json()["access_token"]
        ac.headers["Authorization"] = f"Bearer {token}"
        yield ac


async def test_health(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_auth_required():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/sessions")
    assert response.status_code in (401, 403)


async def test_full_flow(client):
    seed = await client.post("/api/demo/seed")
    assert seed.status_code == 200
    ids = seed.json()

    created = await client.post(
        "/api/sessions",
        json={"rubric_id": ids["rubric_id"], "interview_id": ids["interview_id"]},
    )
    assert created.status_code == 200
    session = created.json()
    assert session["status"] == "ready"
    rows = {r["competency_id"]: r for r in session["scorecard"]["rows"]}
    assert rows["operations"]["sufficiency"] == "no_data"
    assert rows["solution_design"]["disputed"] is True

    session_id = session["id"]

    evaluation = await client.get(f"/api/sessions/{session_id}/evaluation")
    assert evaluation.status_code == 200
    metrics = evaluation.json()
    assert (
        metrics["baseline"]["unsupported_conclusions"]
        > metrics["multi_agent"]["unsupported_conclusions"]
    )

    docx = await client.get(f"/api/sessions/{session_id}/export.docx")
    assert docx.status_code == 200
    assert len(docx.content) > 0

    audit = await client.post(
        f"/api/sessions/{session_id}/audit",
        json={"competency_id": "solution_design", "claim": "слабый system design"},
    )
    assert audit.status_code == 200
    assert audit.json()["supported"] is False


async def test_transcribe_mock(client):
    files = {"file": ("demo.wav", b"fake-audio-bytes", "audio/wav")}
    response = await client.post("/api/transcribe", files=files)
    assert response.status_code == 200
    body = response.json()
    assert len(body["episodes"]) == 11
    assert "Кандидат" in body["text"]
