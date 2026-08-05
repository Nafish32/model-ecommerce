import threading
from pathlib import Path

from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_DIR = Path(__file__).resolve().parent.parent / "results" / "qwen05b-support-merged"

_tokenizer = None
_model = None
_lock = threading.Lock()


def load():
    global _tokenizer, _model
    if _model is not None:
        return
    _tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    _model = AutoModelForCausalLM.from_pretrained(MODEL_DIR)
    _model.eval()


def generate(message: str, max_new_tokens: int = 256) -> str:
    load()
    messages = [{"role": "user", "content": message}]
    inputs = _tokenizer.apply_chat_template(
        messages, add_generation_prompt=True, return_tensors="pt", return_dict=True
    )
    with _lock:  # ponytail: single shared model, one request at a time avoids race on generate()
        output = _model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.7,
            top_p=0.8,
            top_k=20,
            repetition_penalty=1.1,
            pad_token_id=_tokenizer.pad_token_id or _tokenizer.eos_token_id,
        )
    reply_tokens = output[0][inputs["input_ids"].shape[-1]:]
    return _tokenizer.decode(reply_tokens, skip_special_tokens=True).strip()
