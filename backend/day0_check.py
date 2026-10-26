"""Baseer Day-0 live checks — SAM availability + Spark vs Wonder Arabic A/B.

Run on the machine that holds the key (the key never leaves that machine,
and this script never prints it):

    cp .env.example .env   # from the repo root, then fill MODEL_API_KEY
    cd backend && python day0_check.py

What it does:
  1. SAM probe — 1 synthetic frame x 1 concept ("person"). The frame
     content does not matter; only the status matters:
       200  -> SAM 3.1 ENABLED for this team/key
       404  -> SAM 3.1 GATED (model_not_found) — Muse stays central
       other -> error, status + body snippet printed
  2. Arabic A/B — the SAME mock segments + Arabic inspector note are sent
     to muse-spark-1.3 and muse-wonder-1.0. Both full reports, token usage
     and rough cost per report are printed. Paste the whole output back
     to Muse; the Arabic-quality call is made there.

Exit codes: 0 = checks ran (a GATED SAM result is a verdict, not a
failure); 2 = no API key found.
"""

from __future__ import annotations

import base64
import io
import json
import os
import sys

import httpx

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

BASE_URL = os.getenv("META_API_BASE_URL", "https://api.meta.ai/v1")
SAM_MODEL = os.getenv("SAM_MODEL", "sam-3.1")

# Standard-tier prices, USD per 1M tokens (cached/input/output order in
# the picker; cached tokens ignored here, so costs are slight overestimates).
PRICES = {
    "muse-spark-1.3": (1.25, 4.25),
    "muse-wonder-1.0": (4.00, 20.00),
}

INSPECTOR_NOTE_AR = (
    "أثناء الجولة لاحظت عاملا بدون خوذة حماية يعمل بالقرب من رافعة شوكية "
    "متحركة، والحافة العلوية لمنصة العمل بدون حاجز حماية، ومسار الرافعة "
    "غير محدد بعلامات أرضية."
)
SITE_CONTEXT = "factory (industrial)"


def load_dotenv() -> None:
    """Load KEY=VALUE lines from .env (backend/ then repo root) without
    overwriting real environment variables. No values are printed."""
    for candidate in (os.path.join(HERE, ".env"),
                      os.path.join(os.path.dirname(HERE), ".env")):
        if not os.path.exists(candidate):
            continue
        with open(candidate, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key, value = key.strip(), value.strip().strip("\"'")
                if key and key not in os.environ:
                    os.environ[key] = value
        return


def api_key() -> str:
    return os.getenv("MODEL_API_KEY", "") or os.getenv("META_API_KEY", "")


def headers() -> dict:
    return {"Authorization": f"Bearer {api_key()}", "Content-Type": "application/json"}


def make_probe_image() -> bytes:
    """A synthetic 640x480 JPEG. SAM only needs an image to answer; the
    verdict is the HTTP status, not what it finds in this frame."""
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (640, 480), (200, 200, 190))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 320, 640, 480], fill=(120, 120, 115))  # floor
    draw.rectangle([250, 150, 330, 330], fill=(30, 90, 160))  # standing figure
    draw.ellipse([270, 100, 310, 150], fill=(220, 180, 140))  # head, no helmet
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def sam_probe() -> dict:
    """Returns {'status': 'ENABLED'|'GATED'|'ERROR', 'detail': str}."""
    import meta_client

    image_url = "data:image/jpeg;base64," + base64.b64encode(make_probe_image()).decode()
    payload = {
        "model": SAM_MODEL,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": image_url}},
                {"type": "text", "text": "person"},
            ],
        }],
    }
    try:
        with httpx.Client(timeout=180) as client:
            resp = client.post(f"{BASE_URL}/chat/completions",
                               json=payload, headers=headers())
    except Exception as exc:  # network-level failure
        return {"status": "ERROR", "detail": f"request failed: {exc}"}
    if resp.status_code == 404:
        return {"status": "GATED",
                "detail": "404 model_not_found — SAM 3.1 is not enabled for this team/key."}
    if resp.status_code != 200:
        return {"status": "ERROR",
                "detail": f"HTTP {resp.status_code}: {resp.text[:300]}"}
    text = resp.json()["choices"][0]["message"]["content"]
    boxes = meta_client.parse_sam_output(text, "person", 0)
    return {"status": "ENABLED",
            "detail": f"SAM answered. Parsed {len(boxes)} box(es) for 'person'. "
                      f"Raw output (first 300 chars): {text[:300]!r}"}


def reason_with_model(model: str) -> dict:
    """One reasoning call with an explicit model. Mirrors
    meta_client.reason_findings but parameterized for the A/B test."""
    import meta_client
    import prompts

    if model.endswith("-contributor"):
        raise RuntimeError(f"Refusing Contributor-tier model: {model}")
    segments = meta_client._mock_segments(1)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": prompts.SYSTEM_PROMPT},
            {"role": "user", "content": prompts.build_user_prompt(
                segments, INSPECTOR_NOTE_AR, SITE_CONTEXT)},
        ],
        "response_format": {"type": "json_object"},
    }
    with httpx.Client(timeout=180) as client:
        resp = client.post(f"{BASE_URL}/chat/completions",
                           json=payload, headers=headers())
        resp.raise_for_status()
        data = resp.json()
    parsed = json.loads(data["choices"][0]["message"]["content"])
    usage = data.get("usage", {})
    in_tok = usage.get("prompt_tokens", 0)
    out_tok = usage.get("completion_tokens", 0)
    price_in, price_out = PRICES[model]
    cost = in_tok * price_in / 1_000_000 + out_tok * price_out / 1_000_000
    return {"model": model, "parsed": parsed, "usage": usage,
            "cost_usd": cost}


def print_report(result: dict) -> None:
    parsed = result["parsed"]
    print(f"--- {result['model']} ---")
    print(f"tokens in/out: {result['usage'].get('prompt_tokens')} / "
          f"{result['usage'].get('completion_tokens')}  |  "
          f"rough cost/report: ${result['cost_usd']:.4f}")
    print(f"summary_ar: {parsed.get('summary_ar', '')}")
    print(f"summary_en: {parsed.get('summary_en', '')}")
    for i, f in enumerate(parsed.get("findings", []), 1):
        print(f"  [{i}] {f.get('severity', '?')} | "
              f"{f.get('title_ar', '')} / {f.get('title_en', '')}")
        print(f"      action_ar: {f.get('action_ar', '')}")


def main() -> int:
    load_dotenv()
    if not api_key():
        print("No API key found.")
        print("  1. Copy .env.example to .env in the repo root.")
        print("  2. Set MODEL_API_KEY to your dev.meta.ai key.")
        print("  3. Re-run: cd backend && python day0_check.py")
        return 2

    print("== Check 1: SAM 3.1 availability ==")
    sam = sam_probe()
    print(f"SAM status: {sam['status']}")
    print(sam["detail"])
    print()

    print("== Check 2: Arabic A/B — Spark 1.3 vs Wonder 1.0 ==")
    print(f"Inspector note (same for both): {INSPECTOR_NOTE_AR}")
    print()
    for model in ("muse-spark-1.3", "muse-wonder-1.0"):
        try:
            print_report(reason_with_model(model))
        except Exception as exc:
            print(f"--- {model} --- FAILED: {exc}")
        print()

    print("== Paste this whole output back to Muse ==")
    print(f"SAM verdict: {sam['status']}. The Arabic-quality call (which "
          "model writes the final reports) is made from the two reports above.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
