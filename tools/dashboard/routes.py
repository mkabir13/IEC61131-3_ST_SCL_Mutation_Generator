import csv
import io
import json

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, abort,
    Response, current_app,
)

from dashboard.extensions import db
from dashboard.models import Submission, MutantCompileResult
from dashboard.mutate_service import (
    compile_via_project_harness, parse_and_mutate, scan_structure, render_diff_html,
    render_side_by_side_highlighted, available_categories, save_mutant_file,
    save_original_file, write_to_mutatecode_slot, to_scl_style, save_mutant_scl_file,
)
from dashboard.distinguish_search import DistinguishSearchError
from dashboard.adequacy_diagnostician import run_with_diagnosis_guided_refinement
from dashboard.experiment_log import log_generation
from dashboard import job_runner
import config as mutate_config  # safe to import bare here -- tools/ is already on sys.path
                                  # via mutate_service's own sys.path.insert, above

bp = Blueprint("dashboard", __name__)


@bp.route("/")
def index():
    submissions = Submission.query.order_by(Submission.created_at.desc()).limit(20).all()
    return render_template("index.html", submissions=submissions, categories=available_categories())


def _generate_mutants(submission: Submission, categories: list[str] | None) -> None:
    """Generates mutants and saves each to Tests/mutatedCode/. Does NOT
    write the mutatecode slot, merge, compile, or run anything -- that's
    all the separate, explicit "Compile and Run" action.
    """
    candidates = parse_and_mutate(submission.original_code, categories=categories)

    log_rows = []
    for cand in candidates:
        row = MutantCompileResult(
            submission_id=submission.id,
            operator_id=cand.operator_id,
            operator_family=cand.operator_family,
            category=cand.category,
            location_id=cand.location_id,
            original_snippet=cand.original_snippet,
            mutated_snippet=cand.mutated_snippet,
            mutated_code=cand.mutated_code,
        )
        db.session.add(row)
        db.session.flush()  # assigns row.id so display_id is available below

        saved_path = save_mutant_file(row.display_id, cand.mutated_code)
        log_rows.append({
            "display_id": row.display_id,
            "operator_id": row.operator_id,
            "category": row.category,
            "location_id": row.location_id,
            "original_snippet": row.original_snippet,
            "mutated_snippet": row.mutated_snippet,
            "mutated_code": row.mutated_code,
            "saved_path": str(saved_path),
        })

    submission.categories_selected = ",".join(categories) if categories else "all"
    submission.generated = True
    submission.generation_log = (
        f"Generated {len(log_rows)} mutant(s) "
        f"({', '.join(categories) if categories else 'all categories'}), "
        f"saved to Tests/mutatedCode/."
    )
    db.session.commit()

    log_generation(
        submission_id=submission.id,
        name=submission.name,
        original_code=submission.original_code,
        categories_selected=categories or ["all"],
        mutant_results=log_rows,
    )


@bp.route("/submit", methods=["POST"])
def submit():
    """Single homepage action: validate the submitted code, save the
    ORIGINAL code to Tests/ (separately from any mutant), and if valid,
    immediately generate mutations for the selected categories.
    """
    name = request.form.get("name", "").strip() or "Untitled"
    selected_categories = request.form.getlist("categories") or None  # None = all

    uploaded_file = request.files.get("st_file")
    if uploaded_file and uploaded_file.filename:
        original_code = uploaded_file.read().decode("utf-8", errors="replace")
    else:
        original_code = request.form.get("original_code", "")

    if not original_code.strip():
        flash("No ST code provided -- paste it in the editor or upload a .st file.", "error")
        return redirect(url_for("dashboard.index"))

    # Requirement: the originally provided code is saved to Tests/,
    # separately from the mutatecode slot mutants overwrite.
    save_original_file(original_code)

    original_ok, original_stderr = compile_via_project_harness(original_code)

    submission = Submission(
        name=name,
        original_code=original_code,
        original_compile_ok=original_ok,
        original_compile_stderr=None if original_ok else original_stderr,
    )
    db.session.add(submission)
    db.session.commit()

    if not original_ok:
        flash("Note: this code doesn't compile in your project's current Library/"
              "Programcontroller/Config harness (see Step 1 below) -- mutations are "
              "generated anyway, since that's a text-level operation independent of "
              "compilation. Compile and Run may fail until the harness mismatch is "
              "resolved.", "warning")

    try:
        _generate_mutants(submission, categories=selected_categories)
    except ValueError as e:
        flash(str(e), "error")

    return redirect(url_for("dashboard.view_submission", submission_id=submission.id))


@bp.route("/submissions/<int:submission_id>")
def view_submission(submission_id: int):
    submission = db.session.get(Submission, submission_id)
    if submission is None:
        abort(404)

    structure = None
    if not submission.generated:
        try:
            structure = scan_structure(submission.original_code)
        except Exception:
            structure = None

    mutants = submission.mutants.order_by(MutantCompileResult.id).all() if submission.generated else []

    highlighted_mutants = []
    for m in mutants:
        _orig_html, mut_html = render_side_by_side_highlighted(submission.original_code, m.mutated_code)
        _orig_scl_html, mut_scl_html = render_side_by_side_highlighted(
            to_scl_style(submission.original_code), to_scl_style(m.mutated_code)
        )
        highlighted_mutants.append({"mutant": m, "mutated_html": mut_html, "mutated_scl_html": mut_scl_html})

    return render_template(
        "submission.html",
        submission=submission,
        structure=structure,
        categories=available_categories(),
        mutants=mutants,
        highlighted_mutants=highlighted_mutants,
        compile_and_run_running=job_runner.is_running(submission_id),
        scl_mode=(request.args.get("view") == "scl"),
        active_mutant=submission.active_mutant() if submission.generated else None,
    )


@bp.route("/submissions/<int:submission_id>/generate", methods=["POST"])
def generate(submission_id: int):
    submission = db.session.get(Submission, submission_id)
    if submission is None:
        abort(404)
    if submission.generated:
        flash("Mutations were already generated for this submission.", "warning")
        return redirect(url_for("dashboard.view_submission", submission_id=submission.id))

    selected_categories = request.form.getlist("categories") or None  # None = all

    try:
        _generate_mutants(submission, categories=selected_categories)
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("dashboard.view_submission", submission_id=submission.id))

    if submission.mutant_count() == 0:
        flash("No mutation operators matched anything for the selected categories.", "warning")

    return redirect(url_for("dashboard.view_submission", submission_id=submission.id))


@bp.route("/submissions/<int:submission_id>/mutant/<int:mutant_id>/activate", methods=["POST"])
def activate_mutant(submission_id: int, mutant_id: int):
    """Picks which mutant's code sits in the mutatecode slot -- just a
    file write, no merge/compile. "Compile and Run" is what actually
    merges and compiles whatever is currently in the slot.
    """
    submission = db.session.get(Submission, submission_id)
    mutant = db.session.get(MutantCompileResult, mutant_id)
    if submission is None or mutant is None or mutant.submission_id != submission_id:
        abort(404)

    write_to_mutatecode_slot(mutant.mutated_code)
    submission.active_mutant_id = mutant.id
    submission.compile_run_ok = None
    submission.compile_run_log = None
    submission.compile_run_for_mutant_id = None
    db.session.commit()

    flash(f"{mutant.display_id} is now in the mutatecode slot. Click Compile and Run to build/test it.", "ok")
    return redirect(url_for("dashboard.view_submission", submission_id=submission_id))


@bp.route("/submissions/<int:submission_id>/compile_and_run", methods=["POST"])
def compile_and_run(submission_id: int):
    """The ONE button: writes the active (or first) mutant into the real
    Tests/ mutatecode slot, then STARTS tools/compile_and_run.py in the
    background (not blocking this request) -- a single Python file that
    itself runs mergeSTcode.py, then statement.sh, in sequence. Runs as
    its own process group so the Stop button can kill it (and every
    child process it spawned) cleanly. Never runs automatically from
    Generate Mutations -- only from this explicit click.
    """
    submission = db.session.get(Submission, submission_id)
    if submission is None:
        abort(404)
    if not submission.generated or submission.mutant_count() == 0:
        flash("Generate mutations first.", "error")
        return redirect(url_for("dashboard.view_submission", submission_id=submission_id))
    if job_runner.is_running(submission_id):
        flash("Compile and Run is already running for this submission.", "warning")
        return redirect(url_for("dashboard.view_submission", submission_id=submission_id))

    mutant = submission.active_mutant()
    if mutant is None:
        mutant = submission.mutants.order_by(MutantCompileResult.id).first()
        submission.active_mutant_id = mutant.id

    write_to_mutatecode_slot(mutant.mutated_code)
    submission.compile_run_ok = None
    submission.compile_run_log = None
    db.session.commit()

    job_runner.start_compile_and_run(submission_id, current_app._get_current_object())

    flash("Compile and Run started -- this page will update as it progresses.", "ok")
    return redirect(url_for("dashboard.view_submission", submission_id=submission_id))


@bp.route("/submissions/<int:submission_id>/scl", methods=["POST"])
def generate_scl(submission_id: int):
    """The SCL button: writes an SCL-formatted copy of every generated
    mutant to Tests/mutatedCode/scl/<id>.scl, then shows the SCL view.
    Doesn't touch the plain Tests/mutatedCode/<id>.st files, the
    mutatecode slot, or anything Compile and Run uses -- without this
    button being pressed, nothing is written to the scl/ directory.
    """
    submission = db.session.get(Submission, submission_id)
    if submission is None:
        abort(404)
    if not submission.generated or submission.mutant_count() == 0:
        flash("Generate mutations first.", "error")
        return redirect(url_for("dashboard.view_submission", submission_id=submission_id))

    saved = [save_mutant_scl_file(m.display_id, m.mutated_code)
             for m in submission.mutants.order_by(MutantCompileResult.id)]
    flash(f"{len(saved)} SCL file(s) saved to {mutate_config.SCL_CODE_DIR}", "ok")
    return redirect(url_for("dashboard.view_submission", submission_id=submission_id, view="scl"))


@bp.route("/submissions/<int:submission_id>/stop", methods=["POST"])
def stop(submission_id: int):
    """Stops the running Compile and Run job for this submission, if any
    -- kills the whole process group (compile_and_run.py plus whatever
    it spawned: mergeSTcode.py, or statement.sh and ITS children
    iec2c/gcc/softplc), not just the top-level process.
    """
    if job_runner.stop_job(submission_id):
        flash("Stop requested -- the running process is being terminated.", "ok")
    else:
        flash("Nothing is currently running for this submission.", "warning")
    return redirect(url_for("dashboard.view_submission", submission_id=submission_id))


@bp.route("/submissions/<int:submission_id>/mutant/<int:mutant_id>/distinguish", methods=["POST"])
def distinguish_mutant(submission_id: int, mutant_id: int):
    """Runs Task 1.3's DistinguishSearch plus Task 2.2's C-DET diagnosis-
    guided refinement (both from the AgenTest-ST paper, scoped down -- see
    dashboard/distinguish_search.py and adequacy_diagnostician.py's module
    docstrings for exactly what's covered): searches boolean input
    sequences for a divergence; if none is found, a deterministic
    diagnostician checks whether the search trace was simply too short
    for a TIMER construct to ever fire, and if so retries once with a
    computed sufficient depth. No LLM anywhere in this path. Independent
    of Compile and Run -- doesn't touch Tests/ or the mutatecode slot.
    """
    submission = db.session.get(Submission, submission_id)
    mutant = db.session.get(MutantCompileResult, mutant_id)
    if submission is None or mutant is None or mutant.submission_id != submission_id:
        abort(404)

    merge_order, _slot = mutate_config.discover_tests_layout()
    library_content = (mutate_config.TESTS_DIR / merge_order[0]).read_text(encoding="utf-8")

    try:
        refinement = run_with_diagnosis_guided_refinement(submission.original_code, mutant.mutated_code, library_content)
        result = refinement.final_result
        mutant.distinguish_status = result.status
        mutant.distinguish_depth = result.witness_depth
        mutant.distinguish_strategy = result.strategy
        mutant.distinguish_log = refinement.log
        mutant.distinguish_refinement_iterations = refinement.iterations
        mutant.distinguish_recovered_by_refinement = (
            refinement.iterations > 0 and result.status == "killed"
        )
    except DistinguishSearchError as e:
        mutant.distinguish_status = "error"
        mutant.distinguish_depth = None
        mutant.distinguish_strategy = None
        mutant.distinguish_log = str(e)
        mutant.distinguish_refinement_iterations = None
        mutant.distinguish_recovered_by_refinement = None

    db.session.commit()
    return redirect(url_for("dashboard.view_mutant", submission_id=submission_id, mutant_id=mutant_id))


@bp.route("/submissions/<int:submission_id>/mutant/<int:mutant_id>")
def view_mutant(submission_id: int, mutant_id: int):
    mutant = db.session.get(MutantCompileResult, mutant_id)
    if mutant is None or mutant.submission_id != submission_id:
        abort(404)
    original_code = mutant.submission.original_code
    original_html, mutated_html = render_side_by_side_highlighted(original_code, mutant.mutated_code)
    original_scl_html, mutated_scl_html = render_side_by_side_highlighted(
        to_scl_style(original_code), to_scl_style(mutant.mutated_code)
    )
    diff_html = render_diff_html(original_code, mutant.mutated_code)
    return render_template("mutant_detail.html", mutant=mutant, submission=mutant.submission,
                            original_html=original_html, mutated_html=mutated_html,
                            original_scl_html=original_scl_html, mutated_scl_html=mutated_scl_html,
                            diff_html=diff_html)


@bp.route("/submissions/<int:submission_id>/export.csv")
def export_csv(submission_id: int):
    submission = db.session.get(Submission, submission_id)
    if submission is None:
        abort(404)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["mutant_id", "operator", "category", "location", "original_snippet",
                      "mutated_snippet", "status", "error"])
    for m in submission.mutants.order_by(MutantCompileResult.id):
        status = "Not tested" if m.compile_ok is None else ("Success" if m.compile_ok else "Failed")
        writer.writerow([m.display_id, m.operator_id, m.category, m.location_id,
                          m.original_snippet, m.mutated_snippet, status, m.compile_stderr or ""])
    return Response(buf.getvalue(), mimetype="text/csv",
                     headers={"Content-Disposition": f"attachment; filename=submission_{submission_id}.csv"})


@bp.route("/submissions/<int:submission_id>/export.json")
def export_json(submission_id: int):
    submission = db.session.get(Submission, submission_id)
    if submission is None:
        abort(404)
    payload = {
        "submission_id": submission.id,
        "name": submission.name,
        "original_compile_ok": submission.original_compile_ok,
        "categories_selected": submission.selected_categories_list(),
        "active_mutant_id": submission.active_mutant_id,
        "compile_run_ok": submission.compile_run_ok,
        "mutants": [
            {
                "mutant_id": m.display_id,
                "operator_id": m.operator_id,
                "category": m.category,
                "location_id": m.location_id,
                "original_snippet": m.original_snippet,
                "mutated_snippet": m.mutated_snippet,
                "status": "not_tested" if m.compile_ok is None else ("success" if m.compile_ok else "failed"),
                "compile_stderr": m.compile_stderr,
            }
            for m in submission.mutants.order_by(MutantCompileResult.id)
        ],
    }
    return Response(json.dumps(payload, indent=2), mimetype="application/json",
                     headers={"Content-Disposition": f"attachment; filename=submission_{submission_id}.json"})
