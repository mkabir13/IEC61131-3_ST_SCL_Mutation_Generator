"""
experiment_log.py -- writes the structured log/ directory:

    log/
    ├── experiments/    one JSON summary per run, never overwritten
    ├── mutations/       one .st file per generated mutant (this run)
    ├── compilation/     one .txt per real Load (statement.sh) run
    └── errors/          copies of only FAILED Load runs, for quick review

Each run gets its own timestamped subfolder, so nothing from a previous
experiment is ever overwritten.
"""

from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

from dashboard.mutate_service import PROJECT_ROOT

LOG_ROOT = PROJECT_ROOT / "log"


def _run_dir(base: Path, submission_id: int) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    d = base / f"submission_{submission_id}_{timestamp}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def log_generation(
    *,
    submission_id: int,
    name: str,
    original_code: str,
    categories_selected: list[str],
    mutant_results: list[dict],
) -> Path:
    """Called once, right after "Generate Mutations" produces its batch.
    Records what was generated -- NOT compile/run status, since nothing
    has been compiled or run yet at this point.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    mutations_dir = _run_dir(LOG_ROOT / "mutations", submission_id)
    experiments_dir = LOG_ROOT / "experiments"
    experiments_dir.mkdir(parents=True, exist_ok=True)

    (mutations_dir / "original.st").write_text(original_code, encoding="utf-8")
    for r in mutant_results:
        (mutations_dir / f"{r['display_id']}.st").write_text(r["mutated_code"], encoding="utf-8")

    summary = {
        "experiment_id": submission_id,
        "timestamp": timestamp,
        "name": name,
        "mutation_categories_used": categories_selected,
        "num_mutations_generated": len(mutant_results),
        "mutations_dir": str(mutations_dir),
    }
    summary_path = experiments_dir / f"experiment_{submission_id}_{timestamp.replace(':', '-')}.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary_path


def log_compile_run(*, submission_id: int, mutant_display_id: str, ok: bool, output: str) -> Path:
    """Called once per "Compile and Run" click -- records the full
    combined mergeSTcode.py + statement.sh output for that mutant.
    Written to compilation/ always, and additionally to errors/ if it failed.
    """
    compilation_dir = _run_dir(LOG_ROOT / "compilation", submission_id)
    log_text = (
        f"Submission: {submission_id}\nMutant: {mutant_display_id}\nResult: "
        f"{'SUCCESS' if ok else 'FAILED'}\n\n{output}\n"
    )
    path = compilation_dir / f"{mutant_display_id}_compile_run.txt"
    path.write_text(log_text, encoding="utf-8")

    if not ok:
        errors_dir = _run_dir(LOG_ROOT / "errors", submission_id)
        (errors_dir / f"{mutant_display_id}_compile_run.txt").write_text(log_text, encoding="utf-8")

    return path
