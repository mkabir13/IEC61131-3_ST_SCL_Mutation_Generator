# tools/ -- ST Mutation, Compilation & Dashboard (complete project)

Everything lives here now: the mutation engine, the CLI campaign tool, and
the web dashboard. Drop this whole `tools/` folder into your `mutate/`
project (alongside `matiec/`, `Tests/`, `Output/`, `log/`) and you're set.

```
mutate/
├── matiec/        (yours, untouched)
├── Tests/         (yours, untouched)
├── Output/        (yours, untouched)
├── log/           (yours, untouched -- shared by both the CLI tool and the dashboard)
└── tools/         <- everything below is in here
    ├── start.sh                  <- ONE COMMAND to launch the dashboard
    ├── run_dashboard.py
    ├── requirements.txt
    ├── config.py                  (mutation-engine paths: MATIEC_BIN, etc.)
    ├── mergeSTcode.py
    ├── matiec_runner.py
    ├── run_mutation_campaign.py    (CLI: compile+execute+GCOV workflow, needs Tests/3-5)
    ├── CLI_CAMPAIGN_TOOL.md        (bug fixes + details specific to the CLI tool)
    ├── runtime_patch/main.c
    ├── mutate_core/                (mutation operators -- shared by CLI tool AND dashboard)
    │   ├── manifest.py
    │   └── operators.py
    └── dashboard/                  (the web UI)
        ├── app.py, routes.py, models.py, mutate_service.py, experiment_log.py
        ├── templates/, static/
        ├── tests/
        └── README.md               (mutation categories, logging format, scope decisions)
```

## Run it -- single command

```bash
cd mutate/tools
./start.sh
```

First run creates `tools/.venv` and installs Flask + Flask-SQLAlchemy
automatically (a few seconds). Every run after that reuses the same venv, so
it starts in about a second. Open the URL it prints -- by default:

```
http://<your-machine's-LAN-IP>:5050
```

(It binds to `0.0.0.0` by default, so it's reachable from other devices on
your network immediately -- no extra flags needed. Use
`DASHBOARD_HOST=127.0.0.1 ./start.sh` if you want local-only access instead.)

To stop it: `Ctrl+C` in the terminal running `start.sh`.

## What you get

A dashboard where you can:
1. Paste or upload ST code -- validated immediately against the real MATIEC compiler
2. See a structure summary (POU type/name, variables, timers, IF/loop/assignment counts)
3. Pick from 9 mutation categories (or select all) and generate mutants
4. See every mutant auto-compiled, with a unique ID (M001, M002, ...), pass/fail status, and full compiler errors on failure
5. View a highlighted diff per mutant
6. Export results as CSV or JSON
7. Find every run logged under `mutate/log/{experiments,mutations,compilation,errors}/`, never overwritten

This is **compile-only** (no GCC build, execution, or GCOV coverage) -- that
was an explicit scope decision, since execution needs a runnable test
harness that a bare uploaded ST file doesn't have on its own. The separate
CLI tool (`python3 run_mutation_campaign.py`, still here, unchanged) does
the full compile+execute+coverage workflow against your `Tests/` harness
files if you need that instead.

## Requirements

- Python 3.10+
- A built `matiec/iec2c` binary at `../matiec/iec2c` relative to `tools/`
  (i.e. `mutate/matiec/iec2c`) -- you already have this. `start.sh` warns
  you if it's missing.
- No C toolchain (gcc/gcov) needed for the dashboard -- only for the
  separate CLI campaign tool's execution/coverage workflow.

`start.sh` handles the Python side (venv + `pip install`) for you.

## Verify it yourself

```bash
cd mutate/tools
source .venv/bin/activate   # after at least one ./start.sh run
pip install pytest
python3 -m pytest dashboard/tests/ -v
```
Expects `14 passed` -- every test runs against the real MATIEC binary, nothing mocked.

```bash
python3 run_mutation_campaign.py
```
Confirms the CLI tool (and the shared `mutate_core` operators) still work.

## If you move MATIEC or use a different path

Set `MATIEC_BIN` and `MATIEC_LIB` before running `start.sh`:
```bash
MATIEC_BIN=/path/to/iec2c MATIEC_LIB=/path/to/lib ./start.sh
```
(`tools/config.py` reads these env vars, falling back to
`../matiec/iec2c` / `../matiec/lib` if unset.)

## More detail

- **Mutation categories, logging format, dashboard scope decisions:** `dashboard/README.md`
- **CLI campaign tool bug fixes and internals (statement.sh/mergeSTcode.py corrections, the common_ticktime__ ns/ms bug, etc.):** `CLI_CAMPAIGN_TOOL.md`
