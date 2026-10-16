from datetime import datetime, timezone
from dashboard.extensions import db


class Submission(db.Model):
    __tablename__ = "submission"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    original_code = db.Column(db.Text, nullable=False)   # the ST code as submitted, NEVER modified
    original_compile_ok = db.Column(db.Boolean, nullable=False)
    original_compile_stderr = db.Column(db.Text, nullable=True)
    categories_selected = db.Column(db.String(255), nullable=True)  # comma-separated, set at generate time
    generated = db.Column(db.Boolean, default=False)  # False until "Generate Mutations" has been run
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Which mutant is currently written into the mutatecode slot.
    active_mutant_id = db.Column(db.Integer, nullable=True)
    generation_log = db.Column(db.Text, nullable=True)   # summary of what "Generate Mutations" did

    # --- "Compile and Run" (one button -> tools/compile_and_run.py,
    # which itself runs mergeSTcode.py then statement.sh) ---
    compile_run_ok = db.Column(db.Boolean, nullable=True)         # None = never run
    compile_run_log = db.Column(db.Text, nullable=True)
    compile_run_for_mutant_id = db.Column(db.Integer, nullable=True)  # which mutant this result is for

    mutants = db.relationship("MutantCompileResult", backref="submission",
                               cascade="all, delete-orphan", lazy="dynamic")

    def mutant_count(self) -> int:
        return self.mutants.count()

    def distinguish_summary(self) -> dict:
        """A small, real comparison in the spirit of the paper's RQ4
        (does diagnosis-guided refinement improve fault detection beyond
        the baseline search alone?) -- scoped to whatever mutants have
        actually been run through DistinguishSearch on this submission,
        not a controlled multi-program study like the paper's Thrust 3.
        """
        searched = [m for m in self.mutants if m.distinguish_status is not None]
        return {
            "searched": len(searched),
            "killed_no_refinement": sum(1 for m in searched if m.distinguish_status == "killed"
                                          and not m.distinguish_recovered_by_refinement),
            "killed_by_refinement": sum(1 for m in searched if m.distinguish_recovered_by_refinement),
            "undetermined": sum(1 for m in searched if m.distinguish_status == "undetermined"),
        }

    def selected_categories_list(self) -> list[str]:
        return self.categories_selected.split(",") if self.categories_selected else []

    def active_mutant(self):
        if self.active_mutant_id is None:
            return None
        return db.session.get(MutantCompileResult, self.active_mutant_id)


class MutantCompileResult(db.Model):
    __tablename__ = "mutant_compile_result"

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey("submission.id"), nullable=False)

    operator_id = db.Column(db.String(64), nullable=False)
    operator_family = db.Column(db.String(16), nullable=False)  # "conventional" | "plc"
    category = db.Column(db.String(32), nullable=False)
    location_id = db.Column(db.String(120), nullable=False)
    original_snippet = db.Column(db.Text, nullable=False)
    mutated_snippet = db.Column(db.Text, nullable=False)
    mutated_code = db.Column(db.Text, nullable=False)

    # Populated only once this mutant has actually been through a real
    # Compile and Run while active -- None means "not tested yet".
    compile_ok = db.Column(db.Boolean, nullable=True)
    compile_stderr = db.Column(db.Text, nullable=True)

    # Populated only once "Run DistinguishSearch" has been clicked for
    # this mutant -- None means "not searched yet".
    distinguish_status = db.Column(db.String(16), nullable=True)   # "killed" | "undetermined" | "error"
    distinguish_depth = db.Column(db.Integer, nullable=True)
    distinguish_strategy = db.Column(db.String(32), nullable=True)
    distinguish_log = db.Column(db.Text, nullable=True)
    distinguish_refinement_iterations = db.Column(db.Integer, nullable=True)
    distinguish_recovered_by_refinement = db.Column(db.Boolean, nullable=True)  # was baseline undetermined, refinement fixed it?

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    @property
    def display_id(self) -> str:
        return f"M{self.id:03d}"
