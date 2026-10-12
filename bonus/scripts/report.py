#!/usr/bin/env python3
"""Vector plots and findings derived only from bonus experiment records."""
import csv,json,statistics,math
from collections import defaultdict
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import simpleSplit
ROOT=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader((ROOT/'results/experiments.csv').open()))
env=json.loads((ROOT/'results/environment.json').read_text())
N=int(rows[0]['nodes']);TRIALS=env['trials']
assert {0.0,0.01,0.1,0.4,1.0} <= set(env['probabilities']), 'Report comparisons require p=0, .01, .1, .4 and 1'
groups=defaultdict(list)
for r in rows:groups[r['algorithm'],r['topology'],float(r['failure_probability'])].append(r)
tops=['full','2D','line','imp2D'];colors=['#2563eb','#059669','#dc2626','#9333ea']
def metrics(alg,top,p):
 rs=groups[alg,top,p];good=[r for r in rs if r['status']=='converged']
 ts=[int(r['time_us'])/1000 for r in good]
 return {'completed':len(good),'trials':len(rs),'completion_pct':100*len(good)/len(rs),'coverage_pct':100*statistics.mean(int(r['reached'])/int(r['nodes']) for r in rs),'mean_completed_ms':statistics.mean(ts) if ts else None,'mean_dropped':statistics.mean(int(r['dropped']) for r in rs),'max_completed_error':max((float(r['max_error']) for r in good),default=None)}
C=canvas.Canvas(str(ROOT/'Report-bonus.pdf'),pagesize=(612,792));C.setTitle('COP5612 Bonus - Permanent Connection Failures');C.setAuthor('Omkar Salkade; Paresh Devlekar');page=0
def start(title,sub):
 global page
 page+=1;C.setFillColor(HexColor('#0f172a'));C.setFont('Helvetica-Bold',22);C.drawString(48,738,title);C.setFont('Helvetica',10);C.setFillColor(HexColor('#475569'));C.drawString(48,716,sub);C.setStrokeColor(HexColor('#cbd5e1'));C.line(48,700,564,700)
def text(txt,y,size=10):
 C.setFont('Helvetica',size);C.setFillColor(HexColor('#334155'))
 for line in simpleSplit(txt,'Helvetica',size,516):C.drawString(48,y,line);y-=size*1.4
 return y-10
def head(txt,y):
 C.setFont('Helvetica-Bold',12);C.setFillColor(HexColor('#0f172a'));C.drawString(48,y,txt);return y-22
def end():
 C.setFont('Helvetica',9);C.setFillColor(HexColor('#64748b'));C.drawString(48,30,'COP5612 | Bonus | Omkar Salkade & Paresh Devlekar');C.drawRightString(564,30,str(page));C.showPage()
start('Permanent connection failures','A parameter-controlled Erlang actor experiment')
y=head('Team and implemented model',671)
y=text('Omkar Salkade and Paresh Devlekar. This bonus implements permanent connection failure only. Each unique unordered pair of neighboring actors fails independently with probability p before execution. The failure remains for the entire run.',y)
y=text('Actors keep their original neighbor lists. An Erlang transport actor forwards messages over working connections and discards messages over failed connections. No acknowledgement, retry, repaired route or failure detection is added. An imperfect-grid extra connection can be directed; its endpoint pair shares the same failure state wherever that pair occurs.',y)
y=head('Algorithms and completion definitions',y)
y=text('Gossip sends a single rumor on 1 ms timers and stops each sender after ten receptions. Completion means every actor received the rumor at least once. Push-sum adds received (s,w), keeps half and sends half. Strict completion means the first actor has three consecutive ratio changes below 1e-10 and exits. It is local stability, not accurate network-wide averaging.',y)
y=text('Push-sum starts one receive-driven message chain. A failed transfer destroys that chain and loses the transferred mass. Without recovery, all actors can then wait indefinitely. Gossip has multiple active timer-driven senders, so one discarded copy does not necessarily stop propagation.',y)
y=head('Experiment design',y)
y=text(f'{len(rows)} serial runs: {env["requested_nodes"]} requested actors (grid sizes round upward if needed), four topologies, two algorithms, {env["trials"]} trials per parameter value. Tested p values: '+', '.join(f'{p:g}' for p in env['probabilities'])+f'. Timeout: {env["timeout_ms"]} ms. Seeds: 2000 + trial. Each run uses a fresh Erlang VM and strict termination.',y)
y=text('The p=0 control uses the same transport actor as failure runs. With a fixed seed and topology, masks are nested across p because every connection uses the same draw. Asynchronous schedules still vary. Timing starts after actor setup and ends on completion notification or timeout. Setup and VM launch are excluded; transport overhead is included.',y)
y=head('Tests and measurement limits',y)
y=text('Automated checks cover no-failure and all-failure masks, unordered endpoint identity, seeded reproducibility, both algorithms on all topologies, actual message drops, singleton behavior, process cleanup and invalid probabilities. Transport counters are a snapshot just after timing ends. Timeouts are failures within this deadline, not measured convergence times.',y)
y=text(f'Host: {env["platform"]}; {env["machine"]}; Erlang/OTP {env["otp"]}; four schedulers. {TRIALS} trials provide coarse rates in {100/TRIALS:g} percentage-point steps. Results are an initial experiment on one machine, not general reliability guarantees.',y)
end()
def plot(alg,key,label,base):
 left,width,height=87,450,190;bottom=base;maxp=max(p for p in env['probabilities'] if p<1);ps=[p for p in env['probabilities'] if p<1]
 def x(p):return left+width*p/maxp
 def y(v):return bottom+height*v/100
 C.setFillColor(HexColor('#0f172a'));C.setFont('Helvetica-Bold',12);C.drawString(left,bottom+height+17,alg)
 C.setFont('Helvetica',9)
 for v in [0,25,50,75,100]:
  C.setStrokeColor(HexColor('#e2e8f0'));C.line(left,y(v),left+width,y(v));C.setFillColor(HexColor('#475569'));C.drawRightString(left-9,y(v)-3,str(v))
 for i in range(5):
  p=i*maxp/4;C.setStrokeColor(HexColor('#e2e8f0'));C.line(x(p),bottom,x(p),bottom+height);C.setFillColor(HexColor('#475569'));C.drawCentredString(x(p),bottom-17,f'{p:.2f}')
 C.setStrokeColor(HexColor('#64748b'));C.line(left,bottom,left+width,bottom);C.line(left,bottom,left,bottom+height)
 C.setFont('Helvetica',10);C.drawCentredString(left+width/2,bottom-37,'Permanent connection failure probability p')
 C.saveState();C.translate(31,bottom+height/2);C.rotate(90);C.drawCentredString(0,0,label);C.restoreState()
 for top,color in zip(tops,colors):
  C.setStrokeColor(HexColor(color));C.setFillColor(HexColor(color));C.setLineWidth(1.5);prev=None
  for p in ps:
   point=(x(p),y(metrics(alg,top,p)[key]))
   if prev:C.line(*prev,*point)
   C.circle(*point,2.7,stroke=0,fill=1);prev=point
 def legend():
  for i,(top,color) in enumerate(zip(tops,colors)):
   xx=87+i*115;C.setStrokeColor(HexColor(color));C.line(xx,base-62,xx+20,base-62);C.setFillColor(HexColor('#334155'));C.setFont('Helvetica',9);C.drawString(xx+27,base-65,top)
 legend()
start('Completion rate vs. failure','Parameter sweep | complete runs divided by all trials')
plot('gossip','completion_pct','Completed runs (%)',445)
plot('push-sum','completion_pct','Locally completed runs (%)',150)
text(f'Each dot summarizes {TRIALS} trials. Lines connect tested levels; they do not predict untested values. The p=1 endpoint is omitted here for low-probability detail: all runs timed out at p=1.',58,size=9)
end()
start('Coverage vs. failure','Mean fraction of actors reached across all trials, including timeouts')
plot('gossip','coverage_pct','Mean actors reached (%)',445)
plot('push-sum','coverage_pct','Mean actors reached (%)',150)
text(f'Coverage is recorded at completion or timeout. It describes message reach, not ratio accuracy. All p=1 runs reached only the initially activated actor (1/{N} = {100/N:.2f}%).',58,size=9)
end()
start('Findings and limitations','Numerical comparisons derived from the raw experiment records')
y=head('Completion and conditional time at p=0.10',672)
C.setFont('Helvetica-Bold',9)
for x,t in [(48,'Topology'),(154,'Gossip complete'),(268,'Gossip mean ms'),(386,'Push-sum complete'),(493,'Push mean ms')]:C.drawString(x,y,t)
y-=20
for top in tops:
 g=metrics('gossip',top,.1);p=metrics('push-sum',top,.1)
 vals=[top,f'{g["completed"]}/{g["trials"]}',f'{g["mean_completed_ms"]:.2f}' if g['mean_completed_ms'] is not None else '-',f'{p["completed"]}/{p["trials"]}',f'{p["mean_completed_ms"]:.2f}' if p['mean_completed_ms'] is not None else '-']
 C.setFont('Helvetica',9)
 for x,v in zip([48,154,268,386,493],vals):C.drawString(x,y,v)
 y-=21
y=text('Means above include only completed runs. A dash means there was no completed run. These conditional means can favor easy cases; compare completion and coverage as well as speed.',y-6)
y=head('Interesting observations',y)
gf=metrics('gossip','full',.4);gl=metrics('gossip','line',.1);gg=metrics('gossip','2D',.4);gi=metrics('gossip','imp2D',.4)
y=text(f'Connectivity redundancy matters. At p=0.40, full-network gossip completed {gf["completed"]}/{gf["trials"]} runs, regular-grid gossip {gg["completed"]}/{gg["trials"]}, and imperfect-grid gossip {gi["completed"]}/{gi["trials"]}. At only p=0.10, line gossip completed {gl["completed"]}/{gl["trials"]}. A single line connection failure separates the network; full graphs offer many alternative routes.',y)
y=text(f'For {N} line actors there are {N-1} connections. The probability that none fails is (1-p)^(N-1). At p=0.10 this is about {100*.9**(N-1):.2f}%. This explains the sharp line decline: repeated gossip cannot cross a permanently failed bridge. The formula is a connectivity probability, not a guaranteed completion probability.',y)
pf=metrics('push-sum','full',.01);pb=metrics('push-sum','full',0)
y=text(f'Push-sum is fragile even in a redundant graph. Full-network local completion fell from {pb["completed"]}/{pb["trials"]} at p=0 to {pf["completed"]}/{pf["trials"]} at p=0.01. One lost transfer can stop its only message chain. Independent of graph connectivity, the unmodified receive-driven protocol lacks a mechanism to restart communication or recover mass.',y)
y=text('Gossip coverage can remain high while completion falls: many actors may receive the rumor, but one unreachable actor prevents full coverage. Extra imperfect-grid edges help in some trials, but eight trials do not establish a universal ranking or monotonic trend.',y)
y=head('Accuracy, limitations and reproduction',y)
errors=[float(r['max_error']) for r in rows if r['algorithm']=='push-sum' and r['status']=='converged'];maxerr=max(errors,default=0)
y=text(f'The largest reported error among locally completed push-sum runs was {maxerr:.3g}, relative to the expected average {(N+1)/2:g}. Local stability is not correct averaging. Message loss also violates mass conservation. Dropped mass is not recovered.',y)
y=text(f'The {env["timeout_ms"]} ms deadline, small network, {TRIALS} seeds and centralized transport actor limit generalization. Longer deadlines could change some completion rates. Zero drops do not prove zero failed connections: unused connections may have failed. Repeat with more sizes, seeds and deadlines to strengthen conclusions.',y)
y=text('Reproduce with make test, python3 scripts/benchmark.py, python3 scripts/report.py and python3 scripts/package.py. The archive includes source, tests, CSV measurements and machine metadata. Report generation requires ReportLab.',y)
end();C.save()
summary=[]
for key in sorted(groups):summary.append(dict(algorithm=key[0],topology=key[1],failure_probability=key[2],**metrics(*key)))
with (ROOT/'results/summary.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
print('Created Report-bonus.pdf and results/summary.csv')
