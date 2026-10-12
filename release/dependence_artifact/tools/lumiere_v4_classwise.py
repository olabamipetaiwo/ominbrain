"""Class-wise DSCR behaviour for the worked-example model (reviewer concern 1).

Aggregate DSCR accuracy below the majority-class share does not establish that the model ignores the slice: a
model can recover some non-majority classes while losing majority-class items, so it is neither a constant
predictor nor a correct one. This computes the own-image RANO confusion matrix (key class x predicted class)
and per-class recall for Llama-4-Scout on DSCR, reusing the option shuffle the run saw (``load_item``) to map
each stored answer letter back to its class text. No model is called; this is pure re-analysis.

  python -m tools.lumiere_v4_classwise            # writes results/lumiere_v4_classwise.json
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import tools.lumiere_v4_stats as st
from src.lumiere_labels import canonical_answer_text
from tools.lumiere_v4_donor_validation import load_item

# RANO classes in descending frequency in the cohort (progressive disease is the majority class).
CLASSES = ["Progressive disease", "Complete response", "Stable disease", "Partial response"]


def confusion(model: str, phase: str = "DSCR", condition: str = "own") -> dict:
    recs = st.load_records(model)
    conf: dict[str, Counter] = defaultdict(Counter)
    key_n: Counter = Counter()
    n = correct = 0
    for (c, p, k), r in recs.items():
        if p != phase or k != condition:
            continue
        try:
            sh, corr, _ = load_item(c, phase)
        except StopIteration:
            continue
        key_cls = canonical_answer_text(sh[corr])
        ans = r.get("model_answer")
        pred_cls = canonical_answer_text(sh[ans]) if ans in sh else "unparseable"
        conf[key_cls][pred_cls] += 1
        key_n[key_cls] += 1
        n += 1
        correct += (key_cls == pred_cls)
    pred_n: Counter = Counter()
    for kc in conf:
        for pc, v in conf[kc].items():
            pred_n[pc] += v
    majority = max(key_n.values()) if key_n else 0
    return {
        "model": model, "phase": phase, "condition": condition, "n": n,
        "accuracy": 100.0 * correct / n if n else float("nan"),
        "majority_share": 100.0 * majority / n if n else float("nan"),
        "classes": CLASSES,
        "matrix": {kc: {pc: conf[kc].get(pc, 0) for pc in CLASSES + ["unparseable"]} for kc in CLASSES},
        "key_n": {kc: key_n.get(kc, 0) for kc in CLASSES},
        "pred_n": {pc: pred_n.get(pc, 0) for pc in CLASSES + ["unparseable"]},
        "recall": {kc: (100.0 * conf[kc].get(kc, 0) / key_n[kc]) if key_n.get(kc) else float("nan") for kc in CLASSES},
        "correct_on_majority": conf[CLASSES[0]].get(CLASSES[0], 0),          # majority-class items answered correctly
        "correct_off_majority": correct - conf[CLASSES[0]].get(CLASSES[0], 0),  # non-majority items answered correctly
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Llama-4-Scout")
    ap.add_argument("--out", default="results/lumiere_v4_classwise.json")
    args = ap.parse_args()
    res = confusion(args.model)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=1))
    print(f"{res['model']} {res['phase']} ({res['condition']}): n={res['n']} acc={res['accuracy']:.1f}% "
          f"majority={res['majority_share']:.1f}%")
    hdr = [c.split()[0][:4] for c in CLASSES] + ["unp", "n", "recall"]
    print(f"{'key/pred':<22}" + "".join(f"{h:>7}" for h in hdr))
    for kc in CLASSES:
        row = res["matrix"][kc]
        print(f"{kc:<22}" + "".join(f"{row[pc]:>7}" for pc in CLASSES)
              + f"{row['unparseable']:>7}{res['key_n'][kc]:>7}{res['recall'][kc]:>6.0f}%")
    print(f"correct on majority class: {res['correct_on_majority']}/{res['key_n'][CLASSES[0]]}; "
          f"correct on other classes: {res['correct_off_majority']}/{res['n'] - res['key_n'][CLASSES[0]]}")


if __name__ == "__main__":
    main()
