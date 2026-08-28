# LUMIERE dataset config — real longitudinal glioblastoma MRI (91 patients),
# used to build a genuine same-patient causal-chain dataset (replaces the
# stitched-multi-patient "chains" in OmniBrainBench's source_file grouping).
#
# Source: Suter et al., "The LUMIERE Dataset: Longitudinal Glioblastoma MRI
#   with Expert RANO Evaluation", Sci Data 9, 768 (2022).
#   https://www.nature.com/articles/s41597-022-01881-7
# Hosting: Figshare/Springer Nature collection
#   DOI 10.6084/m9.figshare.c.5904905.v1  (collection id 5904905)
# License: non-commercial use (readme item itself is CC0) — note in paper's
#   data/ethics section.
#
# Article/file IDs below were resolved live via the Figshare API on 2026-08-26
# (GET https://api.figshare.com/v2/articles/<article_id>). They can change if
# the dataset is revised — lumiere_downloader.py re-resolves from the API at
# runtime and only falls back to these as a cached default.

FIGSHARE_COLLECTION_DOI = "10.6084/m9.figshare.c.5904905.v1"

FIGSHARE_ARTICLES = {
    "readme": {
        "article_id": 21266241,
        "file_id": 37983597,
        "filename": "LUMIERE-readme.pdf",
    },
    "rano_ratings": {
        "article_id": 21195556,
        "file_id": 38369741,
        "filename": "LUMIERE-ExpertRating-v202211.csv",
    },
    "demographics": {
        "article_id": 21195559,
        "file_id": 37575637,
        "filename": "LUMIERE-Demographics_Pathology.csv",
    },
    "completeness": {
        "article_id": 21195430,
        "file_id": 37575523,
        "filename": "LUMIERE-datacompleteness.csv",
    },
    "imaging": {
        "article_id": 21249516,
        "file_id": 38249697,
        "filename": "Imaging-v202211.zip",
        "approx_size_bytes": 32_565_467_707,
    },
}

# RANO rating codes as they actually appear in LUMIERE-ExpertRating-v202211.csv
# "Rating" column (confirmed 2026-08-26 by inspecting the real file). Two are
# baseline surgical states, not response categories — only the 4 response
# codes are used for DSCR question authoring; Pre-Op/Post-Op inform AIA/TCM
# framing instead. Raw values also include whitespace/formatting noise
# ("Post-Op ", "Post-Op/PD", NaN) — normalize (strip, take first "/"-token)
# before matching against this map.
RANO_RESPONSE_CODES = {
    "PD": "progressive disease",
    "SD": "stable disease",
    "PR": "partial response",
    "CR": "complete response",
}
RANO_BASELINE_CODES = {"Pre-Op": "pre-operative", "Post-Op": "post-operative"}

RANO_TO_LETTER = {
    "progressive disease": "A",
    "stable disease": "B",
    "partial response": "C",
    "complete response": "D",
}

# Segmentation tools present in the imaging archive (both automated, not
# manually verified — RANO labels are the actual expert ground truth here).
SEGMENTATION_TOOLS = ["HD-GLIO-AUTO", "DeepBraTumIA"]
SEGMENTATION_TOOL_PRIMARY = "HD-GLIO-AUTO"

# Anatomical sequence used for atlas registration (LIL localization only —
# volume/volume-change facts come from the mask's own header, no registration
# needed for those).
LOCALIZATION_SEQUENCE = "t1c"

# Maps each LUMIERE-authored question to the closest existing task_label from
# src/phase_map.py's TASK_PHASE_MAP, so KB-alignment grounding-term scoring
# (src/kb_aligner.py, TASK_GROUNDING_TERMS) works unmodified on LUMIERE cases
# without needing new phase_map.py entries.
LUMIERE_TASK_LABEL_MAP = {
    "AIA": "Imaging Modality Identification",
    "LIL": "Lesion Localization",
    "DSCR": "Disease Diagnosis Reasoning",
    "PJRF": "Prognostic Factor Analysis",
    "TCM": "Treatment Plan Selection",
}

# Target size of this build pass. Originally 30 (matching the feasibility
# estimate presented to/approved by the professor, ~20-35 expert hours);
# expanded to the FULL eligible cohort per user decision 2026-08-26, so the
# expert reviews everything in one pass instead of doing this in tranches.
# 55 is the true eligible count under select_target_patients()'s filter
# (>=3 real response-rated timepoints AND full 4-sequence+both-segmentation
# imaging) — confirmed from that function's own output, not an estimate.
TARGET_N_PATIENTS = 55
MIN_RANO_TIMEPOINTS = 3  # minimum real response-rated follow-ups for a genuine chain

LUMIERE_DATA_DIR = "data/lumiere"

# Real per-patient folder/file layout — confirmed 2026-08-26 both from the
# readme PDF and by actually listing Imaging-v202211.zip's central directory
# (31,370 entries) via lumiere_downloader.list_zip_entries():
#   Imaging/<patient_id>/<timepoint>/{T1,CT1,T2,FLAIR}.nii.gz
#                                     DeepBraTumIA-segmentation/atlas/segmentation/
#                                         seg_mask.nii.gz, measured_volumes_in_mm3.json
#                                     HD-GLIO-AUTO-segmentation/registered/segmentation.nii.gz
# patient_id like "Patient-001" (zero-padded 3 digits, matches the CSVs'
# "Patient" column exactly); timepoint like "week-000", "week-000-1"
# (same-week repeat study), "week-044" — matches the CSVs' "Timepoint"/"Date"
# columns exactly (verified against Patient-001: week-000-1, week-000-2,
# week-044, week-056).
# IMPORTANT: DeepBraTumIA's "atlas" outputs are already registered to MNI
# space by the dataset authors — no registration step needed on our end for
# lesion-location facts (just a centroid -> standard-atlas-region lookup).
# measured_volumes_in_mm3.json ships precomputed tumor-region volumes per
# timepoint — no voxel-counting needed either.
ZIP_ROOT = "Imaging"
PATIENT_DIR_TEMPLATE = "Patient-{:03d}"
DEEPBRATUMIA_ATLAS_MASK = "DeepBraTumIA-segmentation/atlas/segmentation/seg_mask.nii.gz"
DEEPBRATUMIA_VOLUMES_JSON = "DeepBraTumIA-segmentation/atlas/segmentation/measured_volumes_in_mm3.json"
HDGLIO_REGISTERED_MASK = "HD-GLIO-AUTO-segmentation/registered/segmentation.nii.gz"
# Skull-stripped anatomical series (atlas space) used for slice-PNG rendering
DEEPBRATUMIA_ATLAS_CT1 = "DeepBraTumIA-segmentation/atlas/skull_strip/ct1_skull_strip.nii.gz"
