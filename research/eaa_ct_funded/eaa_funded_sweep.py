#!/usr/bin/env python3
from eaa_funded_v2 import *

# Test multiple model combinations, static MNQ and structural stop-dollar-cap, official challenge profile.
COMBOS=list(itertools.chain.from_iterable(itertools.combinations(MODELS,k) for k in range(1,7)))
SIZES=[('fixed',x) for x in (1,2,3,4,5,6,8,10)] + [('riskcap',x) for x in (75,100,125,150,175,200,250,300,400)]
rows=[]
for pc in ('trailing_365d','calendar_2026','last_30d'):
 for combo in COMBOS:
  for qmod,qval in SIZES:
   row,_=evaluate(pc,combo,qmod,qval)
   rows.append(row)
 print('COMPLETE',pc, len([x for x in rows if x['period']==pc]),flush=True)
path=D/'D01009_EAA_FUNDED_SWEEP_63x17x3_2026-10-11.csv'
with open(path,'w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print('OUTPUT',path)
for p in ('trailing_365d','calendar_2026','last_30d'):
 print('\nPERIOD',p)
 sel=[r for r in rows if r['period']==p]
 best=sorted(sel,key=lambda a:(-a['pass_pct'],a['fail_pct'],-a['mean_end_balance']))
 print('GLOBAL BEST 12')
 for r in best[:12]:print(r['models'],r['qmode'],r['qvalue'],r['pass_pct'],r['fail_pct'],r['median_pass_day'],r['median_executed'],r['windows'])
 print('ALL MODELS BY PASS')
 for r in sorted((r for r in sel if r['models']=='+'.join(MODELS)),key=lambda a:-a['pass_pct'])[:12]:print(r['qmode'],r['qvalue'],r['pass_pct'],r['fail_pct'],r['median_pass_day'],r['median_executed'])
 print('OTHER KEY COMBOS OPTIMUM')
 for m in ['FADE+DIV+TRAP','FADE+DIV','FADE+ABSORB','DIV+ABSORB','FADE+DIV+ABSORB','FADE+DIV+TRAP+ABSORB','ABSORB','FADE','DIV']:
  bs=sorted((r for r in sel if r['models']==m),key=lambda a:(-a['pass_pct'],a['fail_pct']))
  if bs:
   for r in bs[:2]:print(r['models'],r['qmode'],r['qvalue'],r['pass_pct'],r['fail_pct'],r['median_pass_day'],r['median_executed'])
