"""
Per-patient, per-phase fact extraction from LUMIERE.

Confirmed empirically (2026-08-26, see config/lumiere.py comments) before writing
this module:
  - DeepBraTumIA's "atlas" segmentation outputs are already registered to a
    standard MNI152 1mm grid (182,218,182; affine matches FSL's own
    HarvardOxford atlas images exactly) — no registration step needed here,
    just a voxel-index lookup against FSL's bundled Harvard-Oxford atlas.
  - measured_volumes_in_mm3.json ships precomputed per-timepoint tumor-region
    volumes (Enhancing_Core, Necrotic_NonEnhancing, Edema_Compartment) — label
    IDs 1/2/3 respectively in seg_mask.nii.gz (verified by cross-checking
    voxel counts against the JSON for Patient-001/week-000-1).
  - RANO "Rating" values are PD/SD/PR/CR (response) or Pre-Op/Post-Op
    (baseline surgical state) — only response ratings feed DSCR facts.

One chain per patient: earliest available timepoint (baseline, usually Pre-Op
or Post-Op) vs. the latest real response-rated follow-up (for LIL volume
change + DSCR). PJRF/TCM are patient-level facts (survival, demographics,
templated treatment).

Requires FSL's Harvard-Oxford atlas data (module load fsl) for location
lookup — set FSLDIR before running, or pass an explicit atlas_dir.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import fsspec
import nibabel as nib
import numpy as np
import pandas as pd
import zipfile

import config.lumiere as lcfg
from src.lumiere_downloader import resolve_article

LETTERS = "ABCDE"


#
# Tabular loading
#


def _tabular_dir() -> Path:
    return Path(lcfg.LUMIERE_DATA_DIR) / "tabular"


def load_rano() -> pd.DataFrame:
    df = pd.read_csv(_tabular_dir() / "LUMIERE-ExpertRating-v202211.csv")
    rating_col = [c for c in df.columns if c.startswith("Rating (")][0]
    rationale_col = [c for c in df.columns if c.startswith("Rating rationale")][0]
    df = df.rename(columns={rating_col: "rating_raw", rationale_col: "rationale"})
    df["rating_raw"] = df["rating_raw"].astype(str).str.strip()
    # normalize noise: "Post-Op/PD" -> take the response half if present, else baseline
    df["rating_code"] = df["rating_raw"].apply(_normalize_rating)
    return df


def _normalize_rating(raw) -> str | None:
    raw = str(raw).strip()
    if raw in ("nan", "None", ""):
        return None
    parts = [p.strip() for p in raw.split("/")]
    for p in parts:
        if p in lcfg.RANO_RESPONSE_CODES:
            return p
    for p in parts:
        if p in lcfg.RANO_BASELINE_CODES:
            return p
    return None


def load_demographics() -> pd.DataFrame:
    return pd.read_csv(_tabular_dir() / "LUMIERE-Demographics_Pathology.csv")


def load_completeness() -> pd.DataFrame:
    df = pd.read_csv(_tabular_dir() / "LUMIERE-datacompleteness.csv")
    df["all4"] = (df[["CT1", "T1", "T2", "FLAIR"]] == "x").all(axis=1)
    df["both_seg"] = (df[["DeepBraTumIA", "HD-GLIO-AUTO"]] == "x").all(axis=1)
    return df


#
# Patient selection
#


def select_target_patients(n: int = lcfg.TARGET_N_PATIENTS) -> list[str]:
    """Pick patients with enough genuine multi-timepoint RANO-rated follow-ups
    for a real 5-phase chain — directly targets the construct-validity
    problem this whole effort exists to fix (don't pick patients arbitrarily)."""
    rano = load_rano()
    comp = load_completeness()

    is_response = rano["rating_code"].isin(lcfg.RANO_RESPONSE_CODES.keys())
    response_counts = rano[is_response].groupby("Patient").size()
    eligible = response_counts[response_counts >= lcfg.MIN_RANO_TIMEPOINTS]

    # Prefer patients with full-sequence + both-segmentation coverage at their
    # rated timepoints (avoids picking a patient whose key timepoint is missing data)
    comp_ok = comp[comp["all4"] & comp["both_seg"]].groupby("Patient").size()
    eligible = eligible[eligible.index.isin(comp_ok.index)]

    ranked = eligible.sort_values(ascending=False)
    selected = list(ranked.index[:n])
    print(f"Selected {len(selected)}/{len(eligible)} eligible patients "
          f"(>= {lcfg.MIN_RANO_TIMEPOINTS} response-rated timepoints).")
    return selected


#
# Remote zip access helpers
#


def _zip_url() -> str:
    return resolve_article("imaging")["download_url"]


def _read_member(zf: zipfile.ZipFile, member: str) -> bytes | None:
    try:
        return zf.read(member)
    except KeyError:
        return None


def _load_nifti_bytes(data: bytes):
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".nii.gz", delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    img = nib.load(tmp_path)
    arr = img.get_fdata()
    os.unlink(tmp_path)
    return arr, img.affine


#
# Harvard-Oxford atlas lookup (location facts — no registration needed, see
# module docstring: DeepBraTumIA atlas masks share the exact same grid)
#


_ATLAS_CACHE: dict = {}


def _load_atlas(atlas_dir: Path | None = None):
    if "cort" in _ATLAS_CACHE:
        return _ATLAS_CACHE
    fsldir = atlas_dir or Path(os.environ.get("FSLDIR", "")) / "data" / "atlases"
    cort_img = nib.load(fsldir / "HarvardOxford" / "HarvardOxford-cort-maxprob-thr25-1mm.nii.gz")
    sub_img = nib.load(fsldir / "HarvardOxford" / "HarvardOxford-sub-maxprob-thr25-1mm.nii.gz")
    cort_labels = _parse_atlas_xml(fsldir / "HarvardOxford-Cortical.xml")
    sub_labels = _parse_atlas_xml(fsldir / "HarvardOxford-Subcortical.xml")
    _ATLAS_CACHE.update({
        "cort": cort_img.get_fdata(),
        "sub": sub_img.get_fdata(),
        "cort_labels": cort_labels,
        "sub_labels": sub_labels,
    })
    return _ATLAS_CACHE


def _parse_atlas_xml(path: Path) -> dict[int, str]:
    text = path.read_text(encoding="ISO-8859-1")
    labels = {}
    for m in re.finditer(r'<label index="(\d+)"[^>]*>([^<]+)</label>', text):
        labels[int(m.group(1))] = m.group(2)
    return labels


def _region_at_centroid(mask: np.ndarray, label_id: int, atlas_dir: Path | None = None) -> str | None:
    coords = np.argwhere(mask == label_id)
    if coords.size == 0:
        return None
    cx, cy, cz = coords.mean(axis=0).round().astype(int)
    atlas = _load_atlas(atlas_dir)
    # FSL maxprob atlases: voxel value 0 = unclassified, N = XML index N-1
    cort_val = int(atlas["cort"][cx, cy, cz])
    if cort_val > 0:
        return atlas["cort_labels"].get(cort_val - 1)
    sub_val = int(atlas["sub"][cx, cy, cz])
    if sub_val > 0:
        return atlas["sub_labels"].get(sub_val - 1)
    return None


#
# Per-patient fact extraction
#

SEG_LABELS = {1: "Enhancing_Core", 2: "Necrotic_NonEnhancing", 3: "Edema_Compartment"}


def _patient_timepoints(patient_id: str, comp: pd.DataFrame) -> list[str]:
    rows = comp[(comp["Patient"] == patient_id) & comp["all4"] & comp["both_seg"]]
    return list(rows["Timepoint"])


def _extract_timepoint_imaging_facts(zf: zipfile.ZipFile, patient_id: str, timepoint: str) -> dict | None:
    base = f"{lcfg.ZIP_ROOT}/{patient_id}/{timepoint}"
    vol_bytes = _read_member(zf, f"{base}/{lcfg.DEEPBRATUMIA_VOLUMES_JSON}")
    mask_bytes = _read_member(zf, f"{base}/{lcfg.DEEPBRATUMIA_ATLAS_MASK}")
    if vol_bytes is None or mask_bytes is None:
        return None
    volumes = json.loads(vol_bytes)
    mask, _affine = _load_nifti_bytes(mask_bytes)

    regions = {}
    for label_id, name in SEG_LABELS.items():
        if volumes.get(name, 0) > 0:
            regions[name] = _region_at_centroid(mask, label_id)

    lesion_present = any(v > 0 for v in volumes.values())
    total_volume_mm3 = sum(volumes.values())

    return {
        "timepoint_id": timepoint,
        "lesion_present": lesion_present,
        "volumes_mm3": volumes,
        "total_volume_mm3": total_volume_mm3,
        "regions": regions,
        "source_refs": {
            "volumes_json": f"{base}/{lcfg.DEEPBRATUMIA_VOLUMES_JSON}",
            "mask_file": f"{base}/{lcfg.DEEPBRATUMIA_ATLAS_MASK}",
            "segmentation_source": "DeepBraTumIA (automated, atlas-space)",
        },
    }


def extract_dscr_facts(patient_id: str, rano: pd.DataFrame) -> list[dict]:
    rows = rano[rano["Patient"] == patient_id]
    facts = []
    for _, r in rows.iterrows():
        if r["rating_code"] is None:
            continue
        is_response = r["rating_code"] in lcfg.RANO_RESPONSE_CODES
        facts.append({
            "timepoint_id": r["Date"],
            "rating_code": r["rating_code"],
            "rating_label": (
                lcfg.RANO_RESPONSE_CODES.get(r["rating_code"])
                or lcfg.RANO_BASELINE_CODES.get(r["rating_code"])
            ),
            "is_response_rating": is_response,
            "rationale": None if pd.isna(r["rationale"]) else r["rationale"],
            "source_ref": f"LUMIERE-ExpertRating-v202211.csv row Patient={patient_id} Date={r['Date']}",
        })
    return facts


def _safe_int(value) -> int | None:
    try:
        if pd.isna(value):
            return None
        return int(value)
    except (ValueError, TypeError):
        return None  # non-numeric placeholder, e.g. "na"


def extract_pjrf_facts(patient_id: str, demo: pd.DataFrame) -> dict:
    row = demo[demo["Patient"] == patient_id]
    if row.empty:
        return {}
    r = row.iloc[0]
    return {
        "survival_weeks": _safe_int(r["Survival time (weeks)"]),
        "sex": r["Sex"],
        "age_at_surgery": _safe_int(r["Age at surgery (years)"]),
        "idh_status": r["IDH (WT: wild type)"],
        "mgmt_status": r["MGMT qualitative"],
        "needs_expert_judgment": True,  # distractors need GBM prognostic literature, not LLM-only
        "source_ref": f"LUMIERE-Demographics_Pathology.csv row Patient={patient_id}",
    }


def extract_tcm_facts(patient_id: str, dscr_facts: list[dict]) -> dict:
    had_surgery = any(f["rating_code"] in ("Pre-Op", "Post-Op") for f in dscr_facts)
    progression_events = [f for f in dscr_facts if f["rating_code"] == "PD"]
    return {
        "protocol_assumed": "Stupp protocol (surgical resection + concurrent "
                             "temozolomide-chemoradiation + adjuvant temozolomide) — "
                             "cohort-level assumption from LUMIERE's methods, not a "
                             "per-patient structured field.",
        "surgical_baseline_documented": had_surgery,
        "progression_events_n": len(progression_events),
        "possible_pseudoprogression_flag": len(progression_events) > 0,
        "needs_expert_judgment": True,  # progression-vs-pseudoprogression call needs a radiologist
    }


def build_patient_case_facts(
    patient_id: str,
    rano: pd.DataFrame,
    demo: pd.DataFrame,
    comp: pd.DataFrame,
    zf: zipfile.ZipFile,
    rng: np.random.Generator | None = None,
) -> dict | None:
    dscr_facts = extract_dscr_facts(patient_id, rano)
    response_facts = [f for f in dscr_facts if f["is_response_rating"]]
    if len(response_facts) < lcfg.MIN_RANO_TIMEPOINTS:
        return None

    timepoints = _patient_timepoints(patient_id, comp)
    if not timepoints:
        return None
    baseline_tp = timepoints[0]
    # Pick a RANDOM eligible response-rated timepoint, not always the last —
    # the last rating is overwhelmingly "PD" across this cohort (GBM patients
    # almost always progress before their final scan), which would make every
    # chain's DSCR answer identical and the phase trivially guessable.
    # IMPORTANT: must restrict to response-rated timepoints that ALSO have
    # full imaging available (in `timepoints`) — otherwise the DSCR rating
    # and the LIL imaging facts end up describing two different dates (a
    # real bug caught during the build: an RANO date without full imaging
    # silently fell back to a different imaging timepoint, so the drafted
    # LIL/DSCR facts for the same "chain" contradicted each other).
    imaged_response_facts = [f for f in response_facts if f["timepoint_id"] in timepoints]
    if not imaged_response_facts:
        return None
    rng = rng or np.random.default_rng(42)
    followup_tp = imaged_response_facts[rng.integers(len(imaged_response_facts))]["timepoint_id"]
    followup_imaging_tp = followup_tp

    baseline_imaging = _extract_timepoint_imaging_facts(zf, patient_id, baseline_tp)
    followup_imaging = _extract_timepoint_imaging_facts(zf, patient_id, followup_imaging_tp)
    if baseline_imaging is None or followup_imaging is None:
        return None

    volume_change_pct = None
    if baseline_imaging["total_volume_mm3"] > 0:
        volume_change_pct = round(
            100 * (followup_imaging["total_volume_mm3"] - baseline_imaging["total_volume_mm3"])
            / baseline_imaging["total_volume_mm3"], 1,
        )

    pjrf = extract_pjrf_facts(patient_id, demo)
    tcm = extract_tcm_facts(patient_id, dscr_facts)
    matching_dscr = next((f for f in response_facts if f["timepoint_id"] == followup_tp), response_facts[-1])

    return {
        "patient_id": patient_id,
        "baseline_timepoint": baseline_tp,
        "followup_timepoint": followup_imaging_tp,
        "phase_facts": {
            "AIA": {
                "modalities_available": ["t1", "ct1", "t2", "flair"],
                "segmentation_source": "DeepBraTumIA (automated)",
            },
            "LIL": {
                "baseline": baseline_imaging,
                "followup": followup_imaging,
                "volume_change_pct": volume_change_pct,
            },
            "DSCR": matching_dscr,
            "PJRF": pjrf,
            "TCM": tcm,
        },
        "all_dscr_facts": dscr_facts,
    }


#
# Slice-PNG rendering — bridges LUMIERE's 3D NIfTI to the evaluator's 2D-PNG
# image loading (src/data_loader.load_image_bytes expects a flat image file,
# not a volume). Picks the axial slice with max tumor-mask area.
#


def _render_axial_slice_png(anatomical: np.ndarray, mask: np.ndarray, out_path: Path) -> Path:
    from PIL import Image

    areas = (mask > 0).sum(axis=(0, 1))
    z = int(np.argmax(areas)) if areas.max() > 0 else anatomical.shape[2] // 2
    sl = anatomical[:, :, z]
    sl = np.rot90(sl)
    lo, hi = np.percentile(sl, 1), np.percentile(sl, 99)
    sl = np.clip((sl - lo) / max(hi - lo, 1e-6), 0, 1) * 255
    out_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(sl.astype(np.uint8), mode="L").save(out_path)
    return out_path


def render_slices_for_patient(patient_id: str, facts: dict, out_dir: Path | None = None) -> dict[str, str]:
    """Renders one representative slice PNG per timepoint (baseline + followup)
    for a patient already extracted by build_patient_case_facts(). Returns
    {timepoint_id: relative_png_path}."""
    out_dir = out_dir or Path(lcfg.LUMIERE_DATA_DIR) / "slices" / patient_id
    lil = facts["phase_facts"]["LIL"]
    result = {}
    with fsspec.open(_zip_url(), mode="rb") as f:
        with zipfile.ZipFile(f) as zf:
            for key in ("baseline", "followup"):
                tp = lil[key]["timepoint_id"]
                base = f"{lcfg.ZIP_ROOT}/{patient_id}/{tp}"
                ct1_bytes = _read_member(zf, f"{base}/{lcfg.DEEPBRATUMIA_ATLAS_CT1}")
                mask_bytes = _read_member(zf, f"{base}/{lcfg.DEEPBRATUMIA_ATLAS_MASK}")
                if ct1_bytes is None or mask_bytes is None:
                    continue
                anatomical, _ = _load_nifti_bytes(ct1_bytes)
                mask, _ = _load_nifti_bytes(mask_bytes)
                out_path = out_dir / f"{tp}.png"
                _render_axial_slice_png(anatomical, mask, out_path)
                result[tp] = str(out_path)
                print(f"  rendered {out_path}")
    return result


def render_all_slices(facts_dir: Path | None = None, force: bool = False) -> None:
    facts_dir = facts_dir or Path(lcfg.LUMIERE_DATA_DIR) / "facts"
    slices_root = Path(lcfg.LUMIERE_DATA_DIR) / "slices"
    for fpath in sorted(facts_dir.glob("Patient-*.json")):
        facts = json.loads(fpath.read_text())
        pid = facts["patient_id"]
        lil = facts["phase_facts"]["LIL"]
        expected = [lil["baseline"]["timepoint_id"], lil["followup"]["timepoint_id"]]
        already_done = all((slices_root / pid / f"{tp}.png").exists() for tp in expected)
        if already_done and not force:
            print(f"  [skip] slices already rendered for {pid}")
            continue
        print(f"Rendering slices for {pid}…")
        render_slices_for_patient(pid, facts)


def extract_all(patient_ids: list[str], out_dir: Path | None = None, force: bool = False) -> list[dict]:
    out_dir = out_dir or Path(lcfg.LUMIERE_DATA_DIR) / "facts"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Skip patients already extracted — avoids redundant network/NIfTI work when
    # re-running against an expanded patient list (see plan: idempotency fix).
    to_process = []
    results = []
    for pid in patient_ids:
        out_path = out_dir / f"{pid}.json"
        if out_path.exists() and not force:
            print(f"  [skip] facts already exist for {pid}")
            results.append(json.loads(out_path.read_text()))
        else:
            to_process.append(pid)

    if not to_process:
        return results

    rano, demo, comp = load_rano(), load_demographics(), load_completeness()
    rng = np.random.default_rng(42)
    with fsspec.open(_zip_url(), mode="rb") as f:
        with zipfile.ZipFile(f) as zf:
            for pid in to_process:
                print(f"Extracting facts for {pid}…")
                facts = build_patient_case_facts(pid, rano, demo, comp, zf, rng=rng)
                if facts is None:
                    print(f"  [skip] insufficient data for {pid}")
                    continue
                out_path = out_dir / f"{pid}.json"
                out_path.write_text(json.dumps(facts, indent=2, default=str))
                print(f"  -> {out_path}")
                results.append(facts)
    return results


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="LUMIERE per-patient fact extraction")
    p.add_argument("--select", action="store_true", help="print selected target patients and exit")
    p.add_argument("--n", type=int, default=lcfg.TARGET_N_PATIENTS)
    p.add_argument("--patients", type=str, default=None, help="comma-separated patient IDs (overrides --select)")
    p.add_argument("--force", action="store_true", help="re-extract/re-render even if output already exists")
    p.add_argument("--render-slices", action="store_true", help="also render slice PNGs after extraction")
    args = p.parse_args()

    if args.patients:
        ids = args.patients.split(",")
    else:
        ids = select_target_patients(n=args.n)

    if args.select:
        print(ids)
    else:
        extract_all(ids, force=args.force)
        if args.render_slices:
            render_all_slices(force=args.force)
