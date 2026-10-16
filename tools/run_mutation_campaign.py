"""
run_mutation_campaign.py — generates mutants from "2 Originalcode.txt",
compiles+builds+runs each one through the real MATIEC/gcc/gcov pipeline,
and classifies each as killed or survived by comparing against a baseline
run of the unmutated program.

Usage:
    cd tools/
    python3 run_mutation_campaign.py

Output:
    Output/manifest.json   — full structured results
    Output/summary.csv     — one row per mutant
    log/iter_<N>/           — per-mutant compile/build/run logs (as before)
"""

from pathlib import Path

import config
from mergeSTcode import merge_st_files
from matiec_runner import compile_build_run, archive_iteration_logs
from mutate_core import (
    CampaignManifest, MutantResult, ValidationStatus, KillStatus,
    generate_all_candidates,
)


def classify(run_stdout: str, baseline_stdout: str) -> KillStatus:
    if any(marker in run_stdout for marker in config.FAIL_MARKERS):
        return KillStatus.KILLED_ASSERTION
    if run_stdout != baseline_stdout:
        return KillStatus.KILLED_DIVERGED
    return KillStatus.SURVIVED


def main() -> None:
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    _merge_order, code_slot_filename = config.discover_tests_layout()
    original_path = config.TESTS_DIR / code_slot_filename
    original_text = original_path.read_text(encoding="utf-8")

    manifest = CampaignManifest(program_name=original_path.stem)

    # --- Baseline run (unmutated program) ---
    print("Running baseline (unmutated program)...")
    baseline_merged = merge_st_files()
    (config.TESTS_DIR / config.MERGED_ST_FILENAME).write_text(baseline_merged)
    baseline_result = compile_build_run(config.TESTS_DIR / config.MERGED_ST_FILENAME)
    archive_iteration_logs(0, baseline_result)

    if not baseline_result.matiec_ok:
        print("FATAL: baseline program does not even compile with MATIEC.")
        print(baseline_result.matiec_stderr)
        return
    if not baseline_result.build_ok:
        print("FATAL: baseline program does not build with gcc.")
        print(baseline_result.gcc_stderr)
        return
    if baseline_result.timed_out:
        print("WARNING: baseline run timed out — this is expected if your "
              "test program runs forever by design (bounded by RUN_TIMEOUT_SECONDS).")

    manifest.baseline_stdout = baseline_result.run_stdout
    print(f"Baseline OK. Coverage: {baseline_result.coverage_summary}")

    # --- Generate and run each mutant ---
    candidates = generate_all_candidates(original_text)
    print(f"Generated {len(candidates)} mutant candidate(s).")

    for i, (operator, candidate) in enumerate(candidates, start=1):
        print(f"[{i}/{len(candidates)}] {operator.operator_id} ({candidate.location_id})")

        merged = merge_st_files(original_code_override=candidate.mutated_text)
        (config.TESTS_DIR / config.MERGED_ST_FILENAME).write_text(merged)

        result = compile_build_run(config.TESTS_DIR / config.MERGED_ST_FILENAME)
        archive_iteration_logs(i, result)

        if not result.matiec_ok:
            validation_status = ValidationStatus.INVALID_MATIEC
            kill_status = KillStatus.NOT_RUN
        elif not result.build_ok:
            validation_status = ValidationStatus.INVALID_BUILD
            kill_status = KillStatus.NOT_RUN
        else:
            validation_status = ValidationStatus.VALID
            if not result.run_stdout and not manifest.baseline_stdout:
                # Neither run produced any observable output at all —
                # nothing to compare, so we genuinely can't classify this one.
                kill_status = KillStatus.TIMED_OUT
            else:
                kill_status = classify(result.run_stdout, manifest.baseline_stdout)

        manifest.add(MutantResult(
            mutant_id=candidate.location_id,
            operator_id=operator.operator_id,
            operator_family=operator.family,
            original_snippet=candidate.original_snippet,
            mutated_snippet=candidate.mutated_snippet,
            validation_status=validation_status,
            kill_status=kill_status,
            matiec_stderr=result.matiec_stderr,
            gcc_stderr=result.gcc_stderr,
            run_stdout=result.run_stdout,
            run_stderr=result.run_stderr,
            timed_out=result.timed_out,
            coverage_summary=result.coverage_summary,
        ))
        print(f"    -> {validation_status.value} / {kill_status.value}")

    manifest.write_json(config.OUTPUT_DIR / "manifest.json")
    manifest.write_csv(config.OUTPUT_DIR / "summary.csv")

    print(f"\nMutation score (killed / valid): {manifest.mutation_score():.2f}")
    print(f"Results written to {config.OUTPUT_DIR / 'manifest.json'} and "
          f"{config.OUTPUT_DIR / 'summary.csv'}")


if __name__ == "__main__":
    main()
