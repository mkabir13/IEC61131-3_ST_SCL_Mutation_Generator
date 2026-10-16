"""
config.py — paths and constants for the mutation-testing tool.

Assumes the tool lives at <project_root>/tools/, alongside matiec/, Tests/,
Output/, and log/ — exactly your existing layout:

    mutate/
    ├── matiec/
    ├── Output/
    ├── Tests/
    ├── log/            (created if missing)
    └── tools/          <- this package lives here
"""

from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MATIEC_DIR = PROJECT_ROOT / "matiec"
MATIEC_BIN = MATIEC_DIR / "iec2c"     # run with cwd=MATIEC_DIR, exactly as statement.sh does
MATIEC_LIB_DIR = "lib"                # relative to MATIEC_DIR, per your existing `-I lib`
MATIEC_C_RUNTIME_DIR = MATIEC_DIR / "lib" / "C"

TESTS_DIR = PROJECT_ROOT / "Tests"
OUTPUT_DIR = PROJECT_ROOT / "Output"
OUTPUT_RESULT_DIR = OUTPUT_DIR / "result"
LOG_DIR = PROJECT_ROOT / "log"

MERGED_ST_FILENAME = "TestCode.st"

# Where the dashboard saves every generated mutant's ST source as its own
# file, for inspection/reuse outside the dashboard.
MUTATED_CODE_DIR = TESTS_DIR / "mutatedCode"

# Where the SCL button saves SCL-formatted copies of the mutants
# (Tests/mutatedCode/scl/). Only written when the SCL button is pressed;
# the normal .st files in MUTATED_CODE_DIR are unaffected either way.
SCL_CODE_DIR = MUTATED_CODE_DIR / "scl"

# Names from Config.txt's CONFIGURATION/RESOURCE declarations -- used to
# build the right .c filenames for gcc (CLI campaign tool only; the
# dashboard doesn't need gcc).
CONFIG_NAME = "Config0"
RESOURCE_NAME = "Res0"

RUN_TIMEOUT_SECONDS = 5

# Kill-detection markers your test FBs can print. Case-sensitive substring
# match against stdout.
FAIL_MARKERS = ["FAIL"]
PASS_MARKERS = ["PASS"]

_NUMBERED_FILE_RE = re.compile(r"^(\d+)[\s_.-]+(.+)$")


def discover_tests_layout() -> tuple[list[str], str]:
    """Scans TESTS_DIR for numbered ST source fragments (e.g.
    "1 Library.txt", "2 mutatecode.txt", "3 Programcontroller.txt",
    "4 Config.txt") and returns (ordered_filenames, code_slot_filename) --
    the merge order by numeric prefix, and which one of those files is the
    "code under test" slot (identified by "mutatecode" or "originalcode"
    appearing in its name, case-insensitive).

    Computed fresh on every call (not cached), so renaming, adding, or
    renumbering files in Tests/ takes effect immediately without editing
    this file or restarting anything -- this replaces an earlier hardcoded
    filename list that broke every time the numbering changed.

    Excludes MERGED_ST_FILENAME (the merge OUTPUT, never an input) and any
    file with no numeric prefix (template.st, INCLUDE.st, etc. are treated
    as auxiliary, not part of the automatic merge).
    """
    numbered: list[tuple[int, str]] = []
    for path in TESTS_DIR.iterdir():
        if not path.is_file() or path.name == MERGED_ST_FILENAME:
            continue
        m = _NUMBERED_FILE_RE.match(path.name)
        if m:
            numbered.append((int(m.group(1)), path.name))

    numbered.sort(key=lambda pair: pair[0])
    ordered_filenames = [name for _, name in numbered]

    if not ordered_filenames:
        raise FileNotFoundError(
            f"No numbered ST source files found in {TESTS_DIR} (expected "
            f"files like '1 Library.txt', '2 mutatecode.txt', etc.)."
        )

    slot_candidates = [
        name for name in ordered_filenames
        if "mutatecode" in name.lower() or "originalcode" in name.lower()
    ]
    if not slot_candidates:
        raise FileNotFoundError(
            f"Found numbered files {ordered_filenames} in {TESTS_DIR}, but "
            f"none of their names contain 'mutatecode' or 'originalcode' -- "
            f"can't tell which one is the code-under-test slot. Rename the "
            f"file that holds your PLC program under test to include "
            f"'mutatecode' or 'originalcode' in its name."
        )

    return ordered_filenames, slot_candidates[0]
