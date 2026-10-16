"""
job_runner.py -- makes "Compile and Run" cancellable.

Without this, the button blocks the HTTP request until the whole
mergeSTcode.py + statement.sh chain finishes -- there's no page rendered
yet for a Stop button to even appear on. This runs the job in a
background thread, launching tools/compile_and_run.py as its own process
group (start_new_session=True) so a Stop request can kill it AND every
child process it spawned (matiec's iec2c, gcc, the compiled softplc
binary) in one shot via os.killpg -- not just the top-level Python
process, which would leave orphaned children running.

In-memory job registry, not persisted -- acceptable for this single-user
local dashboard; a job's state is lost if the server restarts mid-run
(the Submission row will just be left showing "running" until the next
Compile and Run click, which is recoverable, not silently wrong).
"""

from __future__ import annotations
import os
import signal
import subprocess
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent


@dataclass
class Job:
    process: subprocess.Popen | None = None
    thread: threading.Thread | None = None
    stdout: str = ""
    returncode: int | None = None
    stop_requested: bool = False
    done: threading.Event = field(default_factory=threading.Event)
    persisted: bool = False  # has the result been written to the DB yet?


_jobs: dict[int, Job] = {}
_lock = threading.Lock()


def start_compile_and_run(submission_id: int, flask_app) -> Job:
    """Starts (or returns the already-running) job for this submission.
    `flask_app` is needed so the background thread can push an app
    context to touch the database once the subprocess finishes.
    """
    with _lock:
        existing = _jobs.get(submission_id)
        if existing is not None and not existing.done.is_set():
            return existing
        job = Job()
        _jobs[submission_id] = job

    def _run():
        try:
            job.process = subprocess.Popen(
                [sys.executable, "compile_and_run.py"],
                cwd=TOOLS_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                start_new_session=True,  # own process group -- lets Stop kill children too
            )
            stdout, _ = job.process.communicate()
            job.stdout = stdout or ""
            job.returncode = job.process.returncode
        except Exception as e:
            job.stdout = f"Failed to start compile_and_run.py: {e}"
            job.returncode = -1
        finally:
            job.done.set()
            _persist_result(submission_id, job, flask_app)

    job.thread = threading.Thread(target=_run, daemon=True)
    job.thread.start()
    return job


def _persist_result(submission_id: int, job: Job, flask_app) -> None:
    with flask_app.app_context():
        from dashboard.extensions import db
        from dashboard.models import Submission
        from dashboard.experiment_log import log_compile_run

        submission = db.session.get(Submission, submission_id)
        if submission is None:
            return

        if job.stop_requested:
            ok = False
            output = job.stdout + "\n\n[Stopped by user -- process group terminated before completion.]"
        else:
            ok = job.returncode == 0
            output = job.stdout

        mutant = submission.active_mutant()
        submission.compile_run_ok = ok
        submission.compile_run_log = output
        submission.compile_run_for_mutant_id = mutant.id if mutant else None
        if mutant is not None:
            mutant.compile_ok = ok
            mutant.compile_stderr = None if ok else output
        db.session.commit()

        if mutant is not None:
            log_compile_run(submission_id=submission_id, mutant_display_id=mutant.display_id,
                             ok=ok, output=output)
        job.persisted = True


def stop_job(submission_id: int) -> bool:
    """Sends SIGTERM to the job's whole process group. Returns False if
    there's no running job to stop.
    """
    with _lock:
        job = _jobs.get(submission_id)
    if job is None or job.process is None or job.done.is_set():
        return False
    job.stop_requested = True
    try:
        pgid = os.getpgid(job.process.pid)
        os.killpg(pgid, signal.SIGTERM)
    except ProcessLookupError:
        return False
    return True


def get_job(submission_id: int) -> Job | None:
    with _lock:
        return _jobs.get(submission_id)


def is_running(submission_id: int) -> bool:
    job = get_job(submission_id)
    return job is not None and not job.done.is_set()
