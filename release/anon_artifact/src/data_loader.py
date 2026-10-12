"""
Downloads OmniBrainBench from HuggingFace and constructs multi-phase cases.

Download targets (from FrankPN/OmniBrainBench):
  closed-ended-qa_6823.json   4.98 MB  — metadata + phase labels
  closed-ended-qa_6823.zip    734 MB   — images

Dataset structure (discovered empirically):
  - 6,823 QA pairs across 15 source files
  - source_file is the correct grouping key for causal chains
    (image_path is per-question; most images appear in only one phase)
  - 10 source files span 2+ phases; 2 span all 5 phases
  - Phase distribution: AIA:2048, LIL:2797, DSCR:1845, PJRF:64, TCM:51
  - Each question has its own image_path (images are per-question, not per-case)

Case format returned is compatible with CausalChainEvaluator.
Images are loaded lazily per-question at eval time (not all at once).
"""

from __future__ import annotations

import io
import json
import random
import zipfile
from pathlib import Path

from PIL import Image

import config
from src.phase_map import PHASE_MAP, TASK_GROUNDING_TERMS

LETTERS = "ABCDE"


#
# Download helpers
#


def _data_dir() -> Path:
    return Path(__file__).parent / config.DATA_CACHE_DIR


def download_dataset(force: bool = False) -> tuple[Path, Path]:
    """
    Download JSON metadata and image zip from HuggingFace if not cached.
    Returns (json_path, image_dir).
    """
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        raise ImportError("Run: pip install huggingface_hub")

    data_dir = _data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)

    json_path = data_dir / config.JSON_FILENAME
    zip_path = data_dir / config.ZIP_FILENAME
    image_dir = data_dir / config.IMAGES_SUBDIR

    # --- JSON metadata ---
    if not json_path.exists() or force:
        print(f"Downloading {config.JSON_FILENAME} (4.98 MB)…")
        hf_hub_download(
            repo_id=config.HF_DATASET_ID,
            filename=config.JSON_FILENAME,
            repo_type="dataset",
            local_dir=str(data_dir),
        )
        print(f"  → {json_path}")
    else:
        print(f"  JSON cached: {json_path}")

    # --- Images zip ---
    if not image_dir.exists() or force:
        if not zip_path.exists() or force:
            print(f"Downloading {config.ZIP_FILENAME} (734 MB)…")
            hf_hub_download(
                repo_id=config.HF_DATASET_ID,
                filename=config.ZIP_FILENAME,
                repo_type="dataset",
                local_dir=str(data_dir),
            )
        print(f"Extracting images from {zip_path.name}…")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(data_dir)
        if not image_dir.exists():
            _fix_image_dir(data_dir, image_dir)
        print(f"  → {image_dir}")
    else:
        print(f"  Images cached: {image_dir}")

    return json_path, image_dir


def _fix_image_dir(data_dir: Path, target: Path):
    """After extraction, locate image files and move to target/."""
    candidates = [
        p
        for p in data_dir.iterdir()
        if p.is_dir() and p.name not in (config.IMAGES_SUBDIR, "__MACOSX")
    ]
    if candidates:
        candidates[0].rename(target)
    else:
        target.mkdir(exist_ok=True)
        exts = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
        for f in data_dir.iterdir():
            if f.suffix.lower() in exts:
                f.rename(target / f.name)


#
# Image loading
#


def _find_image(filename: str, image_dir: Path) -> Path | None:
    """Locate image file inside image_dir, searching recursively."""
    direct = image_dir / filename
    if direct.exists():
        return direct
    name = Path(filename).name
    for hit in image_dir.rglob(name):
        return hit
    return None


def load_image_bytes(image_path: str, image_dir: Path) -> bytes | None:
    """
    Load, resize, and return a single image as PNG bytes.
    Returns None if not found or unreadable.
    """
    path = _find_image(image_path, image_dir)
    if path is None:
        return None
    try:
        with Image.open(path) as img:
            max_d = config.MAX_IMAGE_DIM
            if max(img.size) > max_d:
                ratio = max_d / max(img.size)
                new_w, new_h = int(img.width * ratio), int(img.height * ratio)
                img = img.resize((new_w, new_h), Image.LANCZOS)
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()
    except Exception as e:
        print(f"  [warn] image load failed ({image_path}): {e}")
        return None


def load_image_bytes_list(image_path: str | list[str], image_dir: Path) -> list[bytes]:
    """
    Handle image_path as either a string or a list (OmniBrainBench allows both).
    Returns a list of PNG bytes — one entry per image, skipping any that fail.
    """
    paths = image_path if isinstance(image_path, list) else [image_path]
    result = []
    for p in paths:
        b = load_image_bytes(str(p), image_dir)
        if b is not None:
            result.append(b)
    return result


#
# Case construction helpers
#


def _options_to_dict(options: list[str]) -> dict[str, str]:
    return {LETTERS[i]: opt for i, opt in enumerate(options[:5])}


def _grounding_terms(task_label: str, modality_type: list[str]) -> list[str]:
    terms = list(TASK_GROUNDING_TERMS.get(task_label, []))
    terms += [m.lower() for m in modality_type if m]
    return list(dict.fromkeys(terms))  # dedup, preserve order


#
# Main builder
#


def build_cases(
    json_path: Path,
    image_dir: Path,
    n_cases: int | None = None,
    min_phases: int = 2,
    max_q_per_phase: int = 5,
    modality_filter: list[str] | None = None,
    seed: int = 42,
) -> list[dict]:
    """
    Group OmniBrainBench questions by source_file into multi-phase cases.

    Key insight: source_file is the correct grouping key for causal chains.
    Each source file represents a clinical dataset whose questions span
    multiple reasoning phases. image_path is per-question (not per-case).

    Args:
        json_path:        Path to closed-ended-qa_6823.json
        image_dir:        Directory containing extracted images
        n_cases:          Max cases to return (None = all)
        min_phases:       Min number of distinct phases required per case
        max_q_per_phase:  Max questions sampled per phase (caps large sources
                          like PubMedVision which has 1,079 questions)
        modality_filter:  Only include cases whose modality_type intersects this list
        seed:             Random seed for sampling

    Returns:
        List of case dicts compatible with CausalChainEvaluator.
        Each question stores its own _image_path for lazy per-question loading.
    """
    random.seed(seed)

    with open(json_path, encoding="utf-8") as f:
        rows = json.load(f)

    # Group by source_file — the natural clinical case boundary
    groups: dict[str, list[dict]] = {}
    for row in rows:
        sf = row.get("source_file", "unknown")
        groups.setdefault(sf, []).append(row)

    cases: list[dict] = []

    for source_file, questions in groups.items():

        # Map clinical_phase → abbreviation; drop unknowns
        phase_buckets: dict[str, list[dict]] = {}
        for q in questions:
            abbr = PHASE_MAP.get(q.get("clinical_phase", ""))
            if abbr:
                phase_buckets.setdefault(abbr, []).append(q)

        if len(phase_buckets) < min_phases:
            continue

        # Optional modality filter
        if modality_filter:
            all_mods = {m for q in questions for m in q.get("modality_type", [])}
            if not all_mods.intersection(modality_filter):
                continue

        # Representative metadata from first question
        first = questions[0]
        modality = (first.get("modality_type") or ["unknown"])[0]
        # Dataset name from source file (e.g. "MedXpert" from "MedXpert_brain_QA_32.json")
        dataset_name = source_file.split("_")[0]

        # Build phases dict — each question carries its own image reference
        phases_dict: dict[str, list[dict]] = {}
        for phase_abbr in config.PHASES:
            bucket = phase_buckets.get(phase_abbr)
            if not bucket:
                continue

            # Sample up to max_q_per_phase questions (shuffle for fairness)
            sampled = random.sample(bucket, min(len(bucket), max_q_per_phase))

            phase_qs = []
            for i, q in enumerate(sampled):
                opts = _options_to_dict(q["options"])
                answer = q["answer"].upper()
                task = q.get("task_label", "")
                mods = q.get("modality_type", [])
                phase_qs.append(
                    {
                        "id": f"{dataset_name}_{phase_abbr}_Q{i}",
                        "question": q["question"],
                        "options": opts,
                        "correct_answer": answer,
                        "correct_answer_text": opts.get(answer, ""),
                        "task_label": task,
                        "grounding_terms": _grounding_terms(task, mods),
                        "chain_grounding_terms": [],  # populated dynamically in evaluator
                        # Per-question image — each question has its own scan
                        "_image_path": q.get("image_path", ""),
                        "_image_dir": image_dir,
                    }
                )
            phases_dict[phase_abbr] = phase_qs

        cases.append(
            {
                "id": source_file,
                "title": f"Brain Imaging Case ({dataset_name})",
                "modality": modality,
                "source_file": source_file,
                "_image_dir": image_dir,
                "image_bytes": None,  # not used — images loaded per-question
                "image_bytes_list": None,
                "phases": phases_dict,
            }
        )

    random.shuffle(cases)
    if n_cases:
        cases = cases[:n_cases]

    phase_counts = {p: sum(1 for c in cases if p in c["phases"]) for p in config.PHASES}
    q_counts = {
        p: sum(len(c["phases"].get(p, [])) for c in cases) for p in config.PHASES
    }
    print(
        f"Built {len(cases)} cases | phase coverage: "
        + " | ".join(
            f"{p}:{phase_counts[p]}cases/{q_counts[p]}Qs"
            for p in config.PHASES
            if phase_counts[p] > 0
        )
    )
    return cases


#
# Top-level entry point
#


def load_omnibrain(
    n_cases: int | None = None,
    min_phases: int = 2,
    max_q_per_phase: int = 5,
    force_download: bool = False,
    **kwargs,
) -> list[dict]:
    """Download (if needed) and return cases ready for CausalChainEvaluator."""
    json_path, image_dir = download_dataset(force=force_download)
    return build_cases(
        json_path,
        image_dir,
        n_cases=n_cases,
        min_phases=min_phases,
        max_q_per_phase=max_q_per_phase,
        **kwargs,
    )
