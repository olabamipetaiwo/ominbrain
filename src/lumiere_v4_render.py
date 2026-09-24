"""
Slice rendering for the v4 item set.

Every v4 visual answer key is computed on a specific axial slice (src/lumiere_measure.py); this module
renders exactly that slice, so the key is a function of the displayed pixels.

  * Atlas-space, skull-stripped volumes (DeepBraTumIA `atlas/skull_strip/{ct1,t1,t2,flair}_skull_strip`),
    the same 1 mm MNI grid as the segmentation masks.
  * Intensity window: 1st-99.5th percentile of the non-zero voxels of the WHOLE volume (not of the slice),
    so two timepoints of one patient are windowed consistently.
  * Orientation: np.rot90 of the [x, y] slice -> radiological display (patient's right on the left of the
    image, anterior at the top) when the atlas x axis points to the patient's left and y to anterior; this is
    checked against the affine and the render is refused otherwise.
  * 4x magnification with a 20 mm scale bar burned in at the bottom left (1 atlas voxel = 1 mm).
"""

from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np
from PIL import Image, ImageDraw

import config.lumiere as lcfg

SEQUENCE_FILES = {
    "ct1": "ct1_skull_strip.nii.gz",
    "t1": "t1_skull_strip.nii.gz",
    "t2": "t2_skull_strip.nii.gz",
    "flair": "flair_skull_strip.nii.gz",
}
MAGNIFY = 4
SCALE_BAR_MM = 20


def _member(patient_id: str, timepoint: str, sequence: str) -> str:
    return (f"{lcfg.ZIP_ROOT}/{patient_id}/{timepoint}/DeepBraTumIA-segmentation/atlas/skull_strip/"
            f"{SEQUENCE_FILES[sequence]}")


def render_slice(volume: np.ndarray, affine: np.ndarray, z: int, out_path: Path) -> Path:
    ax = tuple(nib.aff2axcodes(affine))
    if ax[0] != "L" or ax[1] != "A":
        raise ValueError(f"unexpected atlas orientation {ax}; the radiological render assumes L,A,*")
    nz = volume[volume > 0]
    lo, hi = np.percentile(nz, 1), np.percentile(nz, 99.5)
    sl = np.rot90(volume[:, :, z])
    sl = np.clip((sl - lo) / max(hi - lo, 1e-6), 0, 1) * 255
    img = Image.fromarray(sl.astype(np.uint8), mode="L").resize(
        (sl.shape[1] * MAGNIFY, sl.shape[0] * MAGNIFY), Image.LANCZOS).convert("RGB")
    d = ImageDraw.Draw(img)
    bar = SCALE_BAR_MM * MAGNIFY
    x0, y = 12, img.height - 22
    d.line([(x0, y), (x0 + bar, y)], fill=(255, 255, 255), width=3)
    d.text((x0, y - 14), f"{SCALE_BAR_MM} mm", fill=(255, 255, 255))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path


def render_from_zip(zf, patient_id: str, timepoint: str, sequence: str, z: int, out_path: Path) -> Path | None:
    from src.lumiere_facts import _load_nifti_bytes, _read_member
    data = _read_member(zf, _member(patient_id, timepoint, sequence))
    if data is None:
        return None
    vol, aff = _load_nifti_bytes(data)
    return render_slice(vol, aff, z, out_path)
