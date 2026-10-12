# Maps the full clinical_phase strings in OmniBrainBench JSON → our abbreviations
PHASE_MAP = {
    "Anatomical and Imaging Assessment":        "AIA",
    "Lesion Identification and Localization":   "LIL",
    "Diagnostic Synthesis and Causal Reasoning":"DSCR",
    "Prognostic Judgment and Risk Forecasting": "PJRF",
    "Therapeutic Cycle Management":             "TCM",
}

# task_label → phase (cross-reference / sanity check)
TASK_PHASE_MAP = {
    "Anatomical Structure Identification":       "AIA",
    "Imaging Modality Identification":           "AIA",
    "Anatomical Function Understanding":         "AIA",
    "Abnormal Screening":                        "LIL",
    "Lesion Feature Description":                "LIL",
    "Lesion Localization":                       "LIL",
    "Disease Diagnosis Reasoning":               "DSCR",
    "Pathophysiological Mechanism Correlation":  "DSCR",
    "Prognostic Factor Analysis":                "PJRF",
    "Risk Stratification":                       "PJRF",
    "Clinical Sign Prediction":                  "PJRF",
    "Treatment Plan Selection":                  "TCM",
    "Postoperative Outcome Assessment":          "TCM",
    "Drug Response Prediction":                  "TCM",
    "Preoperative Assessment":                   "TCM",
}

# Per-task visual keywords used for grounding faithfulness scoring
TASK_GROUNDING_TERMS = {
    "Anatomical Structure Identification":      ["structure", "anatomy", "region", "lobe", "gyrus", "sulcus", "nucleus"],
    "Imaging Modality Identification":          ["modality", "sequence", "weighted", "contrast", "enhancement", "signal"],
    "Anatomical Function Understanding":        ["function", "cortex", "network", "pathway", "activation"],
    "Abnormal Screening":                       ["abnormal", "lesion", "signal", "intensity", "hyperintense", "hypointense", "irregular"],
    "Lesion Feature Description":               ["size", "shape", "border", "margin", "enhancement", "necrosis", "edema", "mass"],
    "Lesion Localization":                      ["location", "region", "hemisphere", "lobe", "adjacent", "midline", "shift"],
    "Disease Diagnosis Reasoning":              ["diagnosis", "differential", "finding", "consistent", "pattern", "imaging"],
    "Pathophysiological Mechanism Correlation": ["mechanism", "pathology", "etiology", "cause", "vasogenic", "infiltration"],
    "Prognostic Factor Analysis":               ["prognosis", "outcome", "survival", "grade", "stage", "extent"],
    "Risk Stratification":                      ["risk", "severity", "classification", "score", "high", "low"],
    "Clinical Sign Prediction":                 ["symptom", "sign", "presentation", "clinical", "deficit"],
    "Treatment Plan Selection":                 ["treatment", "therapy", "management", "surgery", "resection", "radiation"],
    "Postoperative Outcome Assessment":         ["postoperative", "follow-up", "response", "recurrence", "residual"],
    "Drug Response Prediction":                 ["drug", "response", "chemotherapy", "medication", "targeted"],
    "Preoperative Assessment":                  ["preoperative", "surgical", "candidacy", "planning", "risk"],
}
