"""Run: python test_smoke.py"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_metrics():
    r = client.get("/api/metrics")
    assert r.status_code == 200
    body = r.json()
    assert "base" in body and "fine_tuned" in body


def test_figures():
    r = client.get("/api/figures")
    assert r.status_code == 200
    assert len(r.json()) > 0


def test_chat():
    r = client.post("/api/chat", json={"message": "How do I reset my password?"})
    assert r.status_code == 200
    assert len(r.json()["reply"]) > 0


def test_order_lifecycle():
    r = client.post("/api/orders", json={"items": [{"name": "Ceramic Mug", "price": 12.99, "qty": 2}], "total": 25.98})
    assert r.status_code == 200
    order = r.json()
    assert order["status"] == "placed"

    r = client.post(f"/api/orders/{order['id']}/cancel")
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"

    r = client.post("/api/orders/999999/cancel")
    assert r.status_code == 404


if __name__ == "__main__":
    test_metrics()
    test_figures()
    test_chat()
    test_order_lifecycle()
    print("smoke test OK")
