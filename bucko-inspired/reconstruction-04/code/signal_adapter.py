"""Read-only instrumentation around the byte-frozen RECON03 signal reference."""
from pathlib import Path
import importlib.util,sys,json,time
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('br3_frozen',ROOT/'frozen/reference_replay.py')
frozen=importlib.util.module_from_spec(spec);sys.modules[spec.name]=frozen;spec.loader.exec_module(frozen)
BASE_ENGINE=frozen.PriceEngine

def wilder_rsi(c,n=14):
 diff=np.diff(c,prepend=np.nan);up=np.maximum(diff,0);down=np.maximum(-diff,0);out=np.full(len(c),np.nan)
 if len(c)<=n:return out
 u=float(np.mean(up[1:n+1]));v=float(np.mean(down[1:n+1]))
 for i in range(n,len(c)):
  if i>n:u=(u*(n-1)+up[i])/n;v=(v*(n-1)+down[i])/n
  out[i]=100 if v==0 and u>0 else 100-100/(1+u/v) if v>0 else np.nan
 return out

def run_original(prices):
 trace=[]
 class TraceEngine(BASE_ENGINE):
  def step(self,*args):
   event=super().step(*args)
   trace.append((self.lo,self.hi))
   return event
 d=prices.reset_index(drop=True).copy();d['time']=pd.to_datetime(d.time,utc=True)
 frozen.PriceEngine=TraceEngine
 try:r=frozen.replay(d[['time','open','high','low','close','volume']])
 finally:frozen.PriceEngine=BASE_ENGINE
 r['swing_low_close']=[x[0] for x in trace];r['swing_high_close']=[x[1] for x in trace]
 r['time']=d.time
 for col in ['open','high','low','close','volume']:r[col]=d[col]
 r['symbol']=d['symbol'] if 'symbol' in d else 'MNQ_MASTER_UNKNOWN_ROLL'
 e21=d.close.ewm(span=21,adjust=False).mean();e50=d.close.ewm(span=50,adjust=False).mean()
 r['ema_regime']=np.where(e21>e50,'BULL',np.where(e21<e50,'BEAR','NEUTRAL'))
 r['chop_regime']=np.where(r.er<.25,'CHOP','TREND')
 n=d.time.dt.tz_convert('America/New_York');minute=n.dt.hour*60+n.dt.minute
 r['score_session']=(n.dt.dayofweek<5)&(minute>=570)&(minute<960)
 r['signal_model']='PRIMARY_ORIGINAL'
 return r

def pine_semantics(original):
 r=original.copy();n=len(r);c=r.close
 newr=wilder_rsi(c.to_numpy());prev=np.r_[np.nan,newr[:-1]];momknown=np.isfinite(prev)
 h=r.set_index('time').close.resample('15min',closed='left',label='right').agg(['last','count']);h=h[h['count']>0].copy();h['ema']=h['last'].ewm(span=50,adjust=False).mean();h['n']=np.arange(len(h))
 h=h.reset_index().rename(columns={'time':'ht_closed_at'});ht=pd.merge_asof(r[['time']],h,left_on='time',right_on='ht_closed_at',direction='backward');hk=(ht.n>=49).to_numpy()
 mL=r.mask_L.to_numpy().astype(int);mS=r.mask_S.to_numpy().astype(int)
 newL=mL-(mL&2)-(mL&512)+2*(momknown&(newr>50)&(newr>prev))+512*(hk&(ht['last']>ht.ema))
 newS=mS-(mS&2)-(mS&512)+2*(momknown&(newr<50)&(newr<prev))+512*(hk&(ht['last']<ht.ema))
 r['mask_L']=np.asarray(newL,dtype=int);r['mask_S']=np.asarray(newS,dtype=int)
 r['score_L']=[int(x).bit_count() for x in newL];r['score_S']=[int(x).bit_count() for x in newS]
 known=6+(np.arange(n)>=49).astype(int)+momknown.astype(int)+np.isfinite(r.rvol).astype(int)+hk.astype(int)
 r['known']=known
 ok=(~r.bad)&(r.contiguous>=50)&(known==10)&np.isfinite(r.er)&np.isfinite(r.rvol)
 common=(~ok).astype(int)+4*(r.er<.25).astype(int)+32*(r.raw_mask==3).astype(int)
 r['block_L']=common+2*(r.score_L<6).astype(int);r['block_S']=common+2*(r.score_S<6).astype(int)
 r['approved_mask']=((r.raw_mask%2==1)&(r.block_L==0)).astype(int)+2*((r.raw_mask>=2)&(r.block_S==0)).astype(int)
 r['signal_model']='PINE_SEMANTICS_04_1'
 return r

def main():
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--dataset',choices=['master','legacy','excerpt'],required=True);a=ap.parse_args()
 folder=ROOT/'results/signals';folder.mkdir(parents=True,exist_ok=True)
 if a.dataset=='master':
  d=pd.read_csv(ROOT/'data/master.csv.gz');groups=[('master',d)]
 elif a.dataset=='excerpt':
  d=pd.read_csv(ROOT/'data/recon03_excerpt.csv.gz');groups=[('excerpt',d)]
 else:
  d=pd.read_csv(ROOT/'data/legacy_calendar_roll.csv.gz');groups=list(d.groupby('symbol',sort=False))
 summary=[]
 for name,g in groups:
  t=time.monotonic();r=run_original(g);r.to_csv(folder/f'{a.dataset}_{name}.csv.gz',index=False,compression={'method':'gzip','mtime':0})
  item=dict(dataset=a.dataset,segment=name,bars=len(r),raw_bars=int((r.raw_mask>0).sum()),approved_bars=int((r.approved_mask>0).sum()),seconds=time.monotonic()-t)
  if a.dataset=='master':
   p=pine_semantics(r);p.to_csv(folder/'master_pine_semantics.csv.gz',index=False,compression={'method':'gzip','mtime':0});item['pine_semantics_approved']=int((p.approved_mask>0).sum());item['approval_disagreements']=int((p.approved_mask!=r.approved_mask).sum());item['mask_disagreements']=int(((p.mask_L!=r.mask_L)|(p.mask_S!=r.mask_S)).sum())
   differences=pd.DataFrame({'time':r.time,'original_approved':r.approved_mask,'pine_semantics_approved':p.approved_mask,'original_scoreL':r.score_L,'approx_pine_scoreL':p.score_L,'original_scoreS':r.score_S,'approx_pine_scoreS':p.score_S});differences[differences.original_approved!=differences.pine_semantics_approved].to_csv(ROOT/'results/parity_differences.csv',index=False)
  summary.append(item);print(json.dumps(item),flush=True)
 (ROOT/f'results/{a.dataset}_signal_summary.json').write_text(json.dumps(summary,indent=2))
if __name__=='__main__':main()
