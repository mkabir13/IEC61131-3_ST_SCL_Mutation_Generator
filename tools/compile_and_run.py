"""
compile_and_run.py -- ONE script that runs the full Merge + Compile/Run
pipeline in sequence:

    1. python mergeSTcode.py   (merges Tests/ fragments into TestCode.st)
    2. bash statement.sh        (MATIEC compile, GCC compile, run, gcov)

This is the single entry point the dashboard's "Compile and Run" button
calls, and it's also runnable standalone from the command line:

    cd tools/
    python3 compile_and_run.py

Stops after step 1 if the merge fails -- no point compiling a stale or
broken TestCode.st.
"""

import subprocess
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent


def run_pipeline() -> tuple[bool, str]:
    """Returns (overall_ok, combined_output). combined_output contains
    clearly-labeled sections so a caller can split it for display if
    it wants separate Merge/Load panels.
    """
    sections = []

    merge_result = subprocess.run(
        [sys.executable, "mergeSTcode.py"],
        cwd=TOOLS_DIR,
        capture_output=True,
        text=True,
        timeout=30,
    )
    sections.append("=== MERGE (python mergeSTcode.py) ===")
    sections.append((merge_result.stdout or "") + (merge_result.stderr or ""))

    if merge_result.returncode != 0:
        sections.append("\nMerge failed -- stopping before compile/run.")
        return False, "\n".join(sections)

    statement_sh = TOOLS_DIR / "statement.sh"
    if not statement_sh.exists():
        sections.append(f"\nERROR: {statement_sh} not found.")
        return False, "\n".join(sections)

    try:
        statement_result = subprocess.run(
            ["bash", str(statement_sh)],
            cwd=TOOLS_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired as e:
        sections.append("\n=== COMPILE / RUN (statement.sh) ===")
        sections.append(f"statement.sh timed out: {e}")
        return False, "\n".join(sections)

    sections.append("\n=== COMPILE / RUN (statement.sh) ===")
    sections.append((statement_result.stdout or "") + (statement_result.stderr or ""))

    return statement_result.returncode == 0, "\n".join(sections)


if __name__ == "__main__":
    ok, output = run_pipeline()
    print(output)
    sys.exit(0 if ok else 1)
