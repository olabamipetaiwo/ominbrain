"""
Slice-level measurements from LUMIERE's DeepBraTumIA atlas-space masks (v4 item set).

Why this exists (paper/review.md, concern 1: answerability). The v3 LIL/DSCR answer keys were
whole-volume quantities or expert ratings that the single displayed slice cannot determine. For v4
every visual answer key is a deterministic function of the pixels that are actually displayed:

  * slice choice     z_e = axial slice with the largest enhancing-core area (label 1);
                     z_l = axial slice with the largest tumour-core area (labels 1|2).
  * RANO-style size  bidimensional product (BP, mm^2) of the largest enhancing component on z_e
                     (longest in-plane diameter x longest perpendicular diameter; atlas voxels are 1 mm),
                     the same 2D quantity the RANO criteria use (the expert rationale in the LUMIERE
                     table quotes such measurements, e.g. "28mm x 44mm").
  * localisation     hemisphere and anterior/posterior half of the largest tumour-core component on z_l,
                     relative to the brain mask's own extent on that slice.

The masks are automated (DeepBraTumIA), not manual; the keys are therefore "as measured on the
automated segmentation of the displayed slice", which is stated in the paper.

Orientation: DeepBraTumIA atlas outputs share the MNI152 1 mm grid. Which array index points to the
patient's left/anterior is read from the affine, not assumed. The renderer (src/lumiere_v4_render.py)
uses the same convention: image column = array axis 0, image row = array axis 1 reversed, so the
patient's right is on the LEFT of the image (radiological display) and anterior is up.
"""

from __future__ import annotations

import json
from pathlib import Path

import nibabel as nib
import numpy as np
from scipy import ndimage
from scipy.spatial import ConvexHull

import config.lumiere as lcfg

ENH, NEC, EDEMA = 1, 2, 3  # DeepBraTumIA label ids (Enhancing_Core, Necrotic_NonEnhancing, Edema)
MEASURABLE_BP_MM2 = 100.0  # RANO: measurable enhancing disease is at least 10 mm x 10 mm
MIN_LESION_PX = 100        # LIL: smallest tumour-core component (mm^2) that is asked about
MIDLINE_MARGIN_PX = 10     # LIL: lesions whose centroid is closer than this (mm) to a midline are dropped
SIDE_FRACTION_MIN = 0.8    # LIL: share of the component's pixels on the centroid's side of the midline
MEASURE_VERSION = 1


def _largest_component(slice_mask: np.ndarray) -> np.ndarray:
    lab, n = ndimage.label(slice_mask, structure=np.ones((3, 3)))
    if n == 0:
        return np.zeros_like(slice_mask, dtype=bool)
    sizes = ndimage.sum(slice_mask, lab, index=range(1, n + 1))
    return lab == (1 + int(np.argmax(sizes)))


def bidimensional_product(component: np.ndarray) -> tuple[float, float, float]:
    """(longest diameter, longest perpendicular diameter, product) in mm for a 2D boolean component.

    Voxel centres are 1 mm apart, and each voxel covers 1 mm, so extents add 1."""
    pts = np.argwhere(component).astype(float)
    if len(pts) == 0:
        return 0.0, 0.0, 0.0
    if len(pts) < 3:
        return 1.0, 1.0, 1.0
    try:
        hull = pts[ConvexHull(pts).vertices]
    except Exception:  # collinear points
        hull = pts
    diff = hull[:, None, :] - hull[None, :, :]
    dist = np.sqrt((diff ** 2).sum(-1))
    i, j = np.unravel_index(int(np.argmax(dist)), dist.shape)
    d1 = float(dist[i, j]) + 1.0
    axis = hull[j] - hull[i]
    norm = np.linalg.norm(axis)
    if norm == 0:
        return d1, 1.0, d1
    perp = np.array([-axis[1], axis[0]]) / norm
    proj = pts @ perp
    d2 = float(proj.max() - proj.min()) + 1.0
    return d1, d2, d1 * d2


def _axcodes(affine: np.ndarray) -> tuple[str, str, str]:
    return tuple(nib.aff2axcodes(affine))


def measure_timepoint(seg: np.ndarray, affine: np.ndarray, brain: np.ndarray | None) -> dict:
    """All v4 slice measurements for one timepoint, from the atlas-space label map."""
    ax = _axcodes(affine)
    out: dict = {"version": MEASURE_VERSION, "axcodes": "".join(ax), "shape": list(seg.shape)}

    enh = seg == ENH
    core = (seg == ENH) | (seg == NEC)

    enh_area = enh.sum(axis=(0, 1))
    out["enh_voxels"] = int(enh.sum())
    out["core_voxels"] = int(core.sum())
    if enh_area.max() > 0:
        z_e = int(np.argmax(enh_area))
        comp = _largest_component(enh[:, :, z_e])
        d1, d2, bp = bidimensional_product(comp)
        out["enh"] = {"z": z_e, "area_px": int(enh[:, :, z_e].sum()), "largest_component_px": int(comp.sum()),
                      "d1_mm": round(d1, 1), "d2_mm": round(d2, 1), "bp_mm2": round(bp, 1)}
    else:
        out["enh"] = None

    core_area = core.sum(axis=(0, 1))
    if core_area.max() > 0:
        z_l = int(np.argmax(core_area))
        sl = core[:, :, z_l]
        comp = _largest_component(sl)
        pts = np.argwhere(comp)
        cx, cy = pts.mean(axis=0)
        loc = {"z": z_l, "component_px": int(comp.sum()), "centroid_xy": [round(float(cx), 1), round(float(cy), 1)]}
        if brain is not None and (brain[:, :, z_l] > 0).any():
            b = np.argwhere(brain[:, :, z_l] > 0)
            (x0, y0), (x1, y1) = b.min(axis=0), b.max(axis=0)
            mid_x, mid_y = (x0 + x1) / 2.0, (y0 + y1) / 2.0
            side_is_high_x = cx > mid_x
            on_side = (pts[:, 0] > mid_x) if side_is_high_x else (pts[:, 0] <= mid_x)
            # array axis 0 code 'L' means increasing index points to the patient's left
            left_when_high = ax[0] == "L"
            hemi = "left" if (side_is_high_x == left_when_high) else "right"
            ap_high = cy > mid_y
            anterior_when_high = ax[1] == "A"
            ap = "anterior" if (ap_high == anterior_when_high) else "posterior"
            loc.update({
                "mid_x": round(float(mid_x), 1), "mid_y": round(float(mid_y), 1),
                "dx_mm": round(float(abs(cx - mid_x)), 1), "dy_mm": round(float(abs(cy - mid_y)), 1),
                "side_fraction": round(float(on_side.mean()), 3),
                "hemisphere": hemi, "ap_half": ap,
            })
        out["core"] = loc
    else:
        out["core"] = None
    return out


def lil_eligible(m: dict) -> tuple[bool, str]:
    """(eligible, reason) for a LIL item on this follow-up timepoint's measurements."""
    core = m.get("core")
    if not core or "hemisphere" not in core:
        return False, "no tumour core / brain mask"
    if core["component_px"] < MIN_LESION_PX:
        return False, "tumour-core component smaller than 100 mm^2"
    if core["dx_mm"] < MIDLINE_MARGIN_PX or core["dy_mm"] < MIDLINE_MARGIN_PX:
        return False, "centroid within 10 mm of a midline"
    if core["side_fraction"] < SIDE_FRACTION_MIN:
        return False, "lesion crosses the midline"
    return True, "ok"


def imaging_rano_label(bp_ref: float, bp_fu: float, bp_nadir: float | None = None) -> str | None:
    """Enhancement-based RANO category from bidimensional products (mm^2), or None when the enhancement
    criteria cannot decide.

    RANO judges progression against the NADIR (smallest earlier measurement) and response against the
    post-operative BASELINE. When neither scan has measurable enhancing disease, stable disease and complete
    response cannot be told apart from enhancement (the distinction rests on duration, T2/FLAIR and steroids),
    so the rule abstains and the item is not built. T2/FLAIR progression, clinical status and steroid dose are
    not represented."""
    nadir = bp_ref if bp_nadir is None else min(bp_ref, bp_nadir)
    m_ref, m_fu, m_nad = bp_ref >= MEASURABLE_BP_MM2, bp_fu >= MEASURABLE_BP_MM2, nadir >= MEASURABLE_BP_MM2
    if m_fu and (not m_nad or bp_fu >= 1.25 * nadir):
        return "progressive disease"    # new measurable lesion, or >=25% above the nadir
    if not m_ref:
        return None                     # nothing measurable to compare against: enhancement cannot decide
    if not m_fu:
        return "complete response"
    return "partial response" if bp_fu <= 0.5 * bp_ref else "stable disease"


def cache_path(patient_id: str, timepoint: str, root: Path | None = None) -> Path:
    root = root or Path(lcfg.LUMIERE_DATA_DIR) / "v4" / "measurements"
    return root / patient_id / f"{timepoint}.json"


def load_or_measure(zf, patient_id: str, timepoint: str, root: Path | None = None, force: bool = False) -> dict | None:
    from src.lumiere_facts import _load_nifti_bytes, _read_member
    path = cache_path(patient_id, timepoint, root)
    if path.exists() and not force:
        return json.loads(path.read_text())
    base = f"{lcfg.ZIP_ROOT}/{patient_id}/{timepoint}/DeepBraTumIA-segmentation/atlas"
    seg_bytes = _read_member(zf, f"{base}/segmentation/seg_mask.nii.gz")
    brain_bytes = _read_member(zf, f"{base}/skull_strip/brain_mask.nii.gz")
    if seg_bytes is None:
        return None
    seg, aff = _load_nifti_bytes(seg_bytes)
    brain = _load_nifti_bytes(brain_bytes)[0] if brain_bytes is not None else None
    m = measure_timepoint(np.rint(seg).astype(np.int16), aff, brain)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(m, indent=1))
    return m
