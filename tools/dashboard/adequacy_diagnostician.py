"""
adequacy_diagnostician.py -- a deterministic Adequacy Diagnostician,
matching the paper's own C-DET experimental condition (Task 2.2): "a
deterministic pre-check determines whether... the trace was sufficiently
long relative to the available semantic requirement or observed
distinguishing depth k_hat(m)... If these checks identify a unique
deficiency, the corresponding refinement action is selected
deterministically and the LLM is not called."

This is NOT a stand-in for the paper's full LLM-based Adequacy
Diagnostician (that's Thrust 2 proper, which the paper defines as an
LLM-agent architecture) -- it's specifically C-DET, the paper's own
non-LLM ablation baseline, used here as the whole mechanism rather than as
one arm of a comparison. Explicitly scoped, not a workaround.

What it diagnoses: right now, only "insufficient_scan_depth" for
TIMER-family constructs (TON/TOF/TP), using the paper's own K_PLC formula
from Figure 4: min-depth = ceil(PT / scan_period) + 1. This is the
clearest, most deterministic diagnosis available without an LLM -- given
a construct's PT and the scan period, the minimum observation depth
needed to see it fire is a closed-form calculation, not a judgment call.
Other diagnosis categories from the paper's taxonomy (unreached code,
missing branch outcome, missing observation point, weak oracle, missing
reset/initialization, potentially equivalent) are NOT implemented --
stated plainly rather than silently narrowed.
"""

from __future__ import annotations
import math
import re
from dataclasses import dataclass, field

from dashboard.distinguish_search import (
    run_distinguish_search, DistinguishResult, DistinguishSearchError, SCAN_PERIOD_MS,
)

MAX_REFINEMENT_ITERATIONS = 1  # bounded, matching the paper's imax concept -- kept small here
DEPTH_SAFETY_MARGIN_SCANS = 12  # generous: real-time scan execution has observed
                                  # scheduling slop of several scans vs. nominal
                                  # sequence_length (documented elsewhere in this
                                  # project -- SIGEV_THREAD overhead, process
                                  # startup), so a small margin isn't reliable


@dataclass
class DiagnosisRecord:
    category: str                  # "insufficient_scan_depth" | "no_deficiency_identified"
    evidence: dict = field(default_factory=dict)
    selected_action: str | None = None
    resolved_by: str = "precheck"  # always "precheck" here -- no LLM fallback exists in this build


@dataclass
class RefinementResult:
    final_result: DistinguishResult
    iterations: int
    diagnoses: list[DiagnosisRecord] = field(default_factory=list)
    log: str = ""


_TON_PRESET_RE = re.compile(r"\b(\w+)\s*:\s*(TON|TOF|TP)\b")
_PT_RE_TEMPLATE = r"{name}\s*\([^)]*PT\s*:=\s*T#(\d+)([SMH])"


def _extract_timer_presets(code: str) -> dict[str, int]:
    """Returns {instance_name: preset_in_seconds} for every TON/TOF/TP
    instance found, by locating its declared type then its PT argument at
    the call site.
    """
    presets = {}
    for name, _type in _TON_PRESET_RE.findall(code):
        m = re.search(_PT_RE_TEMPLATE.format(name=re.escape(name)), code)
        if not m:
            continue
        value, unit = int(m.group(1)), m.group(2)
        seconds = {"S": value, "M": value * 60, "H": value * 3600}[unit]
        presets[name] = seconds
    return presets


def _min_depth_for_preset(preset_seconds: int, scan_period_ms: int = SCAN_PERIOD_MS) -> int:
    """The paper's own K_PLC formula (Figure 4): min-depth = ceil(PT / scan_period) + 1."""
    return math.ceil((preset_seconds * 1000) / scan_period_ms) + 1


def diagnose_undetermined(
    original_code: str,
    mutated_code: str,
    attempted_sequence_length: int,
) -> DiagnosisRecord:
    """Task 2.2's deterministic pre-check, scoped to the one diagnosis
    category this build can determine with certainty: was the search
    trace too short to ever observe a timer construct fire at all,
    regardless of which side (original or mutant) fires first?

    Checks BOTH the original's and the mutant's timer presets (a preset
    change is exactly the case where the two constructs need different
    minimum depths) and returns the larger requirement -- the trace needs
    to be long enough to observe whichever one takes longer.
    """
    original_presets = _extract_timer_presets(original_code)
    mutant_presets = _extract_timer_presets(mutated_code)

    all_names = set(original_presets) | set(mutant_presets)
    if not all_names:
        return DiagnosisRecord(
            category="no_deficiency_identified",
            evidence={"reason": "no TIMER-family construct found -- this diagnostician "
                                  "only covers insufficient scan depth for timers"},
        )

    required_depths = []
    for name in all_names:
        for presets in (original_presets, mutant_presets):
            if name in presets:
                required_depths.append(_min_depth_for_preset(presets[name]))

    required_depth = max(required_depths) + DEPTH_SAFETY_MARGIN_SCANS

    if attempted_sequence_length >= required_depth:
        return DiagnosisRecord(
            category="no_deficiency_identified",
            evidence={
                "attempted_sequence_length": attempted_sequence_length,
                "computed_min_depth": required_depth,
                "reason": "search trace was already long enough -- insufficient depth "
                          "is not the (or not the only) explanation for 'undetermined'",
            },
        )

    return DiagnosisRecord(
        category="insufficient_scan_depth",
        evidence={
            "attempted_sequence_length": attempted_sequence_length,
            "computed_min_depth": required_depth,
            "timer_presets_seconds": {**original_presets, **{f"{k}(mutant)": v for k, v in mutant_presets.items()}},
            "formula": "min-depth = ceil(PT_ms / scan_period_ms) + 1 (paper's K_PLC, Figure 4) "
                       f"+ {DEPTH_SAFETY_MARGIN_SCANS}-scan safety margin",
        },
        selected_action=f"retry with sequence_length={required_depth}",
    )


def run_with_diagnosis_guided_refinement(
    original_code: str,
    mutated_code: str,
    library_content: str,
    initial_sequence_length: int = 30,
) -> RefinementResult:
    """The full Task 2.2 loop, deterministic-only: run DistinguishSearch;
    if the result is undetermined, run the deterministic pre-check; if it
    identifies a unique, fixable deficiency (insufficient scan depth),
    apply the corresponding action and retry once (MAX_REFINEMENT_ITERATIONS);
    otherwise stop and report undetermined with the diagnosis attached.
    """
    log_lines = []
    diagnoses = []

    result = run_distinguish_search(original_code, mutated_code, library_content,
                                     sequence_length=initial_sequence_length)
    log_lines.append(f"Iteration 0 (sequence_length={initial_sequence_length}): {result.status}"
                      + (f" at scan {result.witness_depth}" if result.witness_depth else ""))

    if result.status != "undetermined":
        return RefinementResult(final_result=result, iterations=0, diagnoses=[], log="\n".join(log_lines))

    for iteration in range(1, MAX_REFINEMENT_ITERATIONS + 1):
        diagnosis = diagnose_undetermined(original_code, mutated_code, initial_sequence_length)
        diagnoses.append(diagnosis)
        log_lines.append(f"Diagnosis: {diagnosis.category} -- {diagnosis.evidence}")

        if diagnosis.category != "insufficient_scan_depth":
            log_lines.append("No fixable deficiency identified -- stopping (undetermined stands).")
            break

        new_depth = diagnosis.evidence["computed_min_depth"]
        log_lines.append(f"Selected action: {diagnosis.selected_action} (resolved_by=precheck, no LLM)")

        result = run_distinguish_search(original_code, mutated_code, library_content,
                                         sequence_length=new_depth)
        log_lines.append(f"Iteration {iteration} (sequence_length={new_depth}): {result.status}"
                          + (f" at scan {result.witness_depth}" if result.witness_depth else ""))

        if result.status != "undetermined":
            break

    return RefinementResult(final_result=result, iterations=len(diagnoses), diagnoses=diagnoses,
                             log="\n".join(log_lines))
