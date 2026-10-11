#!/usr/bin/env python3
from eaa_funded_v2 import *

POLICIES={
 'A_ALL_ORIGINAL':{'models':MODELS,'thresholds':{}},
 'B_FADE_ABSORB':{'models':('FADE','ABSORB'),'thresholds':{}},
 'C_FADE_ABSORB_ABSRR2':{'models':('FADE','ABSORB'),'thresholds':{'ABSORB':2.0}},
 'D_FADE_ABSORB_FADER1p5_ABSRR2':{'models':('FADE','ABSORB'),'thresholds':{'FADE':1.5,'ABSORB':2.0}},
 'E_ALL_ABSRR2':{'models':MODELS,'thresholds':{'ABSORB':2.0}},
 'F_ALL_FADER1p5_ABSRR2':{'models':MODELS,'thresholds':{'FADE':1.5,'ABSORB':2.0}},
 'G_FADER1p5_DIVR1p5_ABSRR2':{'models':('FADE','DIV','ABSORB'),'thresholds':{'FADE':1.5,'DIV':1.5,'ABSORB':2.0}},
 'H_ALL_RR1p5':{'models':MODELS,'thresholds':dict.fromkeys(MODELS,1.5)},
 'I_ALL_ABSRR1p5':{'models':MODELS,'thresholds':{'ABSORB':1.5}},
 'J_FADE_DIV_TRAP':{'models':('FADE','DIV','TRAP'),'thresholds':{}},
}
SIZ=[('fixed',2),('fixed',3),('fixed',4),('fixed',5),('fixed',6),('riskcap',150),('riskcap',175),('riskcap',200),('riskcap',250),('riskcap',300)]

def filter_policy(trades,p):
 cfg=POLICIES[p]
 return [t for t in trades if t['model'] in cfg['models'] and t['rr_proxy']>=cfg['thresholds'].get(t['model'],0.)]

def met(trades):
 n=len(trades);gp=sum(t['pnl'] for t in trades if t['pnl']>0);gl=-sum(t['pnl'] for t in trades if t['pnl']<0)
 return {'trades':n,'net':round(sum(t['pnl'] for t in trades),2),'pf':round(gp/gl,3) if gl else None}

if __name__=='__main__':
 rows=[];modelmetrics=[]
 for policy in POLICIES:
  selected=filter_policy(T,policy)
  for period,start,end in [('2024',dt.datetime(2024,1,1,tzinfo=TZ),dt.datetime(2025,1,1,tzinfo=TZ)),('2025',dt.datetime(2025,1,1,tzinfo=TZ),dt.datetime(2026,1,1,tzinfo=TZ)),('2026',C2026,CUTOFF),('2026_H1',C2026,dt.datetime(2026,7,1,tzinfo=TZ)),('2026_H2',dt.datetime(2026,7,1,tzinfo=TZ),CUTOFF),('last30',MONTH_START,CUTOFF)]:
   st=[t for t in selected if start<=t['entry']<end]
   modelmetrics.append({'policy':policy,'period':period,**met(st)})
  for period in PERIODS:
   days=sessions(period)
   tt=[t for t in selected if PERIOD_START[period]<=t['entry']<CUTOFF]
   for mod,q in SIZ:
    outs=[]
    for i in range(len(days)-14):
     d=days[i:i+15]
     trades=[t for t in tt if d[0]<=t['market_day']<=d[-1]]
     outs.append(run_window(trades,d,POLICIES[policy]['models'],mod,q))
    n=len(outs);passed=[x for x in outs if x['outcome']=='PASS'];failed=[x for x in outs if x['outcome']=='FAIL']
    rows.append({'policy':policy,'period':period,'qmode':mod,'qvalue':q,'windows':n,'pass':len(passed),'fail':len(failed),'alive':n-len(passed)-len(failed),
    'pass_pct':round(len(passed)/n*100,2),'fail_pct':round(len(failed)/n*100,2),'median_pass_day':statistics.median(z['days'] for z in passed) if passed else None,
    'median_trades':statistics.median(z['trades'] for z in outs),'median_skipped':statistics.median(z['skipped'] for z in outs)})
  print('POLICY_DONE',policy,flush=True)
 with open(D/'D01014_EAA_PINE_SAFE_RR_GATES_FUNDED_2026-10-11.csv','w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 with open(D/'D01015_EAA_RR_GATES_PERIOD_METRICS_2026-10-11.csv','w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(modelmetrics[0]));w.writeheader();w.writerows(modelmetrics)
 for p in ('trailing_365d','calendar_2026','last_30d'):
  print('\nPERIOD',p)
  for pol in POLICIES:
   sel=[x for x in rows if x['period']==p and x['policy']==pol]
   best=sorted(sel,key=lambda v:(-v['pass_pct'],v['fail_pct']))[0]
   base=next(x for x in sel if x['qmode']=='fixed' and x['qvalue']==3)
   print('POL',pol,'BEST',best['qmode'],best['qvalue'],best['pass_pct'],best['fail_pct'],'FIXED3',base['pass_pct'],base['fail_pct'])
 print('MODEL PERIOD METRICS')
 for row in modelmetrics:
  if row['period'] in ('2024','2025','2026','2026_H1','2026_H2','last30'): print(row)
