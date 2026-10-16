"""
distinguish_search.py -- Task 1.3's DistinguishSearch from the AgenTest-ST
paper, scoped to what's actually buildable against this project's real
MATIEC/gcc toolchain, and empirically fixed after discovering a real bug:
MATIEC's bundled plc.c/accessor.h defines __INIT_LOCATED as a no-op, so
located-variable (%QX/%QW) values are NEVER actually linked to program
data in this harness -- the auto-dump silently prints stale/uninitialized
values regardless of real program state. Confirmed by testing a variable
that toggles every scan and observing the "located variables" dump never
changed. Not something fixable by changing our own ST source; it's a gap
in the bundled matiec/tests/plc.c reference harness itself.

What this uses INSTEAD (proven reliable earlier in this project): ST-level
IF/ELSE choosing between two hardcoded printf strings inside a `{ }` inline
C block. Inline C blocks can't reference ST variable VALUES directly, but
choosing which of two fixed strings to print based on a real ST boolean
expression works correctly (this is exactly how PASS/FAIL detection works
elsewhere in tools/). Every BOOL output gets one such IF per scan, printing
a distinctly prefixed marker line -- these are parsed back into a per-scan
state vector for ORIGINAL vs MUTANT comparison.

Scope, stated plainly:
  - Only BOOL VAR_INPUT variables are searched/varied (candidate
    sequences). Non-BOOL inputs are held at a fixed default.
  - Only BOOL VAR_OUTPUT variables are observed/compared. INT/other
    output types are not part of the comparison (no reliable equivalent
    of the marker trick for arbitrary integer values without knowing
    candidate thresholds in advance).
  - Two candidate strategies: a "sustained true" PLC-targeted pattern
    (good for timers/edges) and a few seeded random toggle sequences.
    No coverage-guided fuzzing (needs a seed-trace corpus, out of scope).
  - Reports killed (with witness scan depth + which strategy found it) or
    undetermined within budget. No coverage/mutation-score-interval
    reporting (that's Thrust 3, a separate, larger piece of the paper).
"""

from __future__ import annotations
import math
import random
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import config as mutate_config
from dashboard.mutate_service import scan_structure, StructureSummary

SCAN_PERIOD_MS = 100
DEFAULT_SEQUENCE_LENGTH = 30          # scans -> 3s of simulated time per run
RANDOM_CANDIDATE_COUNT = 3
RANDOM_SEED_BASE = 12345
MARKER_PREFIX = "MUT_OBS:"


@dataclass
class DistinguishResult:
    status: str                    # "killed" | "undetermined" | "error"
    witness_depth: int | None = None
    strategy: str | None = None
    original_trace: list[dict] = field(default_factory=list)
    mutant_trace: list[dict] = field(default_factory=list)
    log: str = ""


class DistinguishSearchError(Exception):
    pass


def _bool_literal(v: bool) -> str:
    return "TRUE" if v else "FALSE"


def _fb_interface(structure: StructureSummary) -> tuple[list[str], list[tuple[str, str]], list[str]]:
    bool_inputs = [n for n, t, s in structure.variables if s == "VAR_INPUT" and t == "BOOL"]
    other_inputs = [(n, t) for n, t, s in structure.variables if s == "VAR_INPUT" and t != "BOOL"]
    bool_outputs = [n for n, t, s in structure.variables if s == "VAR_OUTPUT" and t == "BOOL"]
    return bool_inputs, other_inputs, bool_outputs


def _build_driver_program(
    fb_name: str,
    bool_inputs: list[str],
    other_inputs: list[tuple[str, str]],
    bool_outputs: list[str],
    sequence_length: int,
    input_sequence: dict[str, list[bool]],
) -> str:
    if not bool_outputs:
        raise DistinguishSearchError(
            "No BOOL VAR_OUTPUT found -- DistinguishSearch currently only "
            "observes boolean outputs, and this FB has none."
        )

    call_args = []
    for name in bool_inputs:
        call_args.append(f"{name} := {name}_seq[idx]")
    for name, type_name in other_inputs:
        call_args.append(f"{name} := {'FALSE' if type_name == 'BOOL' else '0'}")

    seq_decls = "\n".join(
        f"  {name}_seq : ARRAY[1..{sequence_length}] OF BOOL := "
        f"[{', '.join(_bool_literal(v) for v in input_sequence[name])}];"
        for name in bool_inputs
    )

    marker_blocks = "\n".join(
        f"IF UUT.{name} THEN\n"
        f'  {{printf("{MARKER_PREFIX}{name}=1\\n");}}\n'
        f"ELSE\n"
        f'  {{printf("{MARKER_PREFIX}{name}=0\\n");}}\n'
        f"END_IF;"
        for name in bool_outputs
    )

    return f"""PROGRAM DistinguishRunner
VAR
  UUT : {fb_name};
  idx : INT := 1;
{seq_decls}
END_VAR
UUT({', '.join(call_args)});
{marker_blocks}
IF idx < {sequence_length} THEN
  idx := idx + 1;
END_IF;
END_PROGRAM

CONFIGURATION {mutate_config.CONFIG_NAME}
  RESOURCE {mutate_config.RESOURCE_NAME} ON PLC
    TASK task0(INTERVAL := T#{SCAN_PERIOD_MS}ms, PRIORITY := 0);
    PROGRAM instance0 WITH task0 : DistinguishRunner;
  END_RESOURCE
END_CONFIGURATION
"""


def _strategy_sustained_true(bool_inputs: list[str], length: int) -> dict[str, list[bool]]:
    return {name: [True] * length for name in bool_inputs}


def _strategy_random(bool_inputs: list[str], length: int, seed: int) -> dict[str, list[bool]]:
    rng = random.Random(seed)
    return {name: [rng.choice([True, False]) for _ in range(length)] for name in bool_inputs}


def _compile_and_run(merged_source: str, timeout_seconds: int) -> tuple[bool, str, str]:
    """Compiles+runs `merged_source` fresh, in an isolated temp directory --
    never touches the real Tests/Output/ directories. Returns
    (ok, stdout, diagnostic_log).
    """
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        src_path = td_path / "search.st"
        src_path.write_text(merged_source, encoding="utf-8")

        matiec_result = subprocess.run(
            [str(mutate_config.MATIEC_BIN), "-Ol", "-I", mutate_config.MATIEC_LIB_DIR,
             str(src_path), "-T", str(td_path)],
            cwd=mutate_config.MATIEC_DIR,
            capture_output=True, text=True, timeout=30,
        )
        if matiec_result.returncode != 0:
            return False, "", f"MATIEC compile failed:\n{matiec_result.stderr}"

        shutil.copy(mutate_config.PROJECT_ROOT / "tools" / "runtime_patch" / "main.c", td_path / "main.c")
        shutil.copy(mutate_config.PROJECT_ROOT / "tools" / "runtime_patch" / "plc.c", td_path / "plc.c")
        shutil.copy(mutate_config.PROJECT_ROOT / "tools" / "runtime_patch" / "iec_lib_math.c",
                    td_path / "iec_lib_math.c")

        sources = [f"{mutate_config.CONFIG_NAME}.c", f"{mutate_config.RESOURCE_NAME}.c", "plc.c", "main.c",
                   "iec_lib_math.c"]
        missing = [s for s in sources if not (td_path / s).exists()]
        if missing:
            return False, "", f"MATIEC did not generate expected files: {missing}"

        gcc_result = subprocess.run(
            ["gcc", "-I", str(mutate_config.MATIEC_C_RUNTIME_DIR), *sources, "-o", "search_runner", "-lm"],
            cwd=td_path, capture_output=True, text=True, timeout=30,
        )
        if gcc_result.returncode != 0:
            return False, "", f"GCC compile failed:\n{gcc_result.stderr}"

        try:
            run_result = subprocess.run(
                ["stdbuf", "-oL", "./search_runner"],
                cwd=td_path, capture_output=True, text=True, timeout=timeout_seconds,
            )
            stdout = run_result.stdout
        except subprocess.TimeoutExpired as e:
            stdout = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")

        return True, stdout, ""


_MARKER_RE = re.compile(re.escape(MARKER_PREFIX) + r"(\w+)=([01])")


def _parse_marker_trace(output: str, bool_outputs: list[str]) -> list[dict[str, str]]:
    """Each scan prints exactly len(bool_outputs) marker lines, in a fixed
    order -- chunk the flat list of matches into per-scan groups.
    """
    matches = _MARKER_RE.findall(output)
    n = len(bool_outputs)
    if n == 0:
        return []
    scans = []
    for i in range(0, len(matches) - n + 1, n):
        chunk = matches[i:i + n]
        scans.append({name: value for name, value in chunk})
    return scans


def _first_divergence(original_trace: list[dict], mutant_trace: list[dict]) -> int | None:
    for i, (o, m) in enumerate(zip(original_trace, mutant_trace), start=1):
        if o != m:
            return i
    return None


def run_distinguish_search(
    original_code: str,
    mutated_code: str,
    library_content: str,
    sequence_length: int = DEFAULT_SEQUENCE_LENGTH,
) -> DistinguishResult:
    structure = scan_structure(original_code)
    if structure.pou_type != "FUNCTION_BLOCK" or not structure.pou_name:
        raise DistinguishSearchError(
            "DistinguishSearch needs a FUNCTION_BLOCK with a detected name -- "
            f"got POU type {structure.pou_type!r}."
        )

    bool_inputs, other_inputs, bool_outputs = _fb_interface(structure)
    if not bool_inputs:
        raise DistinguishSearchError(
            "No BOOL VAR_INPUT found -- DistinguishSearch currently only "
            "searches over boolean inputs, and this FB has none."
        )
    if not bool_outputs:
        raise DistinguishSearchError(
            "No BOOL VAR_OUTPUT found -- DistinguishSearch currently only "
            "observes boolean outputs, and this FB has none."
        )

    strategies: list[tuple[str, dict[str, list[bool]]]] = [
        ("sustained_true", _strategy_sustained_true(bool_inputs, sequence_length)),
    ]
    for i in range(RANDOM_CANDIDATE_COUNT):
        strategies.append((f"random_{i}", _strategy_random(bool_inputs, sequence_length, RANDOM_SEED_BASE + i)))

    log_lines = [f"FB: {structure.pou_name}  BOOL inputs: {bool_inputs}  BOOL outputs observed: {bool_outputs}"]

    for strategy_name, sequence in strategies:
        driver = _build_driver_program(structure.pou_name, bool_inputs, other_inputs, bool_outputs,
                                        sequence_length, sequence)
        # A multiplicative buffer (e.g. "times 1.3") scales the WHOLE
        # window, not just startup overhead -- a "30-scan" request would
        # actually observe ~40 scans, silently widening every search
        # budget and defeating the diagnostician's whole premise (it
        # needs sequence_length to mean what it says). Small additive
        # buffer instead: enough for process startup, not proportional.
        timeout = max(1, math.ceil(sequence_length * SCAN_PERIOD_MS / 1000 + 0.5))

        orig_merged = f"{library_content}\n{original_code}\n{driver}"
        mut_merged = f"{library_content}\n{mutated_code}\n{driver}"

        orig_ok, orig_stdout, orig_err = _compile_and_run(orig_merged, timeout)
        if not orig_ok:
            log_lines.append(f"[{strategy_name}] original failed to compile/build: {orig_err}")
            continue
        mut_ok, mut_stdout, mut_err = _compile_and_run(mut_merged, timeout)
        if not mut_ok:
            log_lines.append(f"[{strategy_name}] mutant failed to compile/build: {mut_err}")
            continue

        orig_trace = _parse_marker_trace(orig_stdout, bool_outputs)
        mut_trace = _parse_marker_trace(mut_stdout, bool_outputs)
        depth = _first_divergence(orig_trace, mut_trace)

        log_lines.append(
            f"[{strategy_name}] {len(orig_trace)} scan(s) observed -- "
            f"{'DIVERGED at scan ' + str(depth) if depth else 'no divergence'}"
        )

        if depth is not None:
            return DistinguishResult(
                status="killed", witness_depth=depth, strategy=strategy_name,
                original_trace=orig_trace, mutant_trace=mut_trace,
                log="\n".join(log_lines),
            )

    return DistinguishResult(status="undetermined", log="\n".join(log_lines))
