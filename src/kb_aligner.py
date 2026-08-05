"""
Knowledge Alignment Benchmarking (KAB) for OmniBrainBench.

Phase-aware KB scoring:
  AIA, LIL        → RadLex  (radiology anatomy, imaging descriptors, lesion features)
  DSCR, PJRF, TCM → NCIt   (tumor biology, WHO grading, staging, treatment)

Two scores per question:
  kb_alignment_score      — fraction of clinical concepts used that are in the phase KB
  concept_precision_score — fraction of phase-KB concepts consistent with the correct answer

missed_concepts: phase-KB terms present in the correct answer but absent from model output.
  Used for feedback-adaptation injection (re-run phase with clinical correction).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

PHASE_KB: dict[str, str] = {
    "AIA":  "radlex",
    "LIL":  "radlex",
    "DSCR": "ncit",
    "PJRF": "ncit",
    "TCM":  "ncit",
}


@dataclass
class KBAlignResult:
    phase: str
    kb_used: str
    extracted_concepts: list[str] = field(default_factory=list)
    matched_concepts: list[str] = field(default_factory=list)
    missed_concepts: list[str] = field(default_factory=list)
    kb_alignment_score: float = 0.0       # matched / extracted  (0.0–1.0)
    concept_precision_score: float = 0.0  # on-target / matched  (0.0–1.0)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9]+(?:[-/][a-zA-Z0-9]+)*", text.lower())


def _find_kb_matches(tokens: list[str], kb: set[str], max_n: int = 4) -> list[str]:
    """
    Greedy longest-match scan over token list.
    Tries longer n-grams first; consumed positions are not reused.
    Returns unique matched KB terms in order of first appearance.
    """
    n = len(tokens)
    used: set[int] = set()
    matches: list[str] = []

    for gram_size in range(min(max_n, n), 0, -1):
        for i in range(n - gram_size + 1):
            if any(j in used for j in range(i, i + gram_size)):
                continue
            phrase = " ".join(tokens[i : i + gram_size])
            if phrase in kb:
                matches.append(phrase)
                used.update(range(i, i + gram_size))

    return matches


def _load_flat_file(path: Path) -> set[str]:
    terms: set[str] = set()
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip().lower()
            if line and not line.startswith("#"):
                terms.add(line)
    return terms


def _load_owl(path: Path) -> set[str]:
    import xml.etree.ElementTree as ET
    tree = ET.parse(path)
    root = tree.getroot()
    rdfs_label = "{http://www.w3.org/2000/01/rdf-schema#}label"
    xml_lang = "{http://www.w3.org/XML/1998/namespace}lang"
    terms: set[str] = set()
    for el in root.iter(rdfs_label):
        lang = el.get(xml_lang)
        if lang and lang != "en":
            continue  # skip non-English labels (e.g. RadLex ships English + German rdfs:label pairs)
        text = (el.text or "").strip().lower()
        if text:
            terms.add(text)
    return terms


class KBAligner:
    """
    Phase-aware KB alignment scorer for the KAB framework.

    Requires real KB files — no stub fallback:
        aligner = KBAligner(
            radlex_path=Path("data/kb/radlex.owl"),
            ncit_path=Path("data/kb/ncit.owl"),
        )
    Both OWL/XML and plain one-term-per-line flat files are supported.
    """

    def __init__(
        self,
        radlex_path: Path,
        ncit_path: Path,
    ) -> None:
        self._kbs: dict[str, set[str]] = {
            "radlex": self._load(radlex_path),
            "ncit":   self._load(ncit_path),
        }
        self._all_terms: set[str] = self._kbs["radlex"] | self._kbs["ncit"]

    def _load(self, path: Path) -> set[str]:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"KB file not found: {path}")
        if path.suffix.lower() in (".owl", ".xml"):
            return _load_owl(path)
        return _load_flat_file(path)

    def align(
        self,
        phase: str,
        visual_grounding: str,
        reasoning: str,
        correct_answer_text: str = "",
    ) -> KBAlignResult:
        """
        Score one model response against the phase-appropriate KB.

        kb_alignment_score:
            All KB terms (union) found in model output = extracted_concepts.
            Subset in the phase KB = matched_concepts.
            Score = matched / extracted.

        concept_precision_score:
            Of matched_concepts, fraction that appear in correct_answer_text.
            Zero when there are no matches (not undefined).

        missed_concepts:
            Phase-KB terms present in correct_answer_text but absent from output.
            Injected as clinical corrections in the feedback-adaptation loop.
        """
        kb_name = PHASE_KB.get(phase, "radlex")
        phase_kb = self._kbs[kb_name]

        combined = f"{visual_grounding} {reasoning}"
        tokens = _tokenize(combined)

        extracted = _find_kb_matches(tokens, self._all_terms)
        matched = [c for c in extracted if c in phase_kb]

        missed: list[str] = []
        if correct_answer_text:
            ans_tokens = _tokenize(correct_answer_text)
            ans_matches = _find_kb_matches(ans_tokens, phase_kb)
            combined_lower = combined.lower()
            missed = [t for t in ans_matches if t not in combined_lower]

        kb_alignment_score = len(matched) / len(extracted) if extracted else 0.0

        if matched and correct_answer_text:
            ans_lower = correct_answer_text.lower()
            on_target = sum(1 for c in matched if c in ans_lower)
            concept_precision_score = on_target / len(matched)
        else:
            concept_precision_score = 0.0

        return KBAlignResult(
            phase=phase,
            kb_used=kb_name,
            extracted_concepts=extracted,
            matched_concepts=matched,
            missed_concepts=missed,
            kb_alignment_score=round(kb_alignment_score, 3),
            concept_precision_score=round(concept_precision_score, 3),
        )
