# COP5612 - Project 2: Gossip Simulator

**Fall 2026 - Omkar Salkade and Paresh Devlekar**

## Run

Requires Erlang/OTP with `erl`, `erlc`, and `escript` on PATH. Tested with the OTP version recorded in `results/environment.json`. No third-party Erlang dependencies.

```sh
./project2 100 full gossip
./project2 100 2D push-sum
./project2 100 line gossip
./project2 100 imp2D push-sum
```

From another directory, invoke the executable by its path. If an unzip utility removes executable permissions, use `chmod +x project2` or `escript project2 ...`.

Arguments: a positive integer, one of `full`, `2D`, `line`, `imp2D`, and one of `gossip`, `push-sum`. Names are case sensitive. Grid topologies round up to the next square and print both requested and actual node counts. Node values use the **actual** count and IDs 1 through N.

Output reports `time_us` in microseconds, status, node counts, number reached, number stable, estimate error, random seed, and termination mode. In strict push-sum mode, `stable=1` describes first local convergence. Exit codes: 0 = convergence, 1 = invalid input/build/runtime failure, 2 = convergence timeout. A timeout is not a successful convergence measurement.

```sh
PROJECT2_SEED=1001 PROJECT2_TIMEOUT_MS=8000 ./project2 400 imp2D push-sum
```

Default termination mode: `strict`. Optional `PROJECT2_TERMINATION=global` is described below. Default seed: 42. Default timeout: 30,000 ms. Different scheduling can produce different measurements even with the same seed. The executable selects four Erlang schedulers and compiles the source in memory, so no build step or beam files are needed.

## What is working

- One Erlang actor per network node; exclusively asynchronous message passing for algorithm state and coordinator notifications. No ETS, shared-state workers, threads, or other parallel frameworks.
- All four topologies. Full topology samples directly from a tuple of actors, avoiding an O(N^2) adjacency list. Grids use orthogonal neighbors without row wrapping. Line endpoints have one neighbor.
- Imperfect grids add a fixed directed random edge to each actor, excluding self and existing grid neighbors. If no such actor exists, no extra edge is possible. The extra edge is not automatically reciprocal.
- Gossip starts at one random actor. Informed actors transmit on a 1 ms Erlang timer until they have received ten copies of the rumor.
- Push-sum initializes s=i, w=1, starts at one actor, adds incoming mass and sends half on each reception. Three successive ratio changes strictly below 1e-10 produce a local convergence report.
- Monotonic microsecond timing, deterministic per-actor random seeds, bounded runs, monitored workers, teardown, topology/algorithm checks, raw benchmark data, and a four-page PDF with two vector plots.

## Convergence and termination

The assignment gives local termination rules but does not specify one global convergence rule. This implementation makes the following choices explicit:

**Gossip:** global convergence means every actor has heard the rumor at least once. Every actor still follows the ten-reception transmission cutoff, but the simulator may stop before all actors reach ten. Gossip can die out before full coverage; the run is recorded as a timeout.

**Push-sum (default `strict`):** each actor literally exits after its ratio changes by less than 1e-10 on three consecutive receptions. The first such actor notification ends the measured run. This measures **first local convergence**. Other actors may still be unstable, and the estimate may differ from the correct average. With one receive-driven circulating message chain, waiting for every actor to exit can stall after the first actor terminates. The assignment does not specify the global criterion; this choice is explicit in both output documentation and the report.

**Optional `global` mode:** `PROJECT2_TERMINATION=global ./project2 100 full push-sum` waits for every actor's latest local stability report. Stable actors continue accepting and forwarding mass, and later unstable receptions revoke their reports. This conserves mass but extends the assignment's literal local actor-exit rule. The included measurements use the default strict mode. Both modes ultimately stop and clean up all remaining actors.

`max_error` is the difference between the first terminating actor's ratio and the known average (N+1)/2 in strict mode; in global mode it is the maximum difference over the latest stable reports. It is a diagnostic, not an extra stopping condition or a simultaneous state snapshot. During a timeout it covers only currently stable actors; zero with `stable=0` means no available stable estimates. Local changes below 1e-10 do not guarantee global average error below 1e-10.

Time starts after actors and their topology are ready, immediately before the initial start message. It ends when the coordinator observes full rumor coverage or first local push-sum termination (all local stability reports in optional global mode). Compilation, Erlang VM launch, topology setup, and teardown are excluded. Coordinator notification latency is included. Setup readiness is acknowledged by every actor.

## Validation and experiments

```sh
make test
python3 scripts/benchmark.py
# Report generation requires Python's reportlab package:
python3 scripts/report.py
python3 scripts/package.py
```

Benchmark defaults: 16, 64, 144, 256, 400, and 900 actual actors; three independent VM runs per combination in strict mode; seeds 1001-1003; an eight-second timeout. Runs are serial. Python only orchestrates experiments, generates the PDF, and packages files; it does not simulate either algorithm.

To extend the experiment:

```sh
python3 scripts/benchmark.py --sizes 16 64 256 1024 --trials 5 --timeout 30000
python3 scripts/report.py
python3 scripts/package.py
```

The benchmark replaces the CSV and environment metadata. Regenerate the PDF and update the table below if experiment sizes change. Full connectivity is implicit; imperfect-grid rejection sampling and all topology setup are outside timing. Memory and VM process limits eventually constrain capacity; the tested sizes below are observations, not maximum theoretical limits.

## Largest networks measured

| Topology | Gossip: all 3 runs converged | Push-sum: all 3 runs locally converged | Largest attempted |
| --- | ---: | ---: | ---: |
| full | 900 | 900 | 900 |
| 2D | 900 | 900 | 900 |
| line | 900 | 900 | 900 |
| imp2D | 900 | 900 | 900 |

“Locally converged” means the first push-sum actor met the specified stability rule; it does not guarantee an accurate network-wide average. See the report for ratio errors and success rates.

See `Report.pdf` for means, spreads, failures, findings and limitations. Raw observations are in `results/experiments.csv`, aggregated observations in `results/summary.csv`, and environment details in `results/environment.json`.

## Files

- `project2`: runnable escript entry point.
- `src/gossip_sim.erl`: simulator, actors and topology generation.
- `tests/simulator_tests.escript`: topology, rounding, singleton, convergence and timeout checks.
- `scripts/`: reproducible benchmark, vector PDF generation and archive creation.
- `Report.pdf`: report with team names and two convergence plots.
- `project2.zip`: archive with source, README, report, tests, scripts and measurements.

The bonus implementation is in `bonus/`, with its own report and archive.
