#!/usr/bin/env python3
"""Serial independent Erlang VMs; one static failure mask per trial."""
import argparse,csv,json,os,platform,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--nodes',type=int,default=36);p.add_argument('--trials',type=int,default=8);p.add_argument('--timeout',type=int,default=300)
p.add_argument('--probabilities',nargs='+',type=float,default=[0,.01,.05,.1,.2,.4,1])
a=p.parse_args()
fields=['algorithm','topology','requested','nodes','trial','seed','failure_probability','termination','status','time_us','reached','stable','max_error','failed_links','total_links','sent','dropped']
with (ROOT/'results/experiments.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
 for alg in ['gossip','push-sum']:
  for top in ['full','2D','line','imp2D']:
   for prob in a.probabilities:
    completed=0
    for trial in range(1,a.trials+1):
     seed=2000+trial
     env=dict(os.environ,PROJECT2_SEED=str(seed),PROJECT2_TIMEOUT_MS=str(a.timeout),PROJECT2_TERMINATION='strict')
     r=subprocess.run([str(ROOT/'project2-bonus'),str(a.nodes),top,alg,str(prob)],env=env,cwd=ROOT,text=True,capture_output=True,timeout=a.timeout/1000+15)
     if r.returncode not in [0,2]:raise RuntimeError(r.stdout+r.stderr)
     vals=dict(item.split('=',1) for item in r.stdout.strip().split());vals['trial']=trial
     completed+=vals['status']=='converged';w.writerow({k:vals[k] for k in fields});f.flush()
    print(f'{alg:8} {top:5} p={prob:.2f}: {completed}/{a.trials} completed',flush=True)
otp=subprocess.check_output(['erl','+S','1','-noshell','-eval','io:format("~s",[erlang:system_info(otp_release)]),halt().'],text=True)
(ROOT/'results/environment.json').write_text(json.dumps({'platform':platform.platform(),'machine':platform.machine(),'otp':otp,'schedulers':4,'requested_nodes':a.nodes,'trials':a.trials,'timeout_ms':a.timeout,'probabilities':a.probabilities,'seeds':'2000 + trial','termination':'strict: gossip full coverage; push-sum first local termination','failure_model':'Each unique unordered neighbor pair independently fails with probability p before start and remains failed. Messages on failed pairs are discarded. No retries, repair or failure detection.','timed_scope':'Start after setup; end on convergence report or deadline. Router instrumentation is included. Statistics are a post-timing router snapshot.'},indent=2)+'\n')
