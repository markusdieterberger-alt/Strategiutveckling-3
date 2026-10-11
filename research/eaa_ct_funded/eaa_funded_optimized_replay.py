#!/usr/bin/env python3
"""Post-change funded proxy on common master data, not new Pine/TV entries.
All variant exits are at or before original TV exit; same original-entry opportunities used.
"""
from eaa_exit_explore import *
from eaa_funded_v2 import run_window

base=dict((t['id'],t) for t in TT)

CONFIGS={
 'TV_ORIGINAL':{},
 'FADE_SL_0875':{'FADE':{'sl_factor':.875}},
 'DIV_TP_0875':{'DIV':{'tp_factor':.875}},
 'DIV_SL0875_TP0875':{'DIV':{'sl_factor':.875,'tp_factor':.875}},
 'ABSORB_TP_0625':{'ABSORB':{'tp_factor':.625}},
 'FADE_SL0875_DIV_TP0875':{'FADE':{'sl_factor':.875},'DIV':{'tp_factor':.875}},
 'FADE_SL0875_DIV_SL0875_TP0875':{'FADE':{'sl_factor':.875},'DIV':{'sl_factor':.875,'tp_factor':.875}},
 'ALL3_DEV_CHANGE':{'FADE':{'sl_factor':.875},'DIV':{'sl_factor':.875,'tp_factor':.875},'ABSORB':{'tp_factor':.625}},
 'ABSORB_TP_050':{'ABSORB':{'tp_factor':.5}},
 'ABSORB_TIMESTOP_15':{'ABSORB':{'time_stop':15}},
 'FADE_TIMESTOP_60':{'FADE':{'time_stop':60}}
}

def build_config(name):
 change=CONFIGS[name];ret=[]
 for t in TT:
  if t['model'] in change:
   z=replay(t,**change[t['model']])
   assert z and z['exit']<=t['exit'],(name,t['id'],z,t['exit'])
   new={**t,**z}
  else:new={**t}
  ret.append(new)
 return ret

STUDY={
 '365d_common':(dt.datetime(2025,10,2,tzinfo=TZ),dt.datetime(2026,10,2,tzinfo=TZ)),
 '2026_common':(dt.datetime(2026,1,1,tzinfo=TZ),dt.datetime(2026,10,2,tzinfo=TZ)),
 '30d_common':(dt.datetime(2026,9,1,tzinfo=TZ),dt.datetime(2026,10,2,tzinfo=TZ)),
 '2026_H1':(dt.datetime(2026,1,1,tzinfo=TZ),dt.datetime(2026,7,1,tzinfo=TZ)),
 '2026_JulSep':(dt.datetime(2026,7,1,tzinfo=TZ),dt.datetime(2026,10,2,tzinfo=TZ))
}
MODEL_ARMS={
 'ALL':MODELS,
 'FADE_DIV_TRAP':('FADE','DIV','TRAP'),
 'FADE_ABSORB':('FADE','ABSORB'),
 'FADE_DIV_TRAP_ABSORB':('FADE','DIV','TRAP','ABSORB'),
 'FADE_DIV_ABSORB':('FADE','DIV','ABSORB'),
 'DIV_ABSORB':('DIV','ABSORB'),
}
Q=[('fixed',2),('fixed',3),('fixed',4),('fixed',5),('fixed',6),('riskcap',150),('riskcap',175),('riskcap',200),('riskcap',250),('riskcap',300)]

def days_for_window(start,end):
 nd=start.astimezone(NY).date();last=(end-dt.timedelta(minutes=1)).astimezone(NY).date()
 return [nd+dt.timedelta(days=i) for i in range((last-nd).days+1) if (nd+dt.timedelta(days=i)).weekday()<5]

def custom_eval(trades,period,arm,mod,qty,extra=0.,intraday='liquidate_DLL',daycap=None):
 s,e=STUDY[period];daylist=days_for_window(s,e)
 n=15;starts=[];results=[]
 pop=[t for t in trades if s<=t['entry']<e and t['model'] in MODEL_ARMS[arm]]
 for i in range(len(daylist)-14):
  days=daylist[i:i+n]
  samp=[t for t in pop if days[0]<=t['market_day']<=days[-1]]
  value=run_window(samp,days,MODEL_ARMS[arm],mod,qty,extra,daycap,intraday)
  value['start']=str(days[0]);results.append(value)
 total=len(results);passes=[v for v in results if v['outcome']=='PASS'];fails=[v for v in results if v['outcome']=='FAIL']
 return {'period':period,'arm':arm,'qmode':mod,'qvalue':qty,'cost_extra':extra,'intraday':intraday,'profit_stop':daycap or 'NONE',
 'n_eligible_trades':len(pop),'windows':total,'pass_n':len(passes),'fail_n':len(fails),'alive_n':total-len(passes)-len(fails),
 'pass_pct':round(len(passes)/total*100,2) if total else None,'fail_pct':round(len(fails)/total*100,2) if total else None,
 'median_pass_day':statistics.median(z['days'] for z in passes) if passes else None,
 'mean_bal':round(statistics.mean(z['balance'] for z in results),2) if results else None,
 'median_executed':statistics.median(z['trades'] for z in results) if results else None,
 'median_skipped':statistics.median(z['skipped'] for z in results) if results else None,
 'dll_hits_sum':sum(z['dll_hits'] for z in results),
 'MLL_fail_n':sum(z['reason'].startswith('MLL') for z in fails)},results

if __name__=='__main__':
 configs={name:build_config(name) for name in CONFIGS}
 outputs=[]
 for study in ('365d_common','2026_common','30d_common','2026_H1','2026_JulSep'):
  for config,trades in configs.items():
   for arm in MODEL_ARMS:
    for mode,qty in Q:
     r,_=custom_eval(trades,study,arm,mode,qty)
     outputs.append({'config':config,**r})
  print('DONE',study,len([r for r in outputs if r['period']==study]),flush=True)
 dest=D/'D01012_EAA_FUNDED_AFTER_EXIT_OPTIMIZATION_2026-10-11.csv'
 with open(dest,'w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(outputs[0]));w.writeheader();w.writerows(outputs)
 print('SAVED',dest)
 for period in ('365d_common','2026_common','30d_common'):
  print('\nPERIOD',period)
  # fixed reference settings comparability
  for arm in ('ALL','FADE_DIV_TRAP','FADE_ABSORB'):
   for config in ('TV_ORIGINAL','FADE_SL_0875','DIV_TP_0875','ABSORB_TP_0625','FADE_SL0875_DIV_TP0875','ALL3_DEV_CHANGE'):
    best=sorted((x for x in outputs if x['period']==period and x['arm']==arm and x['config']==config),key=lambda a:(-a['pass_pct'],a['fail_pct'],-a['mean_bal']))[0]
    print('TOP',arm,config,best['qmode'],best['qvalue'],best['pass_pct'],best['fail_pct'],best['median_pass_day'],best['median_executed'])
 # STRESS for pre-selected configurations and fixed policies, no reoptimization of stress.
 out_stress=[]
 fixed_comps=[('TV_ORIGINAL','ALL','fixed',3),('TV_ORIGINAL','ALL','riskcap',250),('TV_ORIGINAL','FADE_ABSORB','riskcap',250),('FADE_SL0875_DIV_TP0875','ALL','fixed',3),('FADE_SL0875_DIV_TP0875','ALL','riskcap',250),('ALL3_DEV_CHANGE','ALL','fixed',3),('ALL3_DEV_CHANGE','FADE_ABSORB','riskcap',250)]
 for period in ('365d_common','2026_common','30d_common'):
  for cn,arm,mode,q in fixed_comps:
   for extra in (0,1,2,4):
    for how in ('liquidate_DLL','MAE_hard'):
     rr,window=custom_eval(configs[cn],period,arm,mode,q,extra,intraday=how)
     out_stress.append({'config':cn,**rr})
  print('STRESS_DONE',period)
 fp=D/'D01013_EAA_FUNDED_STRESS_AND_POLICY_2026-10-11.csv'
 with open(fp,'w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(out_stress[0]));w.writeheader();w.writerows(out_stress)
 print('SAVED',fp)
 print('STRESS SAMPLE')
 for x in out_stress:
  if x['period']=='2026_common' and x['config']=='TV_ORIGINAL' and x['arm']=='ALL' and x['qmode']=='fixed' and x['qvalue']==3:print(x)
