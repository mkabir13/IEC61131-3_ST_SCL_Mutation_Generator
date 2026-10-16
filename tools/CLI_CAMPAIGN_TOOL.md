# tools/ — mutation-testing tool for your existing mutate/ project

Drop this `tools/` directory in place of your current one, alongside your
existing `matiec/`, `Tests/`, `Output/` (and `log/`, created automatically).
No changes needed to those directories — this only reads from `Tests/` and
writes into `Output/` and `log/`, exactly like your current scripts.

## Run it

    cd tools/
    python3 run_mutation_campaign.py

Output: `Output/manifest.json`, `Output/summary.csv`, `log/iter_<N>/` per
mutant — same log-per-iteration convention as your `statement.sh`.

## Files

| File | Purpose |
|---|---|
| `config.py` | All paths/constants — points at `../matiec`, `../Tests`, `../Output`, `../log` |
| `mergeSTcode.py` | Corrected version of yours — see fix #1 below |
| `mutate_core/operators.py` | Mutation operators (regex-based, matching your text-manipulation style): `REL_OP_BOUNDARY`, `TIMER_BYPASS`, `TIMER_PRESET_CHANGE`, `EDGE_POLARITY_FLIP` |
| `mutate_core/manifest.py` | Result schema — `ValidationStatus`, `KillStatus`, JSON/CSV writers |
| `matiec_runner.py` | Python port of your `statement.sh` — see fixes #2–#4 below |
| `runtime_patch/main.c` | A corrected copy of `matiec/tests/main.c` — see fix #5, the important one |
| `run_mutation_campaign.py` | Main entrypoint: generates mutants, runs each through the real pipeline, classifies killed/survived against a baseline |

## What's corrected relative to your existing scripts

**1. `mergeSTcode.py` — `"3 Testcase.txt"` was missing from the merge.**
Your `st_files` list skipped it, but `"4 Programcontroller.txt"` instantiates
`FB_TEST_0`, which only `"3 Testcase.txt"` defines. Left out, that reference
wouldn't resolve unless `FB_TEST_0` is defined somewhere else. I put it back
in the merge order, right before `Programcontroller.txt`, with
`clean_testcase()` still applied to it. If you're intentionally keeping
test-FB definitions elsewhere, change `config.ST_MERGE_ORDER` back.

**2. `statement.sh`'s gcc failure branch was unreachable.**
`set -e` is active for the whole script but only disabled around the MATIEC
call — not around gcc. A non-zero gcc exit kills the script immediately,
before `gcc_status=$?` is ever read, so `if [ $gcc_status -ne 0 ]` never
fires. `matiec_runner.py` checks `subprocess.run(...).returncode` directly,
so this can't happen.

**3. `mv gcc_output.txt ../Output/result/` assumed that directory exists.**
Nothing created it. `matiec_runner.py`'s `build_with_gcc()` creates
`Output/result/` up front.

**4. `gcov softplc-Res0.gcno` hardcoded a filename that may not match
what your gcc/gcov actually emits.** `generate_coverage_summary()` globs
for `*.gcno` in the output directory instead of assuming a name.

**5. The big one — `common_ticktime__` units mismatch (in `matiec/tests/main.c`,
not your scripts, but it will silently break scan-based testing).**
Your MATIEC build's generated `Config0.c` defines:

    unsigned long long common_ticktime__ = 100000000ULL; /*ns*/

`matiec/tests/main.c` (the reference runtime harness) declares it as:

    extern int common_ticktime__;

and does **millisecond** arithmetic on it (`tv_sec = common_ticktime__/1000`).
Since the real value is in **nanoseconds**, a 100ms task interval gets
misread as a ~27.8-hour period — the periodic scan timer effectively never
fires within any normal test window, and softplc produces no observable
output at all. `runtime_patch/main.c` fixes the extern type and the
ns-to-timespec conversion. `matiec_runner.py` auto-seeds `Output/main.c`
from this fixed version **only if `Output/main.c` doesn't already exist** —
it won't overwrite a main.c you're already using. If you already have your
own and mutants aren't being detected (every run produces identical
output), check for exactly this bug.

## How mutant killing is determined

1. A baseline run (unmutated program) executes once; its stdout is captured.
2. Each mutant runs through the same pipeline (merge → MATIEC → gcc+gcov →
   run for `RUN_TIMEOUT_SECONDS`, using `stdbuf -oL` so printf output survives
   the timeout kill — same reason your original script used it).
3. A mutant is `killed_assertion` if any `FAIL_MARKERS` string
   (`config.FAIL_MARKERS`, default `["FAIL"]`) appears in its stdout,
   `killed_diverged` if its stdout differs from baseline without an explicit
   marker, or `survived` if stdout matches baseline exactly.

This means your test FB (`"3 Testcase.txt"`'s `FB_TEST_0` in the example I
tested with) needs to print something distinguishing — a fixed string, not
an interpolated one (see the note on inline C blocks below).

## A MATIEC constraint worth knowing about

Inline `{ printf(...) }` blocks in ST are spliced verbatim into the
generated C function — they do **not** have access to plain local ST
variables by name (e.g. `{printf("%d", scan_count)}` fails to compile with
"undeclared identifier"). This is exactly why your own working
`"4 Programcontroller.txt"` example only prints a fixed string. Keep
assertion output in your test FBs to fixed strings per branch
(`{printf("FAIL_SOMETHING\n");}`), which is all `FAIL_MARKERS` matching
needs anyway.

## Verified, not just written

I built this against a real MATIEC build (cloned + compiled from source),
a real gcc+gcov toolchain, and a minimal `PumpControl` FB test set matching
your file-naming convention. Confirmed working end to end: `TIMER_BYPASS`
and `TIMER_PRESET_CHANGE` mutants both compile, build, run, and get
correctly classified as killed via a real divergence in program output —
not simulated.

One caveat from that testing, noted for transparency rather than papered
over: the `TIMER_PRESET_CHANGE` mutant (reducing a preset from 3s to 1s)
was correctly killed, but triggered the "late activation" branch rather
than "early activation" — i.e. actual observed timing didn't line up
precisely with wall-clock expectations. The preset value itself was
verified correct in the generated C (`__time_to_timespec` showed the right
seconds argument for both), so this looks like scan-timing precision under
the `SIGEV_THREAD`-based periodic callback (thread-creation overhead per
tick) rather than a bug in the mutation logic — the important thing for
Task 1.3's purpose (is this mutant behaviorally distinguishable?) still
came back correct: killed. If precise timing matters for your
distinguishing-depth measurements, this is worth profiling further before
relying on tick-level timing accuracy.

## Not included here (flag if you want these next)

- `EDGE_POLARITY_FLIP` and `REL_OP_BOUNDARY` operators are implemented but
  only smoke-tested on synthetic input, not against your real programs —
  test against your actual `"2 Originalcode.txt"` before trusting the results.
- Counter (`CTU`/`CTD`) mutation operators from the earlier design aren't
  ported into this regex-based version yet — the earlier AST-based skeleton
  had a `CounterThresholdMutation` stub; add a regex equivalent the same way
  `TimerPresetMutation` is written if you need it.
- No DistinguishSearch-style *search* for a distinguishing input sequence —
  this campaign uses one fixed scenario (`Start := TRUE` for the whole run,
  from your `"3 Testcase.txt"`). Varying inputs across mutants would need
  the test FB itself to accept parameters, or multiple Testcase variants.
