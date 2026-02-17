from fastapi.testclient import TestClient
from webapp.server.main import app

client = TestClient(app)

def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_actions_list_empty():
    r = client.get("/api/actions")
    assert r.status_code == 200
    assert "data" in r.json()
