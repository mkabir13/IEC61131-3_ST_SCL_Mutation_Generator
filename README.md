# IEC61131-3_ST_SCL_Mutation_Generator
A deterministic mutation generator for IEC 61131-3 PLC Structured Text (ST) and Siemens SCL, featuring 14 mutation operators, a Flask web dashboard, and MATIEC–GCC–GCOV-based compilation and test coverage analysis.

# PLC_Mutation_Generator_ST_SCL

A deterministic, **LLM-free** mutation generator for IEC 61131-3 PLC programs written in **Structured Text (ST)** and Siemens **Structured Control Language (SCL)**, with a Flask web dashboard.
Paste or upload an ST program, generate mutants, and push them through the
existing **MATIEC → GCC → run → GCOV** pipeline from the browser.

> Research prototype — CDAC, Lamar University. This project focuses on deterministic
> mutation generation and mutation-testing support for PLC ST/SCL code. See
> [Scope and limitations](#scope-and-limitations).

## Features

- **Input**: paste or upload ST; the original is saved unmodified in `Tests/`.
- **Mutation generation** (not gated on compilation) with category checkboxes:
  relational, logical, arithmetic, boolean constant, numeric constant,
  variable replacement, assignment negation, conditional negation,
  timer bypass / preset, edge-detector polarity, counter threshold / direction,
  SR↔RS latch priority (14 operators).
- **Comment-aware**: operators never mutate text inside `// …`, `(* … *)`
  comments or string literals.
- **Display**: each mutant shown as highlighted diff / fenced code; saved to
  `Tests/mutatedCode/M00X.st`.
- **Compile and Run**: one button runs `tools/compile_and_run.py`
  (`mergeSTcode.py` → `statement.sh`), as an async job with a **Stop** button
  (kills the whole process group).
- **SCL export**: button writes SCL-style copies to `Tests/mutatedCode/scl/<id>.scl`
  (cosmetic `(* *)`→`//` conversion only; not verified against Siemens tools).
- **Thrust 1/2/3 helpers**: `DistinguishSearch` (find an input sequence that
  separates a mutant from the original), a deterministic adequacy
  diagnostician (C-DET), and a small summary of results.
- **Logging**: per-run records under `log/{experiments,mutations,compilation,errors}/`,
  never overwritten. Exports: CSV, JSON.

## Quick start

Prerequisites: Linux, Python 3.10+, `gcc`/`gcov`, and a built
[MATIEC](https://github.com/beremiz/matiec).

```bash
# 1. Layout (sibling of tools/)
git clone https://github.com/<your-username>/PLC_Mutation_Generator_ST_SCL.git && cd PLC_Mutation_Generator_ST_SCL
git clone https://github.com/beremiz/matiec.git
(cd matiec && autoreconf -i && ./configure && make)    # needs bison flex autoconf automake libtool

# 2. Put your harness fragments in Tests/ (see Tests/README.md)

# 3. Run
cd tools && ./start.sh        # creates .venv, installs Flask, binds 0.0.0.0:5050
```

Open `http://<machine-LAN-IP>:5050`. Options: `DASHBOARD_PORT=8080`,
`DASHBOARD_HOST=127.0.0.1` (local only), `MATIEC_BIN=/path/iec2c`,
`MATIEC_LIB=/path/lib`.

## Workflow

```
ST code (paste/upload) → Tests/original_ST_code.st
        │ Generate Mutations (selected categories)
        ▼
mutate_core/operators.py → Tests/mutatedCode/M001.st … (+ DB records, log/)
        │ Compile and Run  (compile_and_run.py)
        ▼
mergeSTcode.py → Tests/TestCode.st → statement.sh
   (MATIEC iec2c → gcc --coverage → run → gcov)  → Output/, log/
```

## Repository layout

```
tools/
├── start.sh, run_dashboard.py     launch the dashboard
├── compile_and_run.py             mergeSTcode.py + statement.sh
├── mergeSTcode.py, statement.sh   merge fragments; MATIEC→GCC→run→GCOV
├── matiec_runner.py               per-mutant compile helper
├── run_mutation_campaign.py       CLI campaign (see CLI_CAMPAIGN_TOOL.md)
├── config.py                      paths, Tests/ layout discovery
├── runtime_patch/                 softPLC harness fixes (tick time, clock, math lib)
├── mutate_core/operators.py       the mutation operators
└── dashboard/                     Flask app, templates, tests
Tests/                             your harness fragments (+ generated mutants, ignored)
```

## Tests

```bash
cd tools && source .venv/bin/activate && pip install pytest
PYTHONPATH=. python -m pytest dashboard/tests -v
```
Most tests need a built MATIEC and the `Tests/` fragments; the operator tests
(including the comment-masking regression) do not.

## Scope and limitations

- No LLM and no AST: operators are regex/offset based on masked source, so
  they are heuristics; some mutants will not compile and are recorded as such.
- Located (`%I/%Q`) variable dumps are unreliable in the harness; observation
  uses `MUT_OBS:` printf markers.
- Harness fixes (`runtime_patch/`) address tick-time units, a never-updated
  `__CURRENT_TIME`, and missing `iec_lib_*` math functions.
- Research prototype; no warranty. Add a `LICENSE` before publishing.

See `tools/README.md`, `tools/dashboard/README.md`, and
`tools/CLI_CAMPAIGN_TOOL.md` for details.
