import csv,datetime as dt,statistics,collections
from eaa_funded_v2 import *
p=D/'MNQ_1m_MASTER_2025-10-01_to_2026-10-01 (1)(1).csv'
M={}
for row in csv.DictReader(open(p)):
 tm=dt.datetime.fromisoformat(row['time']).astimezone(TZ)
 M[tm]=tuple(float(row[col]) for col in ('open','high','low','close'))
TT=[t for t in T if t['entry'] in M and t['exit'] in M]
print('BARS',len(M),'TRADES FULLY IN MASTER',len(TT),collections.Counter(t['exit_reason'] for t in TT))

def replay(t, tp_r=None, sl_mult=1., max_minutes=350, trail=None):
 entry=t['entry'];ep=t['entry_px'];s=1 if t['side']=='LONG' else -1
 based=abs(ep-t['sl']); sl=t['sl'] if sl_mult==1 else ep-s*based*sl_mult
 tp=t['tp'] if tp_r is None else ep+s*based*tp_r
 # align hypothetical limit and stop with tick grid
 sl=round(round(sl*4)/4,2);tp=round(round(tp*4)/4,2)
 if (s==1 and (sl>=ep or tp<=ep)) or (s==-1 and (sl<=ep or tp>=ep)):return None
 for n in range(max_minutes):
  time=entry+dt.timedelta(minutes=n)
  candle=M.get(time)
  if candle is None:return ('DATA_GAP',time,0,n)
  o,h,l,c=candle
  # no same bar TP after stop if ambiguous (assume stop first)
  hitstop=(l<=sl if s==1 else h>=sl)
  hittp=(h>=tp+0.25 if s==1 else l<=tp-0.25)
  if hitstop:
   px=(min(o,sl)-0.25 if s==1 else max(o,sl)+0.25)
   pnl=round((px-ep)*s*2-1,2)
   return ('SL',time,pnl,n)
  if hittp:
   pnl=round((tp-ep)*s*2-1,2)
   return ('TP',time,pnl,n)
  # basic hard cutoff, already strategy condition f_eaaSessionOpen (16:44 NY close). Stressed replay flat 16:43 NY.
  ny=time.astimezone(NY)
  if ny.hour==16 and ny.minute>=43:
   px=c-0.25*s
   return ('SESSION_OR_TEST_END',time,round((px-ep)*s*2-1,2),n)
 return ('TIMEOUT',entry+dt.timedelta(minutes=max_minutes),0,max_minutes)

for require in ('SL','TP','ANY'):
 tr=[t for t in TT if (require=='ANY' or t['exit_reason']==require)]
 d=[]
 for t in tr:
  result=replay(t)
  d.append((t,result))
 exact=sum(z is not None and t['exit']==z[1] and t['exit_reason']==z[0] for t,z in d)
 same_dir=sum(z is not None and t['exit_reason']==z[0] for t,z in d)
 pnldiff=[abs(t['pnl']-z[2]) for t,z in d if z is not None and t['exit']==z[1] and t['exit_reason']==z[0]]
 print('GATE',require,'n',len(tr),'same reason',same_dir,'exact time + reason',exact, 'pct',round(100*exact/len(tr),2) if tr else None,'exacttime matching pnl',collections.Counter(pnldiff).most_common(8))
 print('EXAMPLES BAD',[(t['id'],t['model'],t['entry'].isoformat(),t['exit_reason'],t['exit'].isoformat(),z) for t,z in d if not z or t['exit']!=z[1] or t['exit_reason']!=z[0]][:12])
