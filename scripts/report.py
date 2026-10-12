#!/usr/bin/env python3
"""Build a vector PDF directly from measured CSV data (requires ReportLab)."""
import csv,json,math,statistics
from collections import defaultdict
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor,Color
from reportlab.lib.utils import simpleSplit
ROOT=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader((ROOT/'results/experiments.csv').open()))
env=json.loads((ROOT/'results/environment.json').read_text())
groups=defaultdict(list)
for r in rows: groups[(r['algorithm'],r['topology'],int(r['nodes']))].append(r)
tops=['full','2D','line','imp2D']; colors=['#2563eb','#059669','#dc2626','#9333ea']
C=canvas.Canvas(str(ROOT/'Report.pdf'),pagesize=(612,792))
C.setTitle('COP5612 Project 2 - Gossip Simulator'); C.setAuthor('Omkar Salkade; Paresh Devlekar')
page=0
def start(title,sub):
    global page
    page+=1;C.setFillColor(HexColor('#0f172a'));C.setFont('Helvetica-Bold',23);C.drawString(48,738,title)
    C.setFont('Helvetica',10);C.setFillColor(HexColor('#475569'));C.drawString(48,716,sub)
    C.setStrokeColor(HexColor('#cbd5e1'));C.line(48,700,564,700)
def text(txt,y,width=516,size=10):
    C.setFont('Helvetica',size);C.setFillColor(HexColor('#334155'))
    for line in simpleSplit(txt,'Helvetica',size,width): C.drawString(48,y,line);y-=size*1.35
    return y-10
def heading(txt,y):
    C.setFont('Helvetica-Bold',13);C.setFillColor(HexColor('#0f172a'));C.drawString(48,y,txt);return y-23
def end():
    C.setFont('Helvetica',9);C.setFillColor(HexColor('#64748b'));C.drawString(48,30,'COP5612 | Fall 2026 | Omkar Salkade & Paresh Devlekar');C.drawRightString(564,30,str(page));C.showPage()
def stats(alg,top,n):
    rs=groups[(alg,top,n)]; good=[r for r in rs if r['status']=='converged']; ts=[int(r['time_us'])/1000 for r in good]
    return len(good),len(rs),statistics.mean(ts) if ts else None,min(ts) if ts else None,max(ts) if ts else None
start('Gossip Simulator','Measured convergence of asynchronous Erlang actors')
y=heading('Team and scope',670)
y=text('Omkar Salkade and Paresh Devlekar. Both gossip and push-sum run on full, 2D grid, line and imperfect 2D grid networks. Each vertex is a separate Erlang process; communication and coordination use asynchronous messages only.',y)
y=heading('What counts as convergence?',y)
y=text('Gossip: every actor has received the rumor at least once. Each informed actor sends to a random neighbor on a 1 ms timer and stops transmitting after ten receptions. Coverage convergence may precede local transmission termination. It is possible for a rumor to die out before full coverage; such a run is reported as a timeout.',y)
y=text('Push-sum: the first actor to complete three consecutive receptions with an absolute ratio change below 1e-10 terminates, and its notification ends the measured run. This is first local convergence, not proof of network-wide convergence. Initially s=i and w=1. Every receive adds the incoming mass, retains half, and sends half to a random neighbor. Only one actor is initially started. There is no periodic push-sum sender.',y)
y=text('The assignment specifies local termination but leaves global convergence unspecified. The default uses literal actor exit and first local termination: a single receive-driven message chain can otherwise disappear at its first terminated actor. An optional global mode preserves mass by keeping stable actors forwarding until all are stable; it is not used for these measurements.',y)
y=heading('Measurement protocol',y)
y=text(f'{len(rows)} serial runs: {env["trials"]} seeds per size, topology and algorithm; sizes '+', '.join(map(str,env['sizes']))+f'. Timeout: {env["timeout_ms"]/1000:g} s per run. Seeds are 1000 + trial. Timing uses erlang:monotonic_time(microsecond), from the first start message through the selected convergence notification. VM launch, compilation, actor/topology setup and cleanup are excluded.',y)
y=text(f'Host: {env["platform"]}; {env["machine"]}; Erlang/OTP {env["otp"]}; four VM schedulers. A seed fixes random streams but does not fix asynchronous scheduling. Curves show arithmetic means only where every trial succeeded; vertical bars show min/max. Failed sizes are marked at the timeout threshold, not treated as measured convergence.',y,size=10)
end()
def chart(alg,title):
    start(title,('First local termination vs. actor count' if alg=='push-sum' else 'Full rumor coverage vs. actor count')+' | logarithmic axes')
    left,bottom,width,height=87,245,450,405
    ns=sorted({n for a,t,n in groups if a==alg}); xmin,xmax=math.log10(min(ns)),math.log10(max(ns))
    times=[int(r['time_us'])/1000 for r in rows if r['algorithm']==alg and r['status']=='converged']
    failed=any(r['status']!='converged' for r in rows if r['algorithm']==alg)
    ymin=math.floor(math.log10(min(times))); ymax=math.ceil(math.log10(max(times+[env['timeout_ms']] if failed else times)))
    def x(n):return left+width*(math.log10(n)-xmin)/(xmax-xmin)
    def y(t):return bottom+height*(math.log10(max(t,10**ymin))-ymin)/(ymax-ymin)
    C.setFont('Helvetica',9)
    for v in range(ymin,ymax+1):
        yy=y(10**v);C.setStrokeColor(HexColor('#e2e8f0'));C.line(left,yy,left+width,yy);C.setFillColor(HexColor('#475569'));C.drawRightString(left-10,yy-3,f'{10**v:g}')
    for n in ns:
        xx=x(n);C.setStrokeColor(HexColor('#e2e8f0'));C.line(xx,bottom,xx,bottom+height);C.setFillColor(HexColor('#475569'));C.drawCentredString(xx,bottom-18,str(n))
    C.setStrokeColor(HexColor('#64748b'));C.line(left,bottom,left+width,bottom);C.line(left,bottom,left,bottom+height)
    C.setFont('Helvetica',11);C.drawCentredString(left+width/2,bottom-44,'Number of actors (log scale)');C.saveState();C.translate(30,bottom+height/2);C.rotate(90);C.drawCentredString(0,0,'Convergence time in milliseconds (log scale)');C.restoreState()
    for top,color in zip(tops,colors):
        C.setStrokeColor(HexColor(color));C.setFillColor(HexColor(color));C.setLineWidth(1.8);last=None
        for n in ns:
            ok,total,mean,lo,hi=stats(alg,top,n)
            xx=x(n)
            if ok==total:
                yy=y(mean)
                if last:C.line(*last,xx,yy)
                C.line(xx,y(lo),xx,y(hi));C.line(xx-3,y(lo),xx+3,y(lo));C.line(xx-3,y(hi),xx+3,y(hi));C.circle(xx,yy,3,fill=1,stroke=0);last=(xx,yy)
            else:
                last=None;yy=y(env['timeout_ms']);C.line(xx-4,yy-4,xx+4,yy+4);C.line(xx-4,yy+4,xx+4,yy-4)
    for i,(top,color) in enumerate(zip(tops,colors)):
        xx=87+(i%2)*235;yy=173-(i//2)*22;C.setStrokeColor(HexColor(color));C.setLineWidth(2);C.line(xx,yy,xx+24,yy);C.setFillColor(HexColor('#334155'));C.setFont('Helvetica',10);C.drawString(xx+33,yy-3,top)
    text('Dots: mean of all three successful trials. Bars: observed min/max, not confidence intervals. An X indicates at least one timeout; the point is drawn at the time limit and is excluded from the curve.',104,size=10)
    end()
chart('gossip','Rumor propagation')
chart('push-sum','Push-sum local stability')
start('Results and interpretation','Success rates, tested network sizes and observed limitations')
y=heading('Largest measured successful sizes',670)
C.setFont('Helvetica-Bold',10)
for x,t in [(48,'Topology'),(174,'Gossip'),(301,'Push-sum'),(428,'Success criterion')]:C.drawString(x,y,t)
y-=21
summary=[]
for top in tops:
    entries=[]
    for alg in ['gossip','push-sum']:
        allgood=[n for a,t,n in groups if a==alg and t==top and stats(a,t,n)[0]==stats(a,t,n)[1]]
        anygood=[n for a,t,n in groups if a==alg and t==top and stats(a,t,n)[0]>0]
        entries.append((max(allgood,default=0),max(anygood,default=0)))
    C.setFont('Helvetica',10)
    for x,t in [(48,top),(174,str(entries[0][0])),(301,str(entries[1][0])),(428,'3 / 3 runs')]:C.drawString(x,y,t)
    summary.append((top,entries));y-=23
C.setStrokeColor(HexColor('#cbd5e1'));C.line(48,y+6,564,y+6)
y=text('These are the largest tested sizes that converged in every trial, not proven capacity limits. The largest attempted size is '+str(max(env['sizes']))+' actors for every combination.',y-13,size=10)
y=heading('Observed findings',y)
for alg in ['gossip','push-sum']:
    n=max(env['sizes']);parts=[]
    for top in tops:
        ok,total,mean,_,_=stats(alg,top,n);parts.append(f'{top}: {ok}/{total} successes'+(f', mean {mean:.2f} ms' if mean is not None else ''))
    y=text(f'At {n} actors, {alg}: '+ '; '.join(parts)+'.',y,size=10)
y=text('Long paths restrict rumor propagation and slow ratio mixing. The full graph and random shortcut edges generally spread information faster. Local push-sum stability can also occur early, before accurate global mixing; a fast run with a large ratio error is not successful averaging. The imperfect grid has one fixed directed extra edge per actor, selected uniformly from non-self, non-grid neighbors; the added edge is not automatically reciprocal.',y,size=10)
y=text('The two algorithm curves are not directly comparable performance rankings: gossip measures coverage with timer-driven sends, while push-sum measures first local numerical stability using receive-driven sends. Differences reflect both protocol work and the termination criterion.',y,size=10)
y=heading('Numerical accuracy and limits',y)
good=[r for r in rows if r['algorithm']=='push-sum' and r['status']=='converged'];err=max(float(r['max_error']) for r in good)
y=text(f'The correct average is (N+1)/2. Across locally converged push-sum trials, the largest terminating actor estimate error was {err:.3g}. This diagnostic describes the first terminating actor only; it is not a network-wide error bound. Some terminating actors have large errors, exposing the weakness of local stability as a global stopping rule. The required local change threshold is not a global error bound.',y,size=10)
y=text('Timeouts are recorded as failures and excluded from means. Global mode is available for stronger experiments, but it changes local termination semantics and should be labeled separately. Three trials on one machine provide an initial comparison; larger samples, additional sizes and machines would strengthen conclusions. Raw data and scripts are included so results can be reproduced and extended.',y,size=10)
end();C.save()
with (ROOT/'results/summary.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['algorithm','topology','nodes','successes','trials','mean_success_ms','min_success_ms','max_success_ms'])
    for key in sorted(groups):w.writerow([*key,*stats(*key)])
print('Created Report.pdf and results/summary.csv')
