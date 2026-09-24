"""Sanity tests for the v4 item-set code (CPU, no network): python -m tests.test_lumiere_v4"""
import numpy as np

from src.lumiere_labels import canonical_answer_text
from src.lumiere_measure import bidimensional_product, imaging_rano_label, lil_eligible, measure_timepoint
from src.lumiere_v4 import EARLY_MAX_X, LATE_MIN_X, tcm_class
from src.v4_conditions import _retext_window, tcm_rule_class


def test_bidimensional_product():
    disc = np.zeros((61, 61), bool)
    yy, xx = np.ogrid[:61, :61]
    disc[(yy - 30) ** 2 + (xx - 30) ** 2 <= 20 ** 2] = True
    d1, d2, bp = bidimensional_product(disc)
    assert 40 <= d1 <= 43 and 38 <= d2 <= 43, (d1, d2)
    rect = np.zeros((50, 50), bool)
    rect[10:20, 10:30] = True          # 10 x 20 pixels
    d1, d2, bp = bidimensional_product(rect)
    assert d1 > 20 and d2 >= 9 and bp > 150, (d1, d2, bp)
    assert bidimensional_product(np.zeros((5, 5), bool)) == (0.0, 0.0, 0.0)


def test_rano_rule():
    assert imaging_rano_label(400, 600, 400) == "progressive disease"        # +50% over the nadir
    assert imaging_rano_label(400, 480, 400) == "stable disease"             # +20%
    assert imaging_rano_label(400, 150, 400) == "partial response"           # -62%
    assert imaging_rano_label(400, 20, 400) == "complete response"           # nothing measurable left
    assert imaging_rano_label(20, 20, 20) is None                            # nothing to compare: undetermined
    assert imaging_rano_label(20, 400, 20) == "progressive disease"          # new measurable lesion
    assert imaging_rano_label(600, 700, 300) == "progressive disease"        # +133% over the nadir although +17% over baseline


def test_measure_orientation_and_localisation():
    seg = np.zeros((182, 218, 182), np.int16)
    brain = np.zeros_like(seg)
    brain[30:150, 20:200, 60:120] = 1                    # mid_x = 89.5, mid_y = 109.5
    seg[110:130, 150:170, 90] = 1                        # high x, high y: array axes L and A -> left, anterior
    aff = np.diag([-1.0, 1.0, 1.0, 1.0]); aff[:3, 3] = [90, -126, -72]
    m = measure_timepoint(seg, aff, brain)
    assert m["axcodes"] == "LAS", m["axcodes"]
    assert m["core"]["hemisphere"] == "left" and m["core"]["ap_half"] == "anterior", m["core"]
    assert lil_eligible(m)[0]
    seg2 = np.zeros_like(seg); seg2[50:70, 30:50, 90] = 2   # low x, low y -> right, posterior
    m2 = measure_timepoint(seg2, aff, brain)
    assert m2["core"]["hemisphere"] == "right" and m2["core"]["ap_half"] == "posterior"
    seg3 = np.zeros_like(seg); seg3[85:95, 150:170, 90] = 1   # crosses the midline
    assert not lil_eligible(measure_timepoint(seg3, aff, brain))[0]


def test_tcm_rule():
    assert tcm_class(False, 30) == "C" and tcm_class(False, 1) is None
    assert tcm_class(True, EARLY_MAX_X) == "F" and tcm_class(True, LATE_MIN_X) == "E"
    assert tcm_class(True, 12) is None                    # inside the excluded margin
    assert tcm_rule_class("Progressive disease", 4) == "confirm"
    assert tcm_rule_class("Progressive disease", 20) == "escalate"
    assert tcm_rule_class("Stable disease", 20) == "continue"


def test_retext_window():
    q = {"id": "P_TCM", "question": "This MRI is 14 weeks after surgery; chemoradiotherapy ended about 4 weeks before this scan."}
    r = _retext_window(q, 4, 14, 20)
    assert "30 weeks after surgery" in r["question"] and "about 20 weeks before" in r["question"]


def test_canonical():
    assert canonical_answer_text("Progressive disease (PD)") == canonical_answer_text("Progressive disease") == "Progressive disease"
    assert canonical_answer_text("Stable disease.") == "Stable disease"
    assert canonical_answer_text("Right hemisphere, anterior half") == "Right hemisphere, anterior half"


def test_v4_items_if_built():
    from pathlib import Path
    from src.lumiere_loader import load_lumiere
    if not Path("data/lumiere/v4/reviewed").exists():
        return
    cases = load_lumiere(item_set="v4", include_unreviewed=True)
    assert len(cases) > 0
    for c in cases:
        for ph in ("AIA", "DSCR", "TCM"):
            q = c["phases"][ph][0]
            assert q["correct_answer"] in q["options"]
        pj = c["phases"].get("PJRF")
        if pj:
            assert pj[0]["correct_answer"] is None and pj[0]["forecast"]["outcome"] in (0, 1)
            assert list(pj[0]["options"].values())[0] == "Below 20%"     # ordinal bins are never shuffled
        # every image an item names exists
        for ph, qs in c["phases"].items():
            for q in qs:
                for f in q["_image_path"]:
                    assert (Path(q["_image_dir"]) / f).exists(), (q["id"], f)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
