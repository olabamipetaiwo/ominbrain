"""Sanity tests for the v4 item-set code (CPU, no network): python -m tests.test_lumiere_v4"""
import numpy as np

from src.lumiere_labels import canonical_answer_text
from src.lumiere_measure import (bidimensional_product, imaging_rano_label, lil_eligible, measure_timepoint,
                                  nearest_component)
from src.lumiere_v4 import EARLY_MAX_X, LATE_MIN_X, TCM_RULE_STATEMENT, tcm_class
from src.prompts import build_main_prompt
from src.v4_conditions import CONDITIONS, PHASES_BY_CONDITION, _retext_window, tcm_rule_class


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
    big, small = (20.0, 20.0), (4.0, 5.0)   # measurable (both >=10mm) vs. not
    assert imaging_rano_label(400, 600, big, big, 400, big) == "progressive disease"     # +50% over the nadir
    assert imaging_rano_label(400, 480, big, big, 400, big) == "stable disease"          # +20%
    assert imaging_rano_label(400, 150, big, (15.0, 10.0), 400, big) == "partial response"  # -62%
    assert imaging_rano_label(400, 20, big, small, 400, big) == "complete response"      # nothing measurable left
    assert imaging_rano_label(20, 20, small, small, 20, small) is None                   # nothing to compare: undetermined
    assert imaging_rano_label(20, 400, small, big, 20, small) == "progressive disease"   # new measurable lesion
    assert imaging_rano_label(600, 700, (20.0, 30.0), (20.0, 35.0), 300, (15.0, 20.0)) == "progressive disease"  # +133% over the nadir although +17% over baseline


def test_rano_rule_measurability_is_not_just_the_product():
    # 20x6mm: product is 120mm^2 (>=100, old buggy threshold) but the short axis is <10mm, so RANO
    # would not call this measurable disease. paper/review.md concern 1.
    thin = (20.0, 6.0)
    assert imaging_rano_label(120, 120, thin, thin, 120, thin) is None
    # same product, but both axes >=10mm: genuinely measurable, and unchanged (stable) at follow-up.
    square = (11.0, 11.0)  # product 121mm^2
    assert imaging_rano_label(121, 121, square, square, 121, square) == "stable disease"


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


def test_lesion_correspondence_tracks_nearest_not_largest():
    # paper/review.md concern 1: at follow-up, a NEW larger lesion appears far from the reference site,
    # while a smaller lesion persists near the reference site. Naive "largest component" would silently
    # switch lesions; nearest_component must follow the one near the reference instead.
    seg = np.zeros((80, 80, 5), np.int16)
    seg[10:14, 10:14, 2] = 1     # small lesion near (12,12,2): 4x4 = 16 voxels
    seg[50:66, 50:66, 2] = 1     # large, DISTANT lesion near (58,58,2): 16x16 = 256 voxels
    m = measure_timepoint(seg, np.eye(4), None)
    assert len(m["enh_components"]) == 2
    assert m["enh"]["voxels"] == 256          # the naive "largest" pick (what the old code always used)
    anchor = [12.0, 12.0, 2.0]                # the reference scan's lesion was here
    near = nearest_component(anchor, m["enh_components"])
    assert near["voxels"] == 16, "must track the lesion near the reference, not whichever is largest"
    # no anchor (reference itself had no measurable disease): falls back to the largest component
    assert nearest_component(None, m["enh_components"])["voxels"] == 256
    assert nearest_component(anchor, []) is None


def test_explicit_rule_condition_states_the_rule_in_the_prompt():
    # paper/review.md concern 2: every other TCM condition only compares the model's answer against the
    # rule after the fact; explicit_rule must be the one place the rule text actually reaches the model.
    assert "explicit_rule" in CONDITIONS
    assert PHASES_BY_CONDITION["explicit_rule"] == ("TCM",)
    q = {"question": "What next?", "options": {"A": "x", "B": "y"}}
    case = {"title": "t", "modality": "mri"}
    msgs = build_main_prompt(q, case, "TCM", [], extra_instructions=TCM_RULE_STATEMENT)
    user_text = msgs[1]["content"] if isinstance(msgs[1]["content"], str) else msgs[1]["content"][-1]["text"]
    assert TCM_RULE_STATEMENT in user_text
    # without extra_instructions (every other condition), the rule text must NOT leak in
    msgs_plain = build_main_prompt(q, case, "TCM", [])
    plain_text = msgs_plain[1]["content"] if isinstance(msgs_plain[1]["content"], str) else msgs_plain[1]["content"][-1]["text"]
    assert TCM_RULE_STATEMENT not in plain_text


def test_system_prompt_does_not_assume_an_image():
    from src.prompts import SYSTEM_PROMPT
    assert "you will be shown a real brain imaging scan" not in SYSTEM_PROMPT.lower()


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
