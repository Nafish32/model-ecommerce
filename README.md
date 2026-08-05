# Model Ecommerce

Demo storefront ("Nova Goods") with a support chat widget backed by a
Qwen2.5-0.5B model LoRA-fine-tuned for customer support. FastAPI backend,
vanilla HTML/CSS/JS frontend.

## Setup

```
pip install -r requirements.txt
```

The backend loads weights from `results/qwen05b-support-merged/`. The
merged `model.safetensors` (~940MB) is excluded from this repo via
`.gitignore` — place it in that folder yourself (merge the LoRA adapter
in `results/qwen05b-support-lora/` onto `Qwen/Qwen2.5-0.5B-Instruct`, or
copy the file in from wherever the model was trained).

## Run

```
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000.

## Layout

- `app/` — FastAPI backend (`main.py` routes, `model.py` inference)
- `static/` — landing page, styles, chat widget JS
- `results/` — training metrics, figures, and model artifacts
- `test_smoke.py` — endpoint smoke test (`python test_smoke.py`)
- `master_plan.xml` — build roadmap this project followed
