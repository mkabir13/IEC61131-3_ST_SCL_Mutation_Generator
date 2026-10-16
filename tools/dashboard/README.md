# ST Mutation Dashboard

Compile-only scope (execution/GCOV explicitly deferred, per your decision).
Covers requirements 1-11 and 13 of the full spec faithfully; see "Scope" below
for exactly what's included vs. deferred.

## What it does

**Step 1 -- Input & Validation** (`/`)
- Paste ST code or upload a `.st`/`.txt` file
- Compiles the original through the real MATIEC binary immediately
- Original source is never modified -- stored once, read-only from then on

**Step 2 -- Structure Summary & Mutation Options** (`/submissions/<id>`)
- A structural scan (POU type/name, declared variables by section, detected
  timer/edge instances, IF/loop/assignment counts) -- NOT a full AST (MATIEC's
  CLI doesn't expose one); labeled honestly as a summary, not a parse tree
- 9 mutation category checkboxes with Select All / Clear All

**Step 3 -- Generate Mutations** (POST `/submissions/<id>/generate`)
- Runs every selected category automatically
- Compiles every mutant through real MATIEC, continuing past failures
- Assigns unique IDs (M001, M002, ...)
- Writes the structured `log/` directory (see below)

**Step 4 -- Results** (`/submissions/<id>` after generation)
- Total/compiled/failed counts
- Per-mutant table: ID, operator, category, location, change, compile status
- Click through to a diff view (highlighted additions/removals) + full
  mutated code + full compiler error on failure
- CSV and JSON export

## Mutation categories

| Category | Operator(s) | Example |
|---|---|---|
| Relational | `REL_OP_REPLACE` | `>` &harr; `<`, `>=` &harr; `<=`, `=` &harr; `<>` |
| Logical | `LOGICAL_OP_REPLACE` | `AND` &harr; `OR` |
| Arithmetic | `ARITH_OP_REPLACE` | `+` &harr; `-`, `*` &harr; `/` (binary usage only) |
| Boolean Constant | `BOOL_CONST_REPLACE` | `TRUE` &harr; `FALSE` |
| Constant (Numeric) | `CONST_VALUE_REPLACE` | integer literal `+1` |
| Variable Replacement | `VAR_REPLACE` | swaps one BOOL variable usage for another (best-effort, type-safe) |
| Assignment | `ASSIGN_NEGATE` | `X := expr;` &rarr; `X := NOT (expr);` (BOOL targets only) |
| Conditional | `COND_NEGATE` | `IF cond THEN` &rarr; `IF NOT (cond) THEN` |
| Timer / Edge | `TIMER_BYPASS`, `TIMER_PRESET_CHANGE`, `EDGE_POLARITY_FLIP` | PLC-construct-aware mutations |

All defined in `tools/mutate_core/operators.py` -- the single source of truth
shared with your CLI campaign tool (`tools/run_mutation_campaign.py`). Adding
this here didn't touch anything else in `tools/`; the CLI tool picks up the
new operators automatically and still passes its own tests.

## Logging

```
log/
├── experiments/    one JSON summary per run -- never overwritten
│                    (experiment id, timestamp, mutation counts, etc.)
├── mutations/       per-run subfolder with the original + every mutant's
│                    full ST source, one file each
├── compilation/     per-run subfolder, one .txt per mutant with its full
│                    compile log (operator, location, change, stderr)
└── errors/          per-run subfolder, copies of ONLY the failed mutants'
                     compile logs, for fast review
```
Each run's subfolders are timestamped (`submission_<id>_<UTC timestamp>`), so
nothing from a previous experiment is ever overwritten -- confirmed by test
(`test_experiment_log_written`, plus a direct failed-mutant check).

## Requirements and installation

Same as before -- no new dependencies:
```bash
cd mutate/
source ~/langchain-env/bin/activate      # or: python3 -m venv .venv && source .venv/bin/activate
pip install -r dashboard/requirements.txt
DASHBOARD_HOST=0.0.0.0 python3 run_dashboard.py
```
Open `http://<your-ip>:5050` (or `127.0.0.1:5050` for local-only access).

## Verify the install

```bash
pip install pytest
python3 -m pytest dashboard/tests/ -v
```
Expects `14 passed`. Every test hits the real MATIEC binary -- nothing is
mocked. Also re-verify the CLI campaign tool still works after this upgrade:
```bash
cd tools && python3 run_mutation_campaign.py
```

## Scope -- what's in, what's deferred

**In (compile-only, as decided):**
- ST input (paste + upload), validation, structure summary
- Mutation category selection, unique mutant IDs, full traceability
- Automatic MATIEC compilation of every mutant, continuing past failures
- Diff view, per-mutant error display, CSV/JSON export
- Structured, non-overwriting logs

**Deferred (needs a decision, not built):**
- GCC compilation, executable generation, execution/testing, GCOV coverage --
  all of section 6-7's later stages. These need a runnable test harness
  (like your `Tests/3-5` files) that a bare uploaded FUNCTION_BLOCK doesn't
  have on its own. `tools/run_mutation_campaign.py` already does this for a
  *fixed* harness in `Tests/`; wiring that into the dashboard is a following
  step if you want it.
- Real-time/live-updating compile status (the "Pending -> Compiling ->
  Compiled" progression from your spec) -- MATIEC-only compilation is fast
  enough (well under a second per mutant) that this dashboard processes
  synchronously and shows final results on page load, rather than polling or
  using websockets. If mutant counts grow large enough that this becomes
  slow, background job processing (Celery/RQ) would be the next step.
- Integration with `AST_BUILDER.py` / `FAULT_LOCALIZER.py` / etc. -- not
  built, since you confirmed these don't exist yet in your project. No LLM
  components anywhere, per your explicit instruction.
- "Select individual mutation operators" at the operator level (e.g. just
  `TIMER_BYPASS` without `TIMER_PRESET_CHANGE`) -- currently grouped by the
  9 categories from your spec's UI mockup, not by the 11 individual operator
  IDs. Flag if you want per-operator checkboxes instead.
