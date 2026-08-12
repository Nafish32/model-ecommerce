import json
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app import auth, db, model
from app.model import generate
from app.products import PRODUCTS, is_on_topic, retrieve

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
    session_id: str | None = None


# ponytail: in-memory session store, wiped on restart. Swap for Redis if it must survive restarts.
_SESSIONS: dict[str, list[dict]] = {}
_MAX_TURNS = 6  # keep last 3 user+bot exchanges as context


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
    sid = req.session_id or uuid4().hex
    # code-side topic gate: 0.5B won't reliably obey the prompt refusal rule, so block
    # off-topic here before spending a model call on it.
    if not is_on_topic(req.message):
        return {"reply": model.REFUSAL, "session_id": sid, "products": []}
    history = _SESSIONS.get(sid, [])
    matches = retrieve(req.message)
    reply = generate(req.message, context=matches, history=history)
    _SESSIONS[sid] = (history + [
        {"role": "user", "content": req.message},
        {"role": "assistant", "content": reply},
    ])[-_MAX_TURNS:]
    return {"reply": reply, "session_id": sid, "products": matches}


@app.post("/api/orders")
def create_order(req: OrderRequest, user: dict = Depends(auth.require_user)):
    items = [i.model_dump() for i in req.items]
    return db.create_order(items, req.total, customer=user.get("email") or "guest")


@app.get("/api/orders/mine")
def my_orders(user: dict = Depends(auth.require_user)):
    return db.list_orders_by_customer(user.get("email") or "guest")


class ReviewRequest(BaseModel):
    product: str
    rating: int
    text: str


@app.post("/api/reviews")
def create_review(req: ReviewRequest, user: dict = Depends(auth.require_user)):
    email = user.get("email") or "guest"
    if req.product not in db.purchased_products(email):
        raise HTTPException(403, "You can only review a product you have purchased.")
    if not (1 <= req.rating <= 5):
        raise HTTPException(422, "Rating must be 1–5.")
    if not req.text.strip():
        raise HTTPException(422, "Review text is required.")
    return db.add_review(req.product, db.display_name(email), req.rating, req.text.strip())


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


# --- admin ---

class LoginRequest(BaseModel):
    email: str
    password: str


class OrderUpdate(BaseModel):
    status: str


@app.get("/admin")
def admin_page():
    return FileResponse(STATIC_DIR / "admin.html")


@app.post("/api/admin/login")
def admin_login(req: LoginRequest, response: Response):
    user = db.get_user_by_email(req.email)
    if not user or not auth.verify_password(req.password, user["password_hash"]):
        raise HTTPException(401, "Invalid email or password")
    if user["role"] != "admin":
        raise HTTPException(403, "Not an admin account")
    response.set_cookie(
        auth.COOKIE, auth.make_token(user["id"], user["role"], user["email"]),
        httponly=True, samesite="lax", max_age=auth.TTL,
    )
    return {"email": user["email"], "role": user["role"]}


# --- customer auth (storefront): any valid account may log in to shop ---

@app.post("/api/login")
def login(req: LoginRequest, response: Response):
    user = db.get_user_by_email(req.email)
    if not user or not auth.verify_password(req.password, user["password_hash"]):
        raise HTTPException(401, "Invalid email or password")
    response.set_cookie(
        auth.COOKIE, auth.make_token(user["id"], user["role"], user["email"]),
        httponly=True, samesite="lax", max_age=auth.TTL,
    )
    return {"email": user["email"], "role": user["role"]}


@app.get("/api/me")
def me(user: dict = Depends(auth.require_user)):
    return {"email": user.get("email"), "role": user.get("role")}


@app.post("/api/logout")
def logout(response: Response):
    response.delete_cookie(auth.COOKIE)
    return {"ok": True}


@app.post("/api/admin/logout")
def admin_logout(response: Response):
    response.delete_cookie(auth.COOKIE)
    return {"ok": True}


@app.get("/api/admin/me")
def admin_me(admin: dict = Depends(auth.require_admin)):
    return {"role": admin["role"]}


@app.get("/api/admin/analytics")
def admin_analytics(admin: dict = Depends(auth.require_admin)):
    return db.analytics()


@app.get("/api/admin/orders")
def admin_orders(admin: dict = Depends(auth.require_admin)):
    return db.list_orders()


@app.put("/api/admin/orders/{order_id}")
def admin_update_order(order_id: int, req: OrderUpdate, admin: dict = Depends(auth.require_admin)):
    order = db.update_order(order_id, req.status)
    if order is None:
        raise HTTPException(404, "Order not found")
    return order


@app.delete("/api/admin/orders/{order_id}")
def admin_delete_order(order_id: int, admin: dict = Depends(auth.require_admin)):
    if not db.delete_order(order_id):
        raise HTTPException(404, "Order not found")
    return {"ok": True}


@app.get("/api/admin/reviews")
def admin_reviews(admin: dict = Depends(auth.require_admin)):
    return db.list_reviews()
