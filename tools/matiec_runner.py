"""
matiec_runner.py — Python port of statement.sh, callable once per mutant.

Fixes relative to the original bash script:

  1. statement.sh captures `gcc_status=$?` on the line AFTER the gcc
     command, but `set -e` is active and never disabled around that call
     (it IS disabled around the MATIEC call). A non-zero gcc exit kills the
     whole script before `gcc_status` is even read, so the "gcc failed"
     branch is unreachable. Fixed here by checking returncode directly via
     subprocess.run (no shell `set -e` involved).
  2. `mv gcc_output.txt ../Output/result/` assumes Output/result/ exists,
     but nothing creates it. Fixed: created up front.
  3. `gcov softplc-Res0.gcno` hardcodes a filename pattern that may not
     match what your gcc/gcov version actually emits. Fixed: globs for
     `*.gcno` in the output directory instead of assuming a name.
  4. All paths are absolute (via config.py) rather than relative `../`
     paths, so this works regardless of the caller's cwd.
"""

from __future__ import annotations
import glob
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

import config

RUNTIME_PATCH_DIR = Path(__file__).resolve().parent / "runtime_patch"


def ensure_runtime_harness() -> None:
    """Ensures Output/main.c and Output/plc.c exist before the first build.

    Does NOT overwrite files that already exist there — if you already have
    your own main.c/plc.c in Output/, this leaves them alone. If you're
    starting fresh, it seeds them from a corrected main.c (see
    tools/runtime_patch/main.c) and matiec's bundled tests/plc.c.

    IMPORTANT — a real bug found while building this tool: the matiec
    build's generated Config*.c defines `common_ticktime__` as
    `unsigned long long`, in NANOSECONDS. matiec's own bundled
    tests/main.c externs it as `int` and does MILLISECOND arithmetic on
    it — so the periodic scan timer ends up armed for ~100000x too long
    (a 100ms task interval becomes ~27.8 hours), and softplc never
    actually scans within any reasonable test timeout. If you already
    have your own Output/main.c and mutants aren't being detected (every
    run produces identical/empty output), check for this exact issue.
    IMPORTANT -- a real bug found while building this tool: the matiec
    build's generated Config*.c defines `common_ticktime__` as
    `unsigned long long`, in NANOSECONDS. matiec's own bundled
    tests/main.c externs it as `int` and does MILLISECOND arithmetic on
    it -- so the periodic scan timer ends up armed for ~100000x too long
    (a 100ms task interval becomes ~27.8 hours), and softplc never
    actually scans within any reasonable test timeout. If you already
    have your own Output/main.c and mutants aren't being detected (every
    run produces identical/empty output), check for this exact issue.
    tools/runtime_patch/main.c has it fixed.

    IMPORTANT #2 -- a second real bug found later (while building
    DistinguishSearch): the bundled matiec/tests/plc.c declares
    `void run()` with NO parameters, but main.c calls
    `run(CURRENT_TIME.tv_sec, CURRENT_TIME.tv_nsec)`. C's old-style empty
    `()` doesn't enforce argument count, so those values were silently
    discarded -- the global `__CURRENT_TIME` that TON/TOF/TP/etc. read to
    compute elapsed time was NEVER updated. Every timer-dependent
    FUNCTION_BLOCK never saw its preset elapse, regardless of preset
    value or how long the program ran (confirmed: T#1S through T#5S all
    never fired, even after 15+ real seconds). This means any earlier
    TIMER_PRESET_CHANGE mutation-kill results from before this fix are
    unreliable -- they were being killed via a stuck-forever side effect,
    not a real preset-timing difference. tools/runtime_patch/plc.c has
    this fixed (accepts and applies the real elapsed time); seeded here
    instead of the stock matiec/tests/plc.c.
    """
    output_main = config.OUTPUT_DIR / "main.c"
    output_plc = config.OUTPUT_DIR / "plc.c"

    if not output_main.exists():
        shutil.copy(RUNTIME_PATCH_DIR / "main.c", output_main)
        print(f"Seeded {output_main} from tools/runtime_patch/main.c (ns/ms fix applied).")

    if not output_plc.exists():
        shutil.copy(RUNTIME_PATCH_DIR / "plc.c", output_plc)
        print(f"Seeded {output_plc} from tools/runtime_patch/plc.c (__CURRENT_TIME fix applied).")


@dataclass
class RunResult:
    matiec_ok: bool = False
    matiec_stderr: str = ""
    build_ok: bool = False
    gcc_stderr: str = ""
    run_stdout: str = ""
    run_stderr: str = ""
    timed_out: bool = False
    coverage_summary: str = ""


def rotate_log(path: Path) -> None:
    if path.exists():
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        path.rename(path.with_name(f"{path.name}.{timestamp}.bak"))


def clean_output_dir() -> None:
    """Equivalent of statement.sh STEP 1."""
    patterns = [
        "POUS.*", "LOCATED_VARIABLES.h", "VARIABLES.csv",
        f"{config.RESOURCE_NAME}.c", f"{config.CONFIG_NAME}.*",
        "*.html", "*.css", "*.gcov", "*.o", "*.gcno", "*.gcda",
        "softplc", "out", "coverage*",
    ]
    for pattern in patterns:
        for p in config.OUTPUT_DIR.glob(pattern):
            if p.is_file():
                p.unlink()


def compile_with_matiec(merged_st_path: Path) -> tuple[bool, str]:
    """STEP 3: run iec2c from within the matiec dir, exactly as
    statement.sh does (`cd matiec && ./iec2c -Ol -I lib <path>`),
    but with an absolute path to the merged file so cwd doesn't matter.
    """
    result = subprocess.run(
        [str(config.MATIEC_BIN), "-Ol", "-I", config.MATIEC_LIB_DIR, str(merged_st_path)],
        cwd=config.MATIEC_DIR,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0, result.stderr


def move_generated_files() -> None:
    """STEP 4: move MATIEC's generated .h/.c/.csv from the matiec dir
    into Output/ (mirrors `mv *.h ../Output/` etc. in statement.sh).
    """
    for pattern in ("*.h", "*.c", "*.csv"):
        for p in config.MATIEC_DIR.glob(pattern):
            shutil.move(str(p), str(config.OUTPUT_DIR / p.name))


def build_with_gcc() -> tuple[bool, str]:
    """STEP 6: compile the generated C with coverage instrumentation."""
    config.OUTPUT_RESULT_DIR.mkdir(parents=True, exist_ok=True)  # bug fix #2

    # iec_lib_math.c: MATIEC declares 12 iec_lib_* math functions
    # (LN/LOG/EXP/SIN/COS/TAN/ASIN/ACOS/ATAN/SQRT/MOD/POW) but never
    # defines them in the bundled reference harness -- link fails the
    # first time a program uses any of them. Auto-seed the fix.
    output_math = config.OUTPUT_DIR / "iec_lib_math.c"
    if not output_math.exists():
        shutil.copy(RUNTIME_PATCH_DIR / "iec_lib_math.c", output_math)

    sources = [f"{config.CONFIG_NAME}.c", f"{config.RESOURCE_NAME}.c", "plc.c", "main.c", "iec_lib_math.c"]
    missing = [s for s in sources if not (config.OUTPUT_DIR / s).exists()]
    if missing:
        return False, f"Missing expected generated source files: {missing}"

    result = subprocess.run(
        ["gcc", "-I", str(config.MATIEC_C_RUNTIME_DIR),
         "-fprofile-arcs", "-ftest-coverage",
         *sources, "-o", "softplc", "-lm"],
        cwd=config.OUTPUT_DIR,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0, result.stderr  # bug fix #1: no reliance on `set -e`


def run_softplc(timeout_seconds: int = config.RUN_TIMEOUT_SECONDS) -> tuple[str, str, bool]:
    """STEP 7: run the compiled softPLC binary for a bounded window.

    Uses `stdbuf -oL` (as your original statement.sh did) to force
    line-buffered stdout — without it, printf output can sit in the
    process's internal buffer and be lost entirely when the timeout
    kills the process, which would make every mutant look identical
    (empty output) regardless of behavior.
    """
    try:
        result = subprocess.run(
            ["stdbuf", "-oL", "./softplc"],
            cwd=config.OUTPUT_DIR,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        return result.stdout, result.stderr, False
    except subprocess.TimeoutExpired as e:
        stdout = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
        return stdout, stderr, True


def generate_coverage_summary() -> str:
    """STEP 8: run gcov against whatever .gcno files actually exist
    (bug fix #3 — no assumption about naming)."""
    gcno_files = glob.glob(str(config.OUTPUT_DIR / "*.gcno"))
    if not gcno_files:
        return "no .gcno files found"

    lines = []
    for gcno in gcno_files:
        base = Path(gcno).stem  # e.g. "Res0"
        result = subprocess.run(
            ["gcov", base], cwd=config.OUTPUT_DIR, capture_output=True, text=True,
        )
        for line in result.stdout.splitlines():
            if "Lines executed" in line:
                lines.append(f"{base}: {line.strip()}")
    return "; ".join(lines) if lines else "gcov produced no line-coverage summary"


def compile_build_run(merged_st_path: Path) -> RunResult:
    """Runs the full pipeline once for one merged ST source file."""
    ensure_runtime_harness()
    result = RunResult()

    clean_output_dir()

    result.matiec_ok, result.matiec_stderr = compile_with_matiec(merged_st_path)
    if not result.matiec_ok:
        return result

    move_generated_files()

    result.build_ok, result.gcc_stderr = build_with_gcc()
    if not result.build_ok:
        return result

    result.run_stdout, result.run_stderr, result.timed_out = run_softplc()
    result.coverage_summary = generate_coverage_summary()
    return result


def archive_iteration_logs(iteration: int, result: RunResult) -> None:
    """Mirrors statement.sh's per-iteration log rotation into log/iter_N/."""
    iter_dir = config.LOG_DIR / f"iter_{iteration}"
    iter_dir.mkdir(parents=True, exist_ok=True)
    (iter_dir / "matiec_stderr.txt").write_text(result.matiec_stderr)
    (iter_dir / "gcc_stderr.txt").write_text(result.gcc_stderr)
    (iter_dir / "runtime_stdout.txt").write_text(result.run_stdout)
    (iter_dir / "runtime_stderr.txt").write_text(result.run_stderr)
    (iter_dir / "coverage_summary.txt").write_text(result.coverage_summary)
