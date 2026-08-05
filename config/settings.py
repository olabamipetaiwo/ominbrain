# Model settings (overridden per run via CausalChainEvaluator)
MODEL = "gpt-4o"
BASE_URL = None
GATING_THRESHOLD = 0.5
GROUNDING_THRESHOLD = 0.3
MAX_TOKENS = 800
TEMPERATURE = 0.0

# Clinical phases — causal order
PHASES = ["AIA", "LIL", "DSCR", "PJRF", "TCM"]

PHASE_NAMES = {
    "AIA":  "Anatomical and Imaging Assessment",
    "LIL":  "Lesion Identification and Localization",
    "DSCR": "Diagnostic Synthesis and Causal Reasoning",
    "PJRF": "Prognostic Judgment and Risk Forecasting",
    "TCM":  "Therapeutic Cycle Management",
}

FAILURE_TYPE = {
    "AIA":  "perception",
    "LIL":  "perception",
    "DSCR": "reasoning",
    "PJRF": "decision",
    "TCM":  "decision",
}

PHASE_DEPENDENCIES = {
    "AIA":  [],
    "LIL":  ["AIA"],
    "DSCR": ["AIA", "LIL"],
    "PJRF": ["AIA", "LIL", "DSCR"],
    "TCM":  ["AIA", "LIL", "DSCR", "PJRF"],
}

# Dataset (HuggingFace)
HF_DATASET_ID   = "FrankPN/OmniBrainBench"
DATA_CACHE_DIR  = "data"
JSON_FILENAME   = "closed-ended-qa_6823.json"
ZIP_FILENAME    = "closed-ended-qa_6823.zip"
IMAGES_SUBDIR   = "closed-ended-qa_6823"     # actual extracted folder from zip

# Image pre-processing
MAX_IMAGE_DIM = 1280           # match OmniBrainBench preprocessing (was 1024)

# API retry settings
API_RETRY_ATTEMPTS = 3
API_RETRY_DELAY    = 5         # seconds — doubles each attempt (exponential backoff)
