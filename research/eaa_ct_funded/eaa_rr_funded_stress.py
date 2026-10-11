#!/usr/bin/env python3
from eaa_rr_gate_funded import *

SELECT=('A_ALL_ORIGINAL','E_ALL_ABSRR2','F_ALL_FADER1p5_ABSRR2')
OUT=[]
for policy in SELECT:
 population=filter_policy(T,policy)
 for period in ('trailing_365d','calendar_2026','last_30d'):
  days=sessions(period)
  trades=[t for t in population if PERIOD_START[period]<=t['entry']<CUTOFF]
  for mod,qty in [('fixed',3),('fixed',4),('riskcap',200),('riskcap',250)]:
   for cost in (0,1,2,4):
    for cap in (None,500):
     res=[]
     for i in range(len(days)-14):
      ds=days[i:i+15];obs=[t for t in trades if ds[0]<=t['market_day']<=ds[-1]]
      res.append(run_window(obs,ds,POLICIES[policy]['models'],mod,qty,extra_per_mnq=cost,day_profit_stop=cap))
     n=len(res);passed=[x for x in res if x['outcome']=='PASS'];failed=[x for x in res if x['outcome']=='FAIL']
     OUT.append({'policy':policy,'period':period,'qmode':mod,'qvalue':qty,'add_cost_per_MNQ':cost,'daily_profit_stop':cap or 'NONE',
     'windows':n,'pass_n':len(passed),'fail_n':len(failed),'alive_n':n-len(passed)-len(failed),'pass_pct':round(100*len(passed)/n,2),'fail_pct':round(100*len(failed)/n,2),
     'median_pass_day':statistics.median(x['days'] for x in passed) if passed else None,'median_exec':statistics.median(x['trades'] for x in res),
     'median_skip':statistics.median(x['skipped'] for x in res),'mean_dll_hits':round(statistics.mean(x['dll_hits'] for x in res),2)})
 print('DONE',policy,flush=True)
path=D/'D01016_EAA_RR_GATE_FUNDED_STRESS_2026-10-11.csv'
with open(path,'w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(OUT[0]));w.writeheader();w.writerows(OUT)
print('SAVED',path)
for p in ('trailing_365d','calendar_2026','last_30d'):
 for policy in SELECT:
  for kind,q in [('fixed',3),('riskcap',250)]:
   sel=[x for x in OUT if x['period']==p and x['policy']==policy and x['qmode']==kind and x['qvalue']==q and x['daily_profit_stop']=='NONE']
   print(p,policy,kind,q,[(z['add_cost_per_MNQ'],z['pass_pct'],z['fail_pct'],z['median_exec']) for z in sel])
 for policy in SELECT:
  v0=next(x for x in OUT if x['period']==p and x['policy']==policy and x['qmode']=='fixed' and x['qvalue']==3 and x['add_cost_per_MNQ']==0 and x['daily_profit_stop']=='NONE')
  v1=next(x for x in OUT if x['period']==p and x['policy']==policy and x['qmode']=='fixed' and x['qvalue']==3 and x['add_cost_per_MNQ']==0 and x['daily_profit_stop']==500)
  print('PROFITSTOP',p,policy,'none',v0['pass_pct'],'cap500',v1['pass_pct'])
