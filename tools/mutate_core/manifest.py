"""
mutate_core/manifest.py — lightweight result record for a mutation
campaign. No DB — this campaign runs as a batch job and writes
Output/manifest.json + Output/summary.csv when done.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
from pathlib import Path


class ValidationStatus(Enum):
    VALID = "valid"                      # compiled with MATIEC and gcc
    INVALID_MATIEC = "invalid_matiec"    # MATIEC rejected it (syntax/type/semantic)
    INVALID_BUILD = "invalid_build"      # MATIEC ok, gcc build failed


class KillStatus(Enum):
    KILLED_ASSERTION = "killed_assertion"   # a FAIL marker appeared in stdout
    KILLED_DIVERGED = "killed_diverged"     # stdout differs from baseline, no explicit marker
    SURVIVED = "survived"                   # stdout matches baseline, no FAIL marker
    NOT_RUN = "not_run"                     # never reached execution (invalid mutant)
    TIMED_OUT = "timed_out"                 # baseline itself timed out — can't classify


@dataclass
class MutantResult:
    mutant_id: str
    operator_id: str
    operator_family: str
    original_snippet: str
    mutated_snippet: str
    validation_status: ValidationStatus
    kill_status: KillStatus = KillStatus.NOT_RUN
    matiec_stderr: str = ""
    gcc_stderr: str = ""
    run_stdout: str = ""
    run_stderr: str = ""
    timed_out: bool = False
    coverage_summary: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["validation_status"] = self.validation_status.value
        d["kill_status"] = self.kill_status.value
        return d


@dataclass
class CampaignManifest:
    program_name: str
    baseline_stdout: str = ""
    results: list[MutantResult] = field(default_factory=list)

    def add(self, result: MutantResult) -> None:
        self.results.append(result)

    def mutation_score(self) -> float:
        runnable = [r for r in self.results if r.validation_status == ValidationStatus.VALID]
        if not runnable:
            return 0.0
        killed = [r for r in runnable if r.kill_status in
                  (KillStatus.KILLED_ASSERTION, KillStatus.KILLED_DIVERGED)]
        return len(killed) / len(runnable)

    def write_json(self, path: Path) -> None:
        payload = {
            "program_name": self.program_name,
            "mutation_score": round(self.mutation_score(), 3),
            "baseline_stdout": self.baseline_stdout,
            "results": [r.to_dict() for r in self.results],
        }
        path.write_text(json.dumps(payload, indent=2))

    def write_csv(self, path: Path) -> None:
        import csv
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["mutant_id", "operator_id", "operator_family",
                              "validation_status", "kill_status", "mutated_snippet"])
            for r in self.results:
                writer.writerow([r.mutant_id, r.operator_id, r.operator_family,
                                  r.validation_status.value, r.kill_status.value,
                                  r.mutated_snippet])
