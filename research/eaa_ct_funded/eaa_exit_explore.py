#!/usr/bin/env python3
"""Conditional entry exit replay using TradingView 1m master + Work CT Scalper trade CSV.
Fully reconstructs bracket+flat for 474/476 historical fills. Not a new entry backtest.
"""
from eaa_funded_v2 import *
import time
MASTER=D/'MNQ_1m_MASTER_2025-10-01_to_2026-10-01 (1)(1).csv'
M={}
for row in csv.DictReader(open(MASTER)):
 tm=dt.datetime.fromisoformat(row['time']).astimezone(TZ)
 M[tm]=tuple(float(row[c]) for c in ('open','high','low','close'))
TT=[t for t in T if t['entry'] in M and t['exit'] in M];assert len(TT)==476

def replay(t,tp_factor=1.,sl_factor=1.,be_at=None,time_stop=None):
 ep=t['entry_px'];s=1 if t['side']=='LONG' else -1
 risk_points=abs(ep-t['sl']);target_points=abs(ep-t['tp'])
 sl=round(round((ep-s*risk_points*sl_factor)*4)/4,2)
 tp=round(round((ep+s*target_points*tp_factor)*4)/4,2)
 if s*(ep-sl)<=0 or s*(tp-ep)<=0:return None
 be_active=False;trail_stop=None
 max_minutes=min(500,int((max(TT[-1]['exit'],t['exit'])-t['entry']).total_seconds()//60)+1)
 adverse=0;favorable=0
 for n in range(max_minutes):
  stamp=t['entry']+dt.timedelta(minutes=n)
  candle=M.get(stamp)
  if candle is None:return None
  o,h,l,c=candle
  active_sl=sl if not be_active else (max(sl,ep) if s==1 else min(sl,ep))
  hit_sl=(l<=active_sl if s==1 else h>=active_sl)
  hit_tp=(h>=tp+0.25 if s==1 else l<=tp-0.25)
  adverse=min(adverse,(l-ep)*s*2 if s==1 else (ep-h)*-2) if False else min(adverse,((l-ep)*2 if s==1 else (ep-h)*2))
  favorable=max(favorable,(h-ep)*2 if s==1 else (ep-l)*2)
  if hit_sl:
   px=(min(o,active_sl)-0.25 if s==1 else max(o,active_sl)+0.25)
   pnl=round((px-ep)*s*2-1,2)
   return {'exit':stamp,'pnl':pnl,'reason':'SL_BE' if be_active and active_sl!=sl else 'SL','duration':n,'mae':min(adverse,pnl+1),'mfe':favorable,'risk':abs(ep-sl)*2+1}
  if hit_tp:
   pnl=round((tp-ep)*s*2-1,2)
   return {'exit':stamp,'pnl':pnl,'reason':'TP','duration':n,'mae':adverse,'mfe':favorable,'risk':abs(ep-sl)*2+1}
  nystamp=stamp.astimezone(NY)
  if nystamp.hour==16 and nystamp.minute>=43:
   px=c-s*0.25
   pnl=round((px-ep)*s*2-1,2)
   return {'exit':stamp,'pnl':pnl,'reason':'SESSION','duration':n,'mae':adverse,'mfe':favorable,'risk':abs(ep-sl)*2+1}
  if time_stop and n+1>=time_stop:
   nextc=M.get(stamp+dt.timedelta(minutes=1))
   if nextc is None:return None
   px=nextc[0]-s*.25
   pnl=round((px-ep)*s*2-1,2)
   return {'exit':stamp+dt.timedelta(minutes=1),'pnl':pnl,'reason':'TIMESTOP','duration':n+1,'mae':adverse,'mfe':favorable,'risk':abs(ep-sl)*2+1}
  if be_at is not None and not be_active and favorable>=risk_points*2*be_at:
   be_active=True # effective NEXT minute, after bar confirmed.
 return None

def stats(tt):
 n=len(tt);p=[t['pnl'] for t in tt];wins=sum(v>0 for v in p);gp=sum(v for v in p if v>0);gl=-sum(v for v in p if v<0)
 eq=peak=dd=0
 for v in p:eq+=v;peak=max(peak,eq);dd=max(dd,peak-eq)
 return {'n':n,'net':round(sum(p),2),'pf':round(gp/gl,4) if gl else None,'win_pct':round(100*wins/n,2) if n else None,'mean_pnl':round(statistics.mean(p),2) if n else None,'closed_dd':round(dd,2)}

if __name__=='__main__':
 exact=0
 for t in TT:
  z=replay(t)
  if z and (z['exit'],z['reason'],z['pnl'])==(t['exit'],t['exit_reason'] if t['exit_reason'] in ('SL','TP') else 'SESSION',t['pnl']):exact+=1
 print('REPLAY PARITY EXACT',exact,'/',len(TT))
 VARS=[('BASE',1.,1.,None,None)]
 VARS += [('TPx'+str(f),f,1.,None,None) for f in (.5,.625,.75,.875,1.0)]
 VARS += [('SLx'+str(f),1.,f,None,None) for f in (.6,.75,.875,1.0)]
 VARS += [('BE_'+str(x),1.,1.,x,None) for x in (.5,.75,1.,1.25,1.5)]
 VARS += [('TIME_'+str(x),1.,1.,None,x) for x in (5,10,15,20,30,45,60,90,120)]
 # 3 combo candidate early exit gates
 VARS += [('TPx'+str(tp)+'_BE'+str(be),tp,1.,be,None) for tp in (.75,.875) for be in (.75,1.)]
 VARS += [('SLx'+str(sl)+'_TPx'+str(tp),tp,sl,None,None) for sl in (.75,.875) for tp in (.75,.875)]
 print('VARIANTS',len(VARS))
 rows=[];trade_outputs={}
 for name,tp,sl,be,ts in VARS:
  out=[]
  for t in TT:
   z=replay(t,tp,sl,be,ts)
   if z is None:continue
   out.append({**t,**z,'original_exit':t['exit'],'original_pnl':t['pnl']})
  assert len(out)==len(TT),(name,len(out))
  trade_outputs[name]=out
  for period,pred in [('all_master',lambda t:True),('dev_oct25_jun26',lambda t:t['entry']<dt.datetime(2026,7,1,tzinfo=TZ)),('recent_jul_sep26',lambda t:t['entry']>=dt.datetime(2026,7,1,tzinfo=TZ)),('2026_all',lambda t:t['entry'].year==2026),('last90_to_oct1',lambda t:t['entry']>=dt.datetime(2026,7,1,tzinfo=TZ))]:
   for model in ['ALL','FADE','DIV','ABSORB','AGG','TRAP']:
    val=[t for t in out if pred(t) and (model=='ALL' or t['model']==model)]
    if not val:continue
    overlap_count=sum(1 for j,t in enumerate(out[:-1]) if t in val and t['exit']>out[j+1]['entry'])
    m=stats(val)
    row={'variant':name,'model':model,'period':period,'tp_factor':tp,'sl_factor':sl,'be_at_R':be,'time_stop_minutes':ts,'overlap_count':overlap_count,**m}
    rows.append(row)
 path=D/'D01010_EAA_EXIT_VARIANTS_CONDITIONAL_2026-10-11.csv'
 with open(path,'w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 print('WRITTEN',path)
 for model in ('ALL','FADE','DIV','ABSORB'):
  base={p:next(r for r in rows if r['variant']=='BASE' and r['model']==model and r['period']==p) for p in ('dev_oct25_jun26','recent_jul_sep26')}
  print('\nMODEL',model,'BASE',base)
  cand=[r for r in rows if r['model']==model and r['period']=='dev_oct25_jun26' and r['variant']!='BASE' and r['overlap_count']==0]
  cand.sort(key=lambda z:(-(z['net']-base['dev_oct25_jun26']['net']),-z['pf']))
  for r in cand[:12]:
   newer=next(z for z in rows if z['model']==model and z['period']=='recent_jul_sep26' and z['variant']==r['variant'])
   print(r['variant'],'DEV',r['n'],r['net'],r['pf'],r['closed_dd'],'RECENT',newer['n'],newer['net'],newer['pf'],newer['closed_dd'],'overlap',newer['overlap_count'])
 # Save selected replay data for further funded sim, immutable model-specific changes names.
 selected=['BASE','TIME_30','BE_1.0','TPx0.75','SLx0.875','TPx0.875_BE1.0']
 trade_path=D/'D01011_EAA_EXIT_REPLAY_SELECTED_TRADES_2026-10-11.csv'
 with open(trade_path,'w',encoding='utf-8',newline='') as f:
  fields=['variant','id','entry','exit','market_day','model','side','entry_px','sl','tp','risk','pnl','mae','mfe','reason','original_exit','original_pnl']
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for v in selected:
   for t in trade_outputs[v]: w.writerow({k:v if k=='variant' else t.get(k) for k in fields})
 print('WRITTEN',trade_path)
