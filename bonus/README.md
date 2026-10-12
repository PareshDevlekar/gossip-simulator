# COP5612 Project 2 - Bonus: Permanent Connection Failures

**Team: Omkar Salkade and Paresh Devlekar**

This separate bonus simulator implements one parameter-controlled failure model: permanent connection outages. The original project and its measurements are unchanged.

## Run

Requires Erlang/OTP (`erl`, `erlc`, `escript`) on PATH. No Erlang dependencies.

```sh
./project2-bonus 36 full gossip 0.10
./project2-bonus 36 2D push-sum 0.05
./project2-bonus 36 line gossip 1
./project2-bonus 36 imp2D push-sum 0
```

Format: `project2-bonus numNodes topology algorithm failureProbability`.

The first three arguments have the base-project meanings. `failureProbability` is a decimal number between 0 and 1, inclusive. `0` means no failed connections; `1` means every inter-actor connection fails. Grid sizes round up to a square.

A connection is a unique unordered pair of neighboring actor IDs. Each connection independently fails with probability p during setup, before the timed run. Its failure lasts for the entire run. If an imperfect-grid connection exists only in one direction, its pair can still fail; failure does not introduce a reverse connection. Realized failed-link counts need not equal p times the total link count.

Neighbor lists are retained. Actors still select random original neighbors. A dedicated Erlang transport actor forwards messages on working connections and discards messages on failed connections. Actors receive no failure notification, acknowledgement, retry or repaired route. This models permanent communication failure, not deliberate removal and replacement of neighbors.

All simulation concurrency uses Erlang actors and asynchronous messages. Python only runs experiments, draws the report and creates the archive.

## Algorithm and stopping rules

- Gossip: one actor initially receives the rumor. Every informed actor sends on a 1 ms timer until ten receptions. The run completes when all actors have received the rumor. Stopped transmitters remain mailbox endpoints. Outages can disconnect the network or cause incomplete propagation in a connected network.
- Push-sum: initial s=i and w=1. Every mass reception adds, halves and forwards values. The default strict mode ends at the first actor meeting three consecutive ratio changes below 1e-10. This is local stability, not proof of accurate network-wide averaging. A dropped mass message destroys the sole circulating message chain, so the remaining actors can stay idle until timeout.
- `PROJECT2_TERMINATION=global` is also supported. Stable actors continue forwarding, and the coordinator waits for all current stability reports. This changes literal local actor termination. The included bonus experiments use strict mode only.
- The baseline and bonus have the same protocol rules, but bonus transport instrumentation adds scheduling overhead. Compare failure levels within the bonus experiment, not its timings against uninstrumented base timings.

## Settings and output

```sh
PROJECT2_SEED=2001 PROJECT2_TIMEOUT_MS=300 ./project2-bonus 36 full gossip 0.2
```

Defaults: seed 42, timeout 30,000 ms, strict termination. Per-actor seeds control neighbor selections; a fixed seed cannot fix asynchronous scheduling. With the same seed and topology, failure levels use the same per-connection draws, producing nested failure masks.

Output includes convergence status, requested and actual node counts, microseconds, reached actors, stable actors, stable-report estimate error, p, failed/total connections, attempted routed messages (`sent`) and dropped messages. `sent` includes dropped attempts. Transport counters are a snapshot taken just after timing ends; they are not an exact end-of-timing message count.

Exit codes: 0 for the selected convergence condition, 2 for timeout, 1 for invalid input or runtime/build error. A push-sum `converged` result means first local stability only. `max_error=0` with `stable=0` means there is no stable estimate, not that the average is correct.

## Tests and reproducibility

```sh
make test
python3 scripts/benchmark.py
python3 scripts/report.py   # Requires ReportLab
python3 scripts/package.py
```

Tests check p=0 and p=1 masks, bidirectional connection identities, fixed-seed masks, all algorithms/topologies, all-links-failed message dropping, one-node behavior, cleanup, and invalid probabilities.

Default experiments: 36 actual actors, four topologies, both algorithms, eight trials per combination, seeds 2001-2008, p in {0, .01, .05, .1, .2, .4, 1}, 300 ms timeout. The p=0 control and p=1 endpoint use the same transport instrumentation. Runs execute serially in independent Erlang VMs.

```sh
python3 scripts/benchmark.py --nodes 64 --trials 20 --timeout 1000 --probabilities 0 0.01 0.05 0.1 0.2 0.4 1
```

This replaces the raw results. Regenerate the PDF and archive afterward. The report derives numerical findings from the CSV. Completion rates are observed within the chosen deadline; a timeout does not prove that eventual convergence is impossible.

## Files

`Report-bonus.pdf` explains the model, tests, parameter sweep, plots, observations and limitations. `project2-bonus.zip` includes this README, runnable source, tests, scripts, report and raw data. The report is also supplied separately at the project root.

The failure model uses permanent connection outages. Dropped mass is not recovered.
