#!/usr/bin/env python3
"""Run serial, independent Erlang VMs; retain successes and failures alike."""
import argparse, csv, os, platform, subprocess, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument('--sizes',nargs='+',type=int,default=[16,64,144,256,400,900])
p.add_argument('--trials',type=int,default=3)
p.add_argument('--timeout',type=int,default=8000)
a=p.parse_args()
(ROOT/'results').mkdir(exist_ok=True)
fields=['algorithm','topology','requested','nodes','trial','seed','status','time_us','reached','stable','max_error']
with (ROOT/'results/experiments.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=fields); writer.writeheader()
    for alg in ['gossip','push-sum']:
        for top in ['full','2D','line','imp2D']:
            for n in a.sizes:
                for trial in range(1,a.trials+1):
                    seed=1000+trial
                    env=dict(os.environ,PROJECT2_SEED=str(seed),PROJECT2_TIMEOUT_MS=str(a.timeout),PROJECT2_TERMINATION="strict")
                    r=subprocess.run([str(ROOT/'project2'),str(n),top,alg],cwd=ROOT,env=env,text=True,capture_output=True,timeout=a.timeout/1000+20)
                    if r.returncode not in [0,2]: raise RuntimeError(r.stdout+r.stderr)
                    vals=dict(item.split('=',1) for item in r.stdout.strip().split())
                    vals['trial']=trial; writer.writerow({k:vals[k] for k in fields}); f.flush()
                print(f'{alg:8} {top:5} n={n:5}: {vals["status"]}, {int(vals["time_us"])/1000:.2f} ms',flush=True)
version=subprocess.check_output(['erl','+S','1','-noshell','-eval','io:format("~s",[erlang:system_info(otp_release)]),halt().'],text=True)
(ROOT/'results/environment.json').write_text(json.dumps({'platform':platform.platform(),'machine':platform.machine(),'otp':version,'schedulers':4,'trials':a.trials,'timeout_ms':a.timeout,'sizes':a.sizes,'seed_per_trial':'1000 + trial','timer':'erlang:monotonic_time(microsecond)','termination':'strict: gossip full coverage; push-sum first local actor termination','timed_scope':'initial start message through coordinator convergence; excludes VM launch, compilation, topology setup and cleanup'},indent=2)+'\n')
