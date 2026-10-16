"""
Covers: ST input (saved to Tests/ as its own file) -> Generate Mutations
(mutants shown highlighted + as markdown-style code blocks in the Monitor,
saved to Tests/mutatedCode/) -> Compile and Run (ONE button, running the
real tools/compile_and_run.py, which itself runs mergeSTcode.py then
statement.sh) -- nothing mocked, all real subprocesses.
"""
import io
from pathlib import Path
import os
import json
import shutil
import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import config as mutate_config
from dashboard.app import create_app
from dashboard.extensions import db

VALID_ST = """FUNCTION_BLOCK PumpControl
VAR_INPUT
  Start : BOOL;
  Enable : BOOL;
END_VAR
VAR_OUTPUT
  Pump : BOOL;
END_VAR
VAR
  T1 : TON;
  Threshold : INT;
  Count : INT;
END_VAR
T1(IN := Start AND Enable, PT := T#3S);
IF Count > Threshold THEN
  Pump := TRUE;
END_IF;
Count := Count + 1;
Pump := T1.Q;
END_FUNCTION_BLOCK
"""

BROKEN_ST = VALID_ST.replace("T1(IN := Start AND Enable, PT := T#3S);",
                              "T1(IN := Start AND Enable, PT := T#3S)")  # missing ';'


@pytest.fixture(autouse=True, scope="module")
def seed_runtime_harness():
    """statement.sh assumes Output/main.c and Output/plc.c already exist
    (as they do on the real project) -- seed them once for this test run.
    """
    output_main = mutate_config.OUTPUT_DIR / "main.c"
    output_plc = mutate_config.OUTPUT_DIR / "plc.c"
    output_math = mutate_config.OUTPUT_DIR / "iec_lib_math.c"
    mutate_config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if not output_main.exists():
        shutil.copy(mutate_config.PROJECT_ROOT / "tools" / "runtime_patch" / "main.c", output_main)
    if not output_plc.exists():
        shutil.copy(mutate_config.PROJECT_ROOT / "tools" / "runtime_patch" / "plc.c", output_plc)
    if not output_math.exists():
        shutil.copy(mutate_config.PROJECT_ROOT / "tools" / "runtime_patch" / "iec_lib_math.c", output_math)
    yield


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
    with app.test_client() as c:
        yield c
    with app.app_context():
        db.drop_all()


def _submit(client, code=VALID_ST, name="PumpControl", categories=None):
    data = {"name": name, "original_code": code}
    if categories is not None:
        data["categories"] = categories
    return client.post("/submit", data=data, follow_redirects=True)


def _compile_and_run(client, submission_id=1):
    """Starts Compile and Run (now asynchronous -- see job_runner.py),
    waits for the background job to finish, then re-fetches the page so
    the returned response reflects the persisted result -- the initial
    redirect response only reflects the just-started state.
    """
    client.post(f"/submissions/{submission_id}/compile_and_run", data={}, follow_redirects=True)
    from dashboard import job_runner
    job = job_runner.get_job(submission_id)
    if job is not None:
        job.thread.join(timeout=60)
    return client.get(f"/submissions/{submission_id}")


def test_counter_and_latch_operators_generate_valid_mutants(client):
    """New Thrust-1 fault families added to fill a real gap against the
    paper's taxonomy: counter (CTU/CTD) and latch (SR/RS) faults, which
    weren't covered before (only timer/edge were). Both param-rename
    fixes (SR/RS and CTU/CTD use different parameter names, not just
    different semantics) verified against real MATIEC."""
    code = """FUNCTION_BLOCK CounterLatchTest
VAR_INPUT
  CountUp : BOOL;
  Reset : BOOL;
  SetIn : BOOL;
END_VAR
VAR_OUTPUT
  Done : BOOL;
  Latched : BOOL;
END_VAR
VAR
  C1 : CTU;
  L1 : SR;
END_VAR
C1(CU := CountUp, R := Reset, PV := 5);
L1(S1 := SetIn, R := Reset);
Done := C1.Q;
Latched := L1.Q1;
END_FUNCTION_BLOCK
"""
    resp = _submit(client, code=code, name="CounterLatchTest", categories=["counter_latch"])
    html = resp.data.decode()
    assert "COUNTER_THRESHOLD_CHANGE" in html
    assert "COUNTER_DIRECTION_FLIP" in html
    assert "LATCH_PRIORITY_FLIP" in html

    with client.application.app_context():
        from dashboard.models import MutantCompileResult
        mutants = MutantCompileResult.query.filter_by(submission_id=1).all()
        assert len(mutants) == 3
        # Compile each mutant standalone (not through the real Tests/
        # harness, which is built around PumpControl and would reject
        # any other FB regardless of mutation correctness -- see the
        # "unrelated program" test above). This isolates whether the
        # OPERATOR produced valid ST, which is what this test checks.
        import config as mutate_config
        import subprocess
        import tempfile
        from pathlib import Path
        for m in mutants:
            with tempfile.TemporaryDirectory() as td:
                src = Path(td) / "mutant.st"
                src.write_text(m.mutated_code)
                result = subprocess.run(
                    [str(mutate_config.MATIEC_BIN), "-Ol", "-I", mutate_config.MATIEC_LIB_DIR, str(src)],
                    cwd=mutate_config.MATIEC_DIR, capture_output=True, text=True, timeout=30,
                )
                assert result.returncode == 0, f"{m.operator_id} produced invalid ST: {result.stderr}"


def test_distinguish_search_kills_timer_bypass(client):
    """Real end-to-end test of the new DistinguishSearch feature (Task 1.3
    from the paper, scoped): TIMER_BYPASS should be found killed at
    scan 1, since it makes Pump mirror Start immediately instead of
    waiting for the timer."""
    _submit(client, categories=["timer"])
    with client.application.app_context():
        from dashboard.models import MutantCompileResult
        timer_bypass = MutantCompileResult.query.filter_by(
            submission_id=1, operator_id="TIMER_BYPASS").first()
        assert timer_bypass is not None
        mutant_id = timer_bypass.id

    resp = client.post(f"/submissions/1/mutant/{mutant_id}/distinguish", data={}, follow_redirects=True)
    html = resp.data.decode()
    assert "KILLED" in html
    assert "scan 1" in html

    with client.application.app_context():
        from dashboard.models import MutantCompileResult
        m = db.session.get(MutantCompileResult, mutant_id)
        assert m.distinguish_status == "killed"
        assert m.distinguish_depth == 1


def test_distinguish_search_refinement_recovers_undetermined_case(client):
    """Proves the C-DET diagnosis-guided refinement loop has real value,
    not just in isolation: a timer preset change large enough that the
    default search budget alone would report 'undetermined', but the
    deterministic diagnostician (paper's own K_PLC min-depth formula)
    computes a sufficient depth and the retry finds it -- reproducing the
    paper's own Motivating Example 2 end to end, through the real route."""
    code = """FUNCTION_BLOCK PumpControl
VAR_INPUT
  Start : BOOL;
END_VAR
VAR_OUTPUT
  Pump : BOOL;
END_VAR
VAR
  T1 : TON;
END_VAR
T1(IN := Start, PT := T#5S);
Pump := T1.Q;
END_FUNCTION_BLOCK
"""
    resp = _submit(client, code=code, name="SlowPreset", categories=["timer"])
    with client.application.app_context():
        from dashboard.models import MutantCompileResult
        preset_mutant = MutantCompileResult.query.filter_by(
            submission_id=1, operator_id="TIMER_PRESET_CHANGE").first()
        assert preset_mutant is not None  # T#5S halves to T#2S -- a real, generatable mutant
        mutant_id = preset_mutant.id
        # Original needs ~51 nominal scans to fire -- comfortably past
        # what a "30-scan" search actually observes in practice (~35-40,
        # due to real-time scheduling slop documented elsewhere in this
        # project). Overwrite the mutant's preset to T#10S (~101 scans)
        # so neither side fires within the default budget.
        preset_mutant.mutated_code = code.replace("T#5S", "T#10S")
        db.session.commit()

    resp = client.post(f"/submissions/1/mutant/{mutant_id}/distinguish", data={}, follow_redirects=True)
    html = resp.data.decode()

    with client.application.app_context():
        from dashboard.models import MutantCompileResult
        m = db.session.get(MutantCompileResult, mutant_id)
        assert m.distinguish_status == "killed"
        assert m.distinguish_refinement_iterations >= 1
        assert m.distinguish_recovered_by_refinement is True
    assert "recovered by C-DET refinement" in html
    assert "insufficient_scan_depth" in html


def test_compile_and_run_is_asynchronous(client):
    """The POST that starts Compile and Run must return quickly (the job
    runs in the background), not block until the whole mergeSTcode.py +
    statement.sh chain finishes."""
    import time
    _submit(client, categories=["timer"])

    start = time.time()
    resp = client.post("/submissions/1/compile_and_run", data={}, follow_redirects=True)
    elapsed = time.time() - start

    assert resp.status_code == 200
    assert elapsed < 3, f"compile_and_run request took {elapsed:.1f}s -- should return almost immediately"

    from dashboard import job_runner
    assert job_runner.is_running(1) or job_runner.get_job(1).done.is_set()

    # Wait for the background job to actually finish before the test ends
    # (and before the next test's fixture/teardown runs), so we're not
    # leaving a dangling subprocess behind.
    job = job_runner.get_job(1)
    job.thread.join(timeout=60)
    assert job.done.is_set()

    with client.application.app_context():
        from dashboard.models import Submission
        s = db.session.get(Submission, 1)
        assert s.compile_run_ok is not None  # background job persisted its result


def test_stop_button_terminates_running_job(client):
    """Clicking Stop while Compile and Run is in progress should
    terminate the whole process group, not just leave it running."""
    import time
    _submit(client, categories=["timer"])
    client.post("/submissions/1/compile_and_run", data={}, follow_redirects=True)

    from dashboard import job_runner
    job = job_runner.get_job(1)
    assert job is not None

    # Give the subprocess a moment to actually start (spawn MATIEC/gcc)
    # before stopping it, so this is a genuine mid-run stop, not a race
    # against a job that hasn't started yet.
    time.sleep(0.5)

    resp = client.post("/submissions/1/stop", data={}, follow_redirects=True)
    assert resp.status_code == 200

    job.thread.join(timeout=15)
    assert job.done.is_set()

    with client.application.app_context():
        from dashboard.models import Submission
        s = db.session.get(Submission, 1)
        assert s.compile_run_ok is False
        assert "Stopped by user" in s.compile_run_log


def test_stop_with_nothing_running_does_not_error(client):
    _submit(client, categories=["timer"])
    resp = client.post("/submissions/1/stop", data={}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Nothing is currently running" in resp.data


def test_scl_style_converts_single_line_comments_only(client):
    """The SCL button's actual scope: single-line (* ... *) comments
    become // comments; everything else (declarations, operators, block
    keywords) stays exactly the same, since it's already compatible."""
    from dashboard.mutate_service import to_scl_style
    text = "Pump := T1.Q; (* keep this *)\nVAR\n  x : BOOL; (* multi\nline *)\nEND_VAR"
    result = to_scl_style(text)
    assert "// keep this" in result
    assert "(* multi\nline *)" in result  # multi-line comments untouched
    assert "VAR" in result and "END_VAR" in result  # declarations untouched


def test_scl_button_present_and_default_view_is_plain_st(client):
    """The SCL button must exist, and without pressing it the page shows
    the normal ST view -- 'otherwise everything remains the same'."""
    resp = _submit(client, categories=["timer"])
    html = resp.data.decode()
    assert 'id="scl-btn"' in html
    assert "```st" in html
    assert "```scl" not in html

    resp = client.get("/submissions/1/mutant/1")
    assert 'id="scl-toggle-btn"' in resp.data.decode()  # detail page keeps its display-only toggle


def test_scl_files_not_written_until_scl_button_pressed(client):
    """Generating mutations must not create anything under
    Tests/mutatedCode/scl/ -- only the SCL button does."""
    import shutil
    shutil.rmtree(mutate_config.SCL_CODE_DIR, ignore_errors=True)
    _submit(client, categories=["timer"])
    assert not mutate_config.SCL_CODE_DIR.exists() or not list(mutate_config.SCL_CODE_DIR.glob("*"))
    assert list(mutate_config.MUTATED_CODE_DIR.glob("M*.st"))  # normal .st files still saved as before


def test_scl_button_saves_scl_files_under_mutatedcode_scl(client):
    """Pressing SCL saves one .scl file per mutant in
    Tests/mutatedCode/scl/, with single-line (* *) comments converted to
    //, and leaves the plain .st files exactly as they were."""
    import shutil
    # start from an empty mutatedCode/ so files left by other tests can't
    # be confused with this submission's mutants (this also clears scl/)
    shutil.rmtree(mutate_config.MUTATED_CODE_DIR, ignore_errors=True)
    _submit(client, categories=["timer"])
    st_before = {f.name: f.read_text() for f in mutate_config.MUTATED_CODE_DIR.glob("M*.st")}
    assert st_before

    resp = client.post("/submissions/1/scl", data={}, follow_redirects=True)
    html = resp.data.decode()
    assert resp.status_code == 200
    assert "SCL file(s) saved" in html
    assert "```scl" in html          # page now shows the SCL view

    assert mutate_config.SCL_CODE_DIR == mutate_config.MUTATED_CODE_DIR / "scl"
    scl_files = sorted(mutate_config.SCL_CODE_DIR.glob("M*.scl"))
    assert [f.stem for f in scl_files] == sorted(Path(n).stem for n in st_before)

    import re
    for f in scl_files:
        text = f.read_text()
        assert re.search(r"// MUTAT(ION|ED)", text), f"{f.name}: mutation annotation not converted to //"
        assert not re.search(r"\(\*\s*MUTAT", text), f"{f.name}: (* MUTAT... *) comment left unconverted"
    # ...while the plain .st versions of the same mutants keep the (* *) style
    assert all(re.search(r"\(\*\s*MUTAT", t) for t in st_before.values())

    st_after = {f.name: f.read_text() for f in mutate_config.MUTATED_CODE_DIR.glob("M*.st")}
    assert st_after == st_before      # plain .st files untouched


def test_scl_button_requires_generated_mutations(client):
    _submit(client, code="not st code at all", categories=["timer"])
    resp = client.post("/submissions/1/scl", data={}, follow_redirects=True)
    assert b"Generate mutations first" in resp.data


def test_homepage_shows_both_buttons(client):
    resp = client.get("/")
    html = resp.data.decode()
    assert "Generate Mutations" in html
    assert "Compile and Run" in html
    assert 'disabled title="Generate mutations first"' in html


def test_single_click_validates_and_generates(client):
    resp = _submit(client, categories=["timer"])
    html = resp.data.decode()
    assert "Valid ST program" in html
    assert "PumpControl" in html
    assert "M001" in html


DIFFERENT_PROGRAM_ST = """FUNCTION_BLOCK CounterLogic
VAR_INPUT
  Enable : BOOL;
  Threshold : INT;
END_VAR
VAR_OUTPUT
  Done : BOOL;
END_VAR
VAR
  count : INT;
END_VAR
IF Enable AND count < Threshold THEN
  count := count + 1;
END_IF;
Done := count >= Threshold;
END_FUNCTION_BLOCK
"""


def test_unrelated_program_still_gets_mutations(client):
    """The real scenario: a completely different program than what this
    project's Programcontroller.txt/Config.txt were built around (e.g.
    DEC_TO_HEX instead of PumpControl). It will very likely fail the
    harness-context compile check -- that must not stop mutation
    generation, which is a text-level operation on whatever code was
    provided."""
    resp = _submit(client, code=DIFFERENT_PROGRAM_ST, name="CounterLogic", categories=["relational"])
    html = resp.data.decode()
    assert "M001" in html
    assert "CounterLogic" in html


def test_mutations_generate_even_when_original_fails_to_compile(client):
    """The user's explicit correction: mutation generation must not be
    gated behind compilation. A program that doesn't fit this project's
    specific Library/Programcontroller/Config harness (e.g. a completely
    different FUNCTION_BLOCK than the one the harness was built around)
    should still get mutants generated -- compilation and mutation are
    independent concerns."""
    resp = _submit(client, code=BROKEN_ST, categories=["timer"])
    html = resp.data.decode()
    assert "Compilation failed" in html
    assert "doesn't compile in your project's current" in html
    assert "M001" in html  # mutations generated anyway


def test_original_code_saved_to_tests_directory(client):
    """The user's explicit requirement: the originally provided code must
    be saved to the real Tests/ directory, not just kept in the database."""
    _submit(client, categories=["timer"])
    saved = mutate_config.TESTS_DIR / "original_ST_code.st"
    assert saved.exists()
    assert saved.read_text() == VALID_ST


def test_mutated_code_shown_as_markdown_style_block_in_monitor(client):
    """The user's explicit requirement: mutated code displayed with
    markdown (fenced code block), not just a one-line snippet."""
    resp = _submit(client, categories=["timer"])
    html = resp.data.decode()
    assert "```st" in html
    assert "mutant-code-block" in html
    assert "hl-added" in html  # the changed portion still highlighted inside the block


def test_generate_does_not_compile_or_run(client):
    """Generate Mutations must not trigger compile_and_run.py."""
    resp = _submit(client, categories=["timer"])
    html = resp.data.decode()
    assert "Step 3/4" not in html
    with client.application.app_context():
        from dashboard.models import Submission
        s = db.session.get(Submission, 1)
        assert s.compile_run_ok is None
        assert s.compile_run_log is None


def test_math_functions_link_correctly(client):
    """Real bug found in production use: MATIEC declares 12 iec_lib_*
    math functions (used by LN/LOG/EXP/SIN/COS/etc.) but never defines
    them in the bundled reference harness -- gcc's LINKER (not MATIEC's
    compiler) fails with 'undefined reference to iec_lib_fmod' the first
    time a program uses any of them. Confirmed via a real user report.
    Exercises the real tools/statement.sh directly (not through the
    dashboard's PumpControl-specific harness, which would reject any
    other FB regardless of this bug -- see the "unrelated program" test).
    """
    tests_dir = mutate_config.TESTS_DIR
    slot_file = tests_dir / "2 mutatecode.txt"
    controller_file = tests_dir / "4 Programcontroller.txt"
    testcase_file = tests_dir / "3 Testcase.txt"

    slot_backup = slot_file.read_text()
    controller_backup = controller_file.read_text()
    testcase_backup = testcase_file.read_text()

    try:
        slot_file.write_text(
            "FUNCTION_BLOCK MathTest\n"
            "VAR_INPUT\n  x : REAL;\nEND_VAR\n"
            "VAR_OUTPUT\n  y : REAL;\nEND_VAR\n"
            "y := LN(x);\n"
            "END_FUNCTION_BLOCK\n"
        )
        controller_file.write_text(
            "PROGRAM TestRunnerProgram\nVAR\n  UUT : MathTest;\nEND_VAR\nUUT(x := 2.0);\nEND_PROGRAM\n"
        )
        testcase_file.write_text("(* unused *)\n")

        import subprocess
        tools_dir = mutate_config.PROJECT_ROOT / "tools"
        merge = subprocess.run(["python3", "mergeSTcode.py"], cwd=tools_dir,
                                capture_output=True, text=True, timeout=30)
        assert merge.returncode == 0, merge.stderr

        result = subprocess.run(["bash", "statement.sh"], cwd=tools_dir,
                                 capture_output=True, text=True, timeout=60)
        output = result.stdout + result.stderr
        assert "undefined reference" not in output, output
        assert "GCC compilation FAILED" not in output, output
        assert "GCC compilation successful" in output, output
    finally:
        slot_file.write_text(slot_backup)
        controller_file.write_text(controller_backup)
        testcase_file.write_text(testcase_backup)


def test_compile_and_run_runs_real_combined_script(client):
    """The ONE button: runs tools/compile_and_run.py, which itself runs
    mergeSTcode.py then statement.sh."""
    _submit(client, categories=["timer"])
    resp = _compile_and_run(client)
    html = resp.data.decode()
    assert "Step 3/4" in html
    assert "MERGE" in html
    assert "COMPILE / RUN" in html
    assert "statement.sh" in html or "compile_and_run.py" in html
    with client.application.app_context():
        from dashboard.models import Submission
        s = db.session.get(Submission, 1)
        assert s.compile_run_ok is not None


def test_activate_switches_active_mutant(client):
    _submit(client, categories=["timer"])
    _compile_and_run(client)

    with client.application.app_context():
        from dashboard.models import Submission
        assert db.session.get(Submission, 1).compile_run_ok is not None

    resp = client.post("/submissions/1/mutant/2/activate", data={}, follow_redirects=True)
    html = resp.data.decode()
    assert "M002" in html

    with client.application.app_context():
        from dashboard.models import Submission
        s = db.session.get(Submission, 1)
        assert s.active_mutant_id == 2
        assert s.compile_run_ok is None  # previous result invalidated by switching


def test_monitor_shows_highlighted_mutations_immediately(client):
    resp = _submit(client, categories=["timer"])
    html = resp.data.decode()
    assert "mutant-summary-list" in html
    assert "hl-removed" in html
    assert "hl-added" in html
    assert "TIMER_BYPASS" in html or "TIMER_PRESET_CHANGE" in html


def test_mutant_detail_shows_highlighted_both_codes(client):
    _submit(client, categories=["timer"])
    resp = client.get("/submissions/1/mutant/1")
    html = resp.data.decode()
    assert "hl-removed" in html
    assert "hl-added" in html
    assert "side-by-side" in html


def test_mutants_saved_to_tests_mutatedcode_dir(client):
    _submit(client, categories=["timer"])
    saved_files = sorted(mutate_config.MUTATED_CODE_DIR.glob("M*.st"))
    assert len(saved_files) >= 1
    assert saved_files[0].name == "M001.st"


def test_mutation_saved_to_mutatecode_slot_after_compile_and_run(client):
    _submit(client, categories=["timer"])
    _compile_and_run(client)
    _merge_order, slot_filename = mutate_config.discover_tests_layout()
    slot_content = (mutate_config.TESTS_DIR / slot_filename).read_text()
    assert "MUTATED" in slot_content or "Start;" in slot_content


def test_file_upload_path(client):
    data = {"name": "FileUpload", "st_file": (io.BytesIO(VALID_ST.encode()), "pump.st"),
            "categories": ["timer"]}
    resp = client.post("/submit", data=data, content_type="multipart/form-data", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Valid ST program" in resp.data
    assert b"M001" in resp.data


def test_export_csv(client):
    _submit(client, categories=["timer"])
    resp = client.get("/submissions/1/export.csv")
    assert resp.status_code == 200
    assert b"mutant_id" in resp.data


def test_export_json(client):
    _submit(client, categories=["timer"])
    resp = client.get("/submissions/1/export.json")
    payload = json.loads(resp.data)
    assert payload["submission_id"] == 1
    assert payload["mutants"][0]["status"] in ("not_tested", "success", "failed")


def test_empty_submission_rejected_cleanly(client):
    resp = client.post("/submit", data={"name": "Empty", "original_code": ""}, follow_redirects=True)
    assert b"No ST code provided" in resp.data


def test_non_st_gibberish_fails_cleanly(client):
    resp = _submit(client, code="not st code at all", categories=["timer"])
    assert b"Compilation failed" in resp.data


def test_original_code_preserved_unchanged(client):
    _submit(client, categories=["timer"])
    with client.application.app_context():
        from dashboard.models import Submission
        s = db.session.get(Submission, 1)
        assert s.original_code == VALID_ST


def test_operators_never_mutate_comments_or_strings():
    from mutate_core.operators import generate_all_candidates
    src = (
        "PROGRAM P\nVAR a : BOOL; b : BOOL; x : INT; END_VAR\n"
        "// b) Circuit+breaker control (Open_xxx = TRUE -> breaker open) AND 5\n"
        "(* c) a + b = TRUE OR 7 *)\n"
        "x := x + 1; // trailing x*2 = FALSE\n"
        "IF a AND b THEN x := 3; END_IF;\nEND_PROGRAM\n"
    )
    protect = ["// b) Circuit+breaker control (Open_xxx = TRUE -> breaker open) AND 5",
               "(* c) a + b = TRUE OR 7 *)", "// trailing x*2 = FALSE"]
    cands = generate_all_candidates(src)
    assert cands
    for _op, c in cands:
        assert c.mutated_text != src
        for line in protect:
            assert line in c.mutated_text
