"""
Input-handling check for one serving pipeline (paper/review.md concern 7; added 2026-09-25 after the runs). GPU node only:
the script talks to a model server (Ollama or vLLM) that must already be running, exactly as run_lumiere_v4.py does.

It answers, for the pipeline that produced the v4 results, three questions that the accuracy tables cannot:

  1. Serving record      exact model tag/digest/quantization/template (Ollama `show`) or /v1/models (vLLM), server version.
  2. Do all images reach the model?   For one real AIA, LIL and DSCR item (DSCR shows two or three images; a three-image item is used), the prompt token count
                         with 0, 1, ..., k of the item's real images, built by the same code as the runs (build_main_prompt).
                         The increment per image should be roughly constant and clearly above the text-only count; a zero
                         increment would mean the image was dropped. A unique nonce starts every prompt so a server-side
                         prefix cache cannot hide tokens.
  3. Can the pipeline see?   Known-answer probes sent through the same message format: solid colours, a printed number,
                         three colour images in order (multi-image ordering), and a real skull-stripped slice (black
                         background). Answers are free text and are scored by simple string match.

Also saves the exact images sent, and a montage of what a 448- and 896-pixel square encoder input looks like for one slice.

  python -m tools.lumiere_v4_input_check --model Gemma-3-12B            # after `ollama serve` is up (see the sbatch)
  python -m tools.lumiere_v4_input_check --model Gemma-3-12B --dry-run  # offline: builds every message, no server

Writes results/lumiere_v4_inputcheck_<model>_<timestamp>/{report.json,report.md,montage.png,images/}.
"""

from __future__ import annotations

import argparse
import datetime
import io
import json
import uuid
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import config
from config.models import MODEL_MAP
from src.evaluator import _load_question_image
from src.lumiere_loader import load_lumiere
from src.prompts import _build_user_content, build_main_prompt


def png_bytes(im: Image.Image) -> bytes:
    b = io.BytesIO()
    im.save(b, format="PNG")
    return b.getvalue()


def color_img(rgb, size=(728, 872)) -> bytes:
    return png_bytes(Image.new("RGB", size, rgb))


def number_img(text: str, size=(728, 872)) -> bytes:
    im = Image.new("RGB", size, (255, 255, 255))
    d = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 280)
    except OSError:
        font = ImageFont.load_default()
    d.text((size[0] // 2, size[1] // 2), text, fill=(0, 0, 0), font=font, anchor="mm")
    return png_bytes(im)


class Fake:
    """Offline stand-in that returns a token count proportional to the payload, so the message building can be tested."""

    class _C:
        class completions:
            @staticmethod
            def create(model, messages, max_tokens, temperature, **kw):
                n = 0
                for m in messages:
                    c = m["content"]
                    n += len(c) // 4 if isinstance(c, str) else sum(256 if p["type"] == "image_url" else len(p["text"]) // 4 for p in c)

                class R:
                    usage = type("U", (), {"prompt_tokens": n, "total_tokens": n})()
                    choices = [type("Ch", (), {"message": type("M", (), {"content": "dry-run"})()})()]
                return R()

    chat = _C()


def ask(client, model, messages, max_tokens=24):
    """One call; returns (prompt_tokens, text). A nonce heads the system prompt so no prefix cache can reuse tokens."""
    messages = [dict(m) for m in messages]
    sys_i = next(i for i, m in enumerate(messages) if m["role"] == "system") if any(m["role"] == "system" for m in messages) else None
    tag = f"[probe {uuid.uuid4().hex}] "
    if sys_i is None:
        messages.insert(0, {"role": "system", "content": tag})
    else:
        messages[sys_i]["content"] = tag + messages[sys_i]["content"]
    r = client.chat.completions.create(model=model, messages=messages, max_tokens=max_tokens, temperature=0.0)
    u = getattr(r, "usage", None)
    return (getattr(u, "prompt_tokens", None) if u else None), (r.choices[0].message.content or "").strip()


def _http(url: str, payload: dict | None = None, timeout: int = 120) -> dict:
    import urllib.request
    req = urllib.request.Request(url, data=json.dumps(payload).encode() if payload is not None else None,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def serving_record(cfg: dict) -> dict:
    """Exact model identity. The `ollama` CLI is a module wrapper that is not on the subprocess PATH, so the server's HTTP API is used."""
    rec = {"model_name": cfg["name"], "model_tag": cfg["model"], "backend": cfg.get("backend"), "base_url": cfg.get("base_url")}
    root = (cfg.get("base_url") or "").rsplit("/v1", 1)[0]
    try:
        if cfg.get("backend") == "ollama":
            rec["ollama_version"] = _http(root + "/api/version").get("version")
            tags = _http(root + "/api/tags").get("models", [])
            rec["listing"] = next((m for m in tags if m.get("name") == cfg["model"] or m.get("model") == cfg["model"]), None)
            show = _http(root + "/api/show", {"model": cfg["model"]})
            rec["details"] = show.get("details")
            rec["template"] = show.get("template")
            rec["parameters"] = show.get("parameters")
            rec["capabilities"] = show.get("capabilities")
            mi = show.get("model_info") or {}
            rec["model_info"] = {k: v for k, v in mi.items() if not isinstance(v, list) or len(v) < 20}
        else:
            rec["v1_models"] = _http(cfg["base_url"] + "/models")
    except Exception as e:                                        # noqa: BLE001 - record the failure, keep going
        rec["error"] = str(e)
    return rec


def real_items(item_set="v4"):
    cases = load_lumiere(n_cases=None, min_phases=2, include_unreviewed=True, item_set=item_set)
    for c in cases:                                               # first patient with AIA, LIL and a three-image DSCR item
        if all(c["phases"].get(p) for p in ("AIA", "LIL", "DSCR")) and len(_load_question_image(c["phases"]["DSCR"][0])) == 3:
            return c
    raise SystemExit("no patient with AIA, LIL and a three-image DSCR item")


def token_increments(client, model, case, out_dir: Path) -> dict:
    res = {"patient": case["id"], "phases": {}}
    (out_dir / "images").mkdir(exist_ok=True)
    for ph in ("AIA", "LIL", "DSCR"):
        q = case["phases"][ph][0]
        imgs = _load_question_image(q)
        for i, b in enumerate(imgs):
            (out_dir / "images" / f"{case['id']}_{ph}_{i + 1}.png").write_bytes(b)
        dims = [Image.open(io.BytesIO(b)).size for b in imgs]

        def prompt(k):
            c = {**case, "image_bytes_list": imgs[:k], "image_bytes": imgs[0] if k else None,
                 "image_labels": q.get("_image_labels") if k == len(imgs) else None,
                 "image_note": q.get("_image_note") if k else None}
            return build_main_prompt(q, c, ph, [])

        counts = {}
        for k in range(len(imgs) + 1):
            counts[k], _ = ask(client, model, prompt(k), max_tokens=1)
        inc = [None if counts[k] is None or counts[k - 1] is None else counts[k] - counts[k - 1] for k in range(1, len(imgs) + 1)]
        res["phases"][ph] = {"question_id": q["id"], "n_images": len(imgs), "image_sizes": dims,
                             "prompt_tokens_by_n_images": counts, "increment_per_added_image": inc,
                             "text_only_tokens": counts[0]}
    return res


def perception_probes(client, model, case, out_dir: Path) -> list[dict]:
    probes = []
    red, green, blue = (220, 30, 30), (30, 170, 30), (30, 30, 220)

    def one(name, imgs, question, expect, labels=None):
        content = _build_user_content(question, imgs, labels)
        _, text = ask(client, model, [{"role": "user", "content": content}], max_tokens=48)
        low = text.lower()
        ok = all(e.lower() in low for e in expect)
        if len(expect) > 1:                                        # ordered list: each colour must appear in the given order
            pos = [low.find(e.lower()) for e in expect]
            ok = ok and pos == sorted(pos)
        probes.append({"probe": name, "expected": expect, "answer": text, "pass": bool(ok)})

    for nm, col in (("red", red), ("green", green), ("blue", blue)):
        one(f"colour_{nm}", [color_img(col)], "What is the dominant colour of this image? Answer with one word.", [nm])
    for num in ("742", "1905"):
        one(f"number_{num}", [number_img(num)], "What number is printed in this image? Answer with the number only.", [num])
    one("three_images_order", [color_img(red), color_img(green), color_img(blue)],
        "Three images are shown. Give the dominant colour of image 1, image 2 and image 3, in order, as a comma-separated list of one word each.",
        ["red", "green", "blue"], labels=["first", "second", "third"])
    one("two_images_second", [color_img(red), color_img(blue)],
        "Two images are shown. What is the dominant colour of the SECOND image? Answer with one word.", ["blue"])
    q = case["phases"]["AIA"][0]
    real = _load_question_image(q)
    one("real_slice_background", real[:1],
        "This is a brain MRI slice. Is the background outside the head black or white? Answer with one word.", ["black"])
    return probes


def montage(case, out: Path) -> None:
    q = case["phases"]["AIA"][0]
    src = Image.open(io.BytesIO(_load_question_image(q)[0])).convert("RGB")
    tiles = [("as sent", src.size), ("896x896 squashed", (896, 896)), ("448x448 squashed", (448, 448))]
    canvas = Image.new("RGB", (sum(min(w, 900) for _, (w, _) in tiles) + 30, 900), (40, 40, 40))
    x = 10
    d = ImageDraw.Draw(canvas)
    for name, size in tiles:
        im = src.resize(size, Image.BICUBIC) if size != src.size else src
        canvas.paste(im, (x, 30))
        d.text((x, 5), f"{name} {size[0]}x{size[1]}", fill=(255, 255, 255))
        x += im.size[0] + 10
    canvas.save(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    cfg = MODEL_MAP[args.model]
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path("results") / f"lumiere_v4_inputcheck_{cfg['name']}{'_dry' if args.dry_run else ''}_{ts}"
    out.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        client = Fake()
    else:
        from openai import OpenAI
        client = OpenAI(base_url=cfg["base_url"], api_key=cfg.get("api_key") or "local")
    case = real_items()
    report = {"serving": serving_record(cfg) if not args.dry_run else {"dry_run": True}, "max_tokens_in_runs": config.MAX_TOKENS,
              "tokens": token_increments(client, cfg["model"], case, out),
              "probes": perception_probes(client, cfg["model"], case, out)}
    montage(case, out / "montage.png")
    (out / "report.json").write_text(json.dumps(report, indent=2, default=str))
    md = [f"# Input check: {cfg['name']} ({cfg['model']})", "", "## Do all images reach the model? (prompt tokens; real v4 items)", "",
          "| phase | images | image size | text only | tokens by images added | increment per added image |", "|---|---|---|---|---|---|"]
    for ph, v in report["tokens"]["phases"].items():
        md.append(f"| {ph} | {v['n_images']} | {v['image_sizes'][0]} | {v['text_only_tokens']} | {v['prompt_tokens_by_n_images']} | {v['increment_per_added_image']} |")
    md += ["", "## Perception probes (same message format)", "", "| probe | expected | answer | pass |", "|---|---|---|---|"]
    for p in report["probes"]:
        md.append(f"| {p['probe']} | {', '.join(p['expected'])} | {p['answer'][:60].replace(chr(10), ' ')} | {'yes' if p['pass'] else 'NO'} |")
    passed = sum(p["pass"] for p in report["probes"])
    md += ["", f"{passed} of {len(report['probes'])} probes passed."]
    (out / "report.md").write_text("\n".join(md))
    print("\n".join(md))
    print(f"\nSaved -> {out}")


if __name__ == "__main__":
    main()
