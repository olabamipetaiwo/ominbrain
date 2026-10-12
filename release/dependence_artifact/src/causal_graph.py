"""
Causal graph structure and gating logic.

AIA -> LIL -> DSCR -> PJRF -> TCM

A phase unlocks only when every upstream phase met the gating threshold.
"""
import config


def get_upstream_phases(phase: str) -> list[str]:
    return config.PHASE_DEPENDENCIES[phase]


def check_gate(phase_scores: dict[str, float], phase: str, threshold: float) -> bool:
    """True if every upstream phase met threshold. AIA is always unlocked."""
    for upstream in get_upstream_phases(phase):
        if upstream not in phase_scores or phase_scores[upstream] < threshold:
            return False
    return True


def phase_index(phase: str) -> int:
    return config.PHASES.index(phase)
