import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.model import generate

ROOT = Path(__file__).resolve().parent.parent
FIGURES_DIR = ROOT / "results" / "figures"
METRICS_PATH = FIGURES_DIR / "summary_metrics.json"
STATIC_DIR = ROOT / "static"

app = FastAPI(title="Qwen0.5B Support Model Showcase")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/figures", StaticFiles(directory=FIGURES_DIR), name="figures")


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


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
