import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app import db
from app.model import generate
from app.products import PRODUCTS

ROOT = Path(__file__).resolve().parent.parent
FIGURES_DIR = ROOT / "results" / "figures"
METRICS_PATH = FIGURES_DIR / "summary_metrics.json"
STATIC_DIR = ROOT / "static"

app = FastAPI(title="Qwen0.5B Support Model Showcase")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/figures", StaticFiles(directory=FIGURES_DIR), name="figures")


@app.on_event("startup")
def on_startup():
    db.init()


class ChatRequest(BaseModel):
    message: str


class OrderItem(BaseModel):
    name: str
    price: float
    qty: int


class OrderRequest(BaseModel):
    items: list[OrderItem]
    total: float


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/products")
def products():
    return PRODUCTS


@app.get("/api/metrics")
def metrics():
    return json.loads(METRICS_PATH.read_text())


@app.get("/api/figures")
def figures():
    return sorted(p.name for p in FIGURES_DIR.glob("*.png"))


@app.post("/api/chat")
def chat(req: ChatRequest):
    reply = generate(req.message)
    return {"reply": reply}


@app.post("/api/orders")
def create_order(req: OrderRequest):
    items = [i.model_dump() for i in req.items]
    return db.create_order(items, req.total)


@app.get("/api/orders/{order_id}")
def read_order(order_id: int):
    order = db.get_order(order_id)
    if order is None:
        raise HTTPException(404, "Order not found")
    return order


@app.post("/api/orders/{order_id}/cancel")
def cancel_order(order_id: int):
    if db.get_order(order_id) is None:
        raise HTTPException(404, "Order not found")
    return db.cancel_order(order_id)
