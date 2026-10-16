"""
mutate_service.py -- bridges the dashboard to your existing tools/ package
(mutate_core operators, MATIEC paths) without modifying anything in tools/.

Compile-only, not the full gcc/execution pipeline in tools/run_mutation_campaign.py
-- deliberately skips gcc/gcov/run to stay fast and dependency-light: only a
working matiec/iec2c binary is needed, not a C toolchain.
"""

from __future__ import annotations
import difflib
import html
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

DASHBOARD_DIR = Path(__file__).resolve().parent      # tools/dashboard
TOOLS_DIR = DASHBOARD_DIR.parent                       # tools/  (dashboard/ now lives inside it)
PROJECT_ROOT = TOOLS_DIR.parent                         # mutate/  (sibling of matiec/, Tests/, Output/, log/)

if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import config as mutate_config  # noqa: E402  (tools/config.py -- reused as-is)
from mergeSTcode import merge_st_files  # noqa: E402  (tools/mergeSTcode.py -- reused as-is)
from mutate_core.operators import (  # noqa: E402
    generate_all_candidates, parse_declarations, CATEGORIES,
)


def _run_matiec(text: str) -> tuple[bool, str]:
    """Compiles `text` (already-merged, ready-to-compile ST source) via the
    real MATIEC binary configured in tools/config.py. Returns (ok, stderr).
    """
    with tempfile.TemporaryDirectory() as td:
        src_path = Path(td) / "submission.st"
        src_path.write_text(text, encoding="utf-8")
        result = subprocess.run(
            [str(mutate_config.MATIEC_BIN), "-Ol", "-I", mutate_config.MATIEC_LIB_DIR, str(src_path)],
            cwd=mutate_config.MATIEC_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
    return result.returncode == 0, result.stderr


def compile_via_project_harness(source_text: str) -> tuple[bool, str]:
    """Quick validity check ONLY -- used for Step 1 (does the originally
    submitted code compile at all, in the context of your real Library/
    Programcontroller/Config), via an in-memory merge. Does NOT touch
    Tests/2 mutatecode.txt or run mergeSTcode.py/statement.sh -- see
    write_to_mutatecode_slot() / run_compile_and_run() for the real,
    on-disk pipeline used from Generate Mutations onward.
    """
    try:
        merged = merge_st_files(original_code_override=source_text)
    except FileNotFoundError as e:
        return False, (
            f"Missing required Tests/ harness file: {e.filename}\n\n"
            f"The dashboard compiles submitted code through your project's real "
            f"merge (tools/config.py's discover_tests_layout(), based on numbered "
            f"files in Tests/). Make sure your Library/Programcontroller/Config "
            f"files are present and numbered."
        )
    return _run_matiec(merged)


def write_to_mutatecode_slot(source_text: str) -> Path:
    """Writes `source_text` into whichever file discover_tests_layout()
    identifies as the code-under-test slot (e.g. "2 mutatecode.txt") --
    the real on-disk file mergeSTcode.py reads by default. This is the one
    file mutants are allowed to overwrite; the ORIGINAL submitted code is
    never touched here (see save_original_file()).
    """
    _merge_order, code_slot_filename = mutate_config.discover_tests_layout()
    mutate_config.TESTS_DIR.mkdir(parents=True, exist_ok=True)
    slot_path = mutate_config.TESTS_DIR / code_slot_filename
    slot_path.write_text(source_text, encoding="utf-8")
    return slot_path


def run_compile_and_run() -> tuple[bool, str]:
    """Runs the REAL tools/compile_and_run.py as a subprocess -- ONE
    Python file that itself runs mergeSTcode.py then statement.sh in
    sequence. This is the single action behind the dashboard's
    "Compile and Run" button.
    """
    script = TOOLS_DIR / "compile_and_run.py"
    if not script.exists():
        return False, f"tools/compile_and_run.py not found at {script}"

    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=TOOLS_DIR,
        capture_output=True,
        text=True,
        timeout=150,
    )
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode == 0, output


def save_original_file(source_text: str) -> Path:
    """Saves the originally submitted ST code (unmutated) to its own file
    in Tests/, separate from the dynamic "2 mutatecode.txt" slot, so the
    as-submitted version is always available even after mutants have
    overwritten that slot.
    """
    mutate_config.TESTS_DIR.mkdir(parents=True, exist_ok=True)
    path = mutate_config.TESTS_DIR / "original_ST_code.st"
    path.write_text(source_text, encoding="utf-8")
    return path


def save_mutant_file(display_id: str, mutated_code: str) -> Path:
    """Saves a generated mutant's ST source as its own file under
    Tests/mutatedCode/, so every mutant is inspectable/reusable outside the
    dashboard -- not just logged to mutate/log/.
    """
    mutate_config.MUTATED_CODE_DIR.mkdir(parents=True, exist_ok=True)
    path = mutate_config.MUTATED_CODE_DIR / f"{display_id}.st"
    path.write_text(mutated_code, encoding="utf-8")
    return path


def save_mutant_scl_file(display_id: str, mutated_code: str) -> Path:
    """Saves the SCL-formatted version of a mutant (see to_scl_style() for
    exactly what that does and doesn't change) to Tests/mutatedCode/scl/
    as <id>.scl. Only called from the SCL button -- generating mutations
    on its own never writes here, and the plain .st file in
    Tests/mutatedCode/ is left exactly as it was.
    """
    mutate_config.SCL_CODE_DIR.mkdir(parents=True, exist_ok=True)
    path = mutate_config.SCL_CODE_DIR / f"{display_id}.scl"
    path.write_text(to_scl_style(mutated_code), encoding="utf-8")
    return path


def annotate_with_comment(original: str, mutated: str, operator_id: str) -> str:
    """Inserts a `(* MUTATED: <operator_id> *)` comment at the end of the
    line containing the change, so the mutation is visible directly in the
    code -- in a text editor, not just as color in the dashboard. Comments
    are always safe to add at end-of-line in ST, so this never risks
    breaking mid-expression syntax. Skipped if the operator already
    embeds its own comment (e.g. TIMER_BYPASS), to avoid double-annotating.
    """
    prefix_len = _common_prefix_len(original, mutated)
    suffix_len = _common_suffix_len(original, mutated, prefix_len)
    change_end = len(mutated) - suffix_len
    mut_middle = mutated[prefix_len:change_end]

    if "(*" in mut_middle:
        return mutated  # operator already added its own comment

    newline_pos = mutated.find("\n", change_end)
    marker = f" (* MUTATED: {operator_id} *)"
    if newline_pos == -1:
        return mutated + marker
    return mutated[:newline_pos] + marker + mutated[newline_pos:]


def _common_prefix_len(a: str, b: str) -> int:
    n = 0
    limit = min(len(a), len(b))
    while n < limit and a[n] == b[n]:
        n += 1
    return n


def _common_suffix_len(a: str, b: str, prefix_len: int) -> int:
    n = 0
    limit = min(len(a), len(b)) - prefix_len
    while n < limit and a[len(a) - 1 - n] == b[len(b) - 1 - n]:
        n += 1
    return n


# ------------------------------------------------------------------
# Structure scan (requirement 2: "read and parse") -- NOT a full AST.
# MATIEC's own compile step (above) is the authoritative parser; this
# is a lightweight structural summary for display purposes.
# ------------------------------------------------------------------

@dataclass
class StructureSummary:
    pou_type: str | None
    pou_name: str | None
    variables: list[tuple[str, str, str]]  # (name, type, section)
    timers: list[tuple[str, str]]           # (name, type)
    edges: list[tuple[str, str]]            # (name, type)
    if_count: int
    loop_count: int
    assignment_count: int
    warnings: list[str] = field(default_factory=list)


_VAR_SECTION_RE = re.compile(
    r"\b(VAR_INPUT|VAR_OUTPUT|VAR_IN_OUT|VAR)\b(.*?)END_VAR", re.S
)
_DECL_RE = re.compile(r"(\w+)\s*:\s*(\w+)\s*(?::=[^;]+)?;")
_POU_RE = re.compile(r"\b(FUNCTION_BLOCK|PROGRAM|FUNCTION)\s+(\w+)")
_TIMER_TYPES = {"TON", "TOF", "TP"}
_EDGE_TYPES = {"R_TRIG", "F_TRIG"}
_COUNTER_TYPES = {"CTU", "CTD", "CTUD"}


def scan_structure(text: str) -> StructureSummary:
    pou_match = _POU_RE.search(text)
    pou_type, pou_name = (pou_match.group(1), pou_match.group(2)) if pou_match else (None, None)

    variables: list[tuple[str, str, str]] = []
    for section, block in _VAR_SECTION_RE.findall(text):
        for name, type_name in _DECL_RE.findall(block):
            variables.append((name, type_name, section))

    timers = [(n, t) for n, t, _ in variables if t in _TIMER_TYPES]
    edges = [(n, t) for n, t, _ in variables if t in _EDGE_TYPES]

    if_count = len(re.findall(r"\bIF\b", text))
    loop_count = len(re.findall(r"\b(FOR|WHILE|REPEAT)\b", text))
    # Crude but honest: counts every ":=" occurrence anywhere in the file,
    # including VAR-block initializers -- a summary count, not exact
    # executable-statement semantics.
    assignment_count = len(re.findall(r":=", text))

    warnings = []
    if pou_type is None:
        warnings.append("No FUNCTION_BLOCK/PROGRAM/FUNCTION header found.")
    if not variables:
        warnings.append("No variable declarations found.")

    return StructureSummary(
        pou_type=pou_type, pou_name=pou_name, variables=variables,
        timers=timers, edges=edges, if_count=if_count,
        loop_count=loop_count, assignment_count=assignment_count,
        warnings=warnings,
    )


# ------------------------------------------------------------------
# Mutation generation
# ------------------------------------------------------------------

@dataclass
class MutantCandidateInfo:
    operator_id: str
    operator_family: str
    category: str
    location_id: str
    original_snippet: str
    mutated_snippet: str
    mutated_code: str


def parse_and_mutate(source_text: str, categories: list[str] | None = None) -> list[MutantCandidateInfo]:
    """Parses declarations and generates mutant candidates for `source_text`,
    restricted to `categories` if given (None = all categories).

    Raises ValueError if no VAR declarations are found at all -- a signal
    the submitted text likely isn't valid ST.
    """
    declarations = parse_declarations(source_text)
    if not declarations:
        raise ValueError(
            "No VAR/VAR_INPUT/VAR_OUTPUT declarations found -- this doesn't "
            "look like a valid ST FUNCTION_BLOCK or PROGRAM. Nothing to mutate."
        )

    candidates = generate_all_candidates(source_text, categories=categories)
    return [
        MutantCandidateInfo(
            operator_id=op.operator_id,
            operator_family=op.family,
            category=op.category,
            location_id=cand.location_id,
            original_snippet=cand.original_snippet,
            mutated_snippet=cand.mutated_snippet,
            mutated_code=annotate_with_comment(source_text, cand.mutated_text, op.operator_id),
        )
        for op, cand in candidates
    ]


def available_categories() -> list[tuple[str, str]]:
    return CATEGORIES


# ------------------------------------------------------------------
# Diff rendering (requirement: highlighted diff view)
# ------------------------------------------------------------------

# ------------------------------------------------------------------
# SCL-style display formatting
# ------------------------------------------------------------------
#
# Siemens' TIA Portal SCL is a distinct dialect from generic IEC 61131-3
# ST -- NOT the same thing, and unlike everything else in this project,
# there is no Siemens compiler available in this environment to verify
# against (MATIEC only understands standard IEC 61131-3 ST). This is
# deliberately scoped to the one difference that's well-established and
# genuinely safe to apply without a compiler to check against: TIA Portal
# SCL commonly uses `//` line comments where generic ST typically uses
# `(* ... *)` block comments (TIA Portal SCL actually accepts both, so
# this is a display/style convention, not a functional necessity).
#
# What this does NOT do: nothing to variable declarations, FB calls,
# operators, or block keywords -- those are unchanged because, for the
# constructs this project's operators mutate, they're already the same
# between generic IEC 61131-3 ST and TIA Portal SCL. Anything beyond
# comment style is genuinely unverified and deliberately left alone
# rather than guessed at.

_SINGLE_LINE_BLOCK_COMMENT_RE = re.compile(r"\(\*\s*(.*?)\s*\*\)")


def to_scl_style(text: str) -> str:
    """Converts single-line `(* ... *)` comments (no embedded newline) to
    `// ...` -- the one SCL-style convention applied here. Multi-line
    block comments are left as `(* ... *)` since converting each line to
    `//` would change line count/structure for no real benefit.
    """
    def _convert(match: re.Match) -> str:
        inner = match.group(1)
        if "\n" in inner:
            return match.group(0)  # leave multi-line comments untouched
        return f"// {inner}" if inner else "//"

    return _SINGLE_LINE_BLOCK_COMMENT_RE.sub(_convert, text)


def render_diff_html(original: str, mutated: str) -> str:
    """Unified-diff-style HTML: unchanged lines plain, removed lines red,
    added lines green. Escapes all code content to prevent HTML injection
    from submitted ST code.
    """
    original_lines = original.splitlines()
    mutated_lines = mutated.splitlines()
    diff = difflib.unified_diff(original_lines, mutated_lines, lineterm="")

    rows = []
    for line in diff:
        if line.startswith(("---", "+++", "@@")):
            continue
        escaped = html.escape(line[1:] if line[:1] in "+-" else line)
        if line.startswith("+"):
            rows.append(f'<div class="diff-add">+ {escaped}</div>')
        elif line.startswith("-"):
            rows.append(f'<div class="diff-remove">- {escaped}</div>')
        else:
            rows.append(f'<div class="diff-context">&nbsp;&nbsp;{escaped}</div>')

    if not rows:
        rows.append('<div class="diff-context">(no line-level difference detected)</div>')
    return "\n".join(rows)


def render_side_by_side_highlighted(original: str, mutated: str) -> tuple[str, str]:
    """Every operator here makes exactly one localized edit, so instead of
    a general-purpose diff (which can fragment into several marks when a
    short substring like "T1" or "TRUE" coincidentally recurs near the
    edit), find the longest common PREFIX and longest common SUFFIX
    between the two full files -- whatever's bracketed in between on each
    side is exactly the one true changed region, with no risk of matching
    the wrong occurrence elsewhere in the file. Returns (original_html,
    mutated_html), each the full code with that one region wrapped in a
    <mark> tag: "hl-removed" (red) in original, "hl-added" (yellow) in
    mutated. Both are pre-escaped -- render with |safe inside a <pre>.
    """
    prefix_len = _common_prefix_len(original, mutated)
    suffix_len = _common_suffix_len(original, mutated, prefix_len)

    orig_prefix, orig_middle, orig_suffix = (
        original[:prefix_len],
        original[prefix_len:len(original) - suffix_len],
        original[len(original) - suffix_len:] if suffix_len else "",
    )
    mut_prefix, mut_middle, mut_suffix = (
        mutated[:prefix_len],
        mutated[prefix_len:len(mutated) - suffix_len],
        mutated[len(mutated) - suffix_len:] if suffix_len else "",
    )

    orig_html = html.escape(orig_prefix)
    if orig_middle:
        orig_html += f'<mark class="hl-removed">{html.escape(orig_middle)}</mark>'
    orig_html += html.escape(orig_suffix)

    mut_html = html.escape(mut_prefix)
    if mut_middle:
        mut_html += f'<mark class="hl-added">{html.escape(mut_middle)}</mark>'
    mut_html += html.escape(mut_suffix)

    return orig_html, mut_html
