"""Run: python test_smoke.py"""
from fastapi.testclient import TestClient

from app.main import app
from app.products import is_on_topic, retrieve

client = TestClient(app)


def test_retrieve():
    # price cap respected, and returns fewer than full catalog
    r = retrieve("bluetooth earbuds under $60")
    assert r and all(p["price"] <= 60 for p in r)
    assert any("earbud" in p["name"].lower() for p in r)
    # keyword match narrows the pool
    assert len(retrieve("keyboard")) < 27
    # bare digits (price/qty) must not match numbers inside descriptions
    audio = retrieve("cheap audio under $50")
    assert all(p["category"] == "Audio" for p in audio), [p["name"] for p in audio]


def test_topic_gate():
    assert is_on_topic("suggest cheap audio under $50")
    assert is_on_topic("how do I get a refund?")
    assert is_on_topic("is the Pulse Smart Watch in stock?")
    assert not is_on_topic("what is the capital of Dhaka?")
    assert not is_on_topic("write me a poem about the moon")


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


def test_order_requires_login():
    # placing an order without a session is rejected
    r = client.post("/api/orders", json={"items": [{"name": "Terra Ceramic Mug", "price": 12.99, "qty": 1}], "total": 12.99})
    assert r.status_code == 401


def test_order_lifecycle():
    with TestClient(app) as c:
        assert c.post("/api/login", json={"email": "guest1@novagoods.com", "password": "guest1pw"}).status_code == 200
        r = c.post("/api/orders", json={"items": [{"name": "Terra Ceramic Mug", "price": 12.99, "qty": 2}], "total": 25.98})
        assert r.status_code == 200
        order = r.json()
        assert order["status"] == "placed"
        assert order["customer"] == "guest1@novagoods.com"

        r = c.post(f"/api/orders/{order['id']}/cancel")
        assert r.status_code == 200
        assert r.json()["status"] == "cancelled"

        r = c.post("/api/orders/999999/cancel")
        assert r.status_code == 404

    r = client.post(f"/api/orders/{order['id']}/cancel")
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"

    r = client.post("/api/orders/999999/cancel")
    assert r.status_code == 404


if __name__ == "__main__":
    test_retrieve()
    test_topic_gate()
    test_order_requires_login()
    test_metrics()
    test_figures()
    test_chat()
    test_order_lifecycle()
    print("smoke test OK")
