"""Guessability check for LUMIERE MCQ items: how often is the correct option the longest?

Chance is 25% for 4 options. A high rate means a length-only baseline can score well
without any clinical reasoning. Re-run after the expert review / any re-drafting.

Usage: python -m tools.check_option_bias [--drafts-dir data/lumiere/drafts]
"""
import argparse
import collections
import glob
import json


from src.lumiere_drafter import ABSOLUTE, HEDGE  # single source for the keyword lists


def cue_guess_rate(items):
    """Share of items where a keyword-only guesser (hedge words minus absolute words) has the
    correct option uniquely highest. Ad-hoc word lists; a rough lower bound on style guessability."""
    score = lambda t: sum(w in t for w in HEDGE) - sum(w in t for w in ABSOLUTE)
    hit = 0
    for q in items:
        s = {k: score(v.lower()) for k, v in q["options"].items()}
        hit += s[q["correct_answer"]] > max(v for k, v in s.items() if k != q["correct_answer"])
    return hit / len(items)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--drafts-dir", default="data/lumiere/drafts")
    args = ap.parse_args()

    by_phase = collections.defaultdict(list)
    for f in sorted(glob.glob(f"{args.drafts_dir}/*.json")):
        for q in json.load(open(f)):
            by_phase[q["id"].split("_")[-1]].append(q)

    print(f"{'Phase':6} {'N':>3} {'longest=correct':>16} {'mean len correct/distractor':>28}")
    for phase, items in by_phase.items():
        longest = sum(
            len(q["options"][q["correct_answer"]]) == max(len(v) for v in q["options"].values())
            for q in items
        )
        cor = sum(len(q["options"][q["correct_answer"]]) for q in items) / len(items)
        dis = sum(
            len(v) for q in items for k, v in q["options"].items() if k != q["correct_answer"]
        ) / (3 * len(items))
        print(f"{phase:6} {len(items):>3} {longest:>5} ({100 * longest / len(items):3.0f}%)"
              f"{cor:>18.0f} / {dis:.0f}")
    print("chance = 25%")
    print("\nHedge/absolute keyword guesser (correct option uniquely highest):")
    for phase, items in by_phase.items():
        print(f"  {phase:6} {100 * cue_guess_rate(items):3.0f}%")


if __name__ == "__main__":
    main()
