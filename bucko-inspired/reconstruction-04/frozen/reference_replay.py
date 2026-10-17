"""BR3.1 diagnostic reference; no fills, exits, PnL or parameter search.

Independent Python implementation of documented price rules. It is NOT a Pine
compiler or a certified TradingView emulator. EWM/RSI initialization, HTF sessions,
history start and data vendors still need native field-by-field parity checks.
"""
from dataclasses import dataclass
from pathlib import Path
import argparse
import hashlib
import json
import math
import numpy as np
import pandas as pd

@dataclass
class Zone:
    lo: float
    hi: float
    born: int
    kind: int
    touched: bool = False

class PriceEngine:
    def __init__(self, tick=0.25, left=2, right=2, cap=12):
        self.tick,self.left,self.right,self.cap=tick,left,right,cap
        self.zones=[]; self.bars=[]; self.contiguous=0
        self.hi=self.lo=None; self.hi_broken=self.lo_broken=False; self.structure=0
    def add(self,z):
        self.zones.append(z)
        same=[x for x in self.zones if x.kind==z.kind]
        if len(same)>self.cap: self.zones.remove(same[0])
    def step(self,t,o,h,l,c,v):
        i=len(self.bars)
        gap=bool(self.bars and t-self.bars[-1][0]!=60)
        bad=not all(math.isfinite(x) for x in (o,h,l,c,v)) or h<max(o,c) or l>min(o,c) or h<l or v<0
        self.contiguous=0 if bad else 1 if gap else self.contiguous+1
        if gap or bad:
            self.zones.clear(); self.hi=self.lo=None
            self.hi_broken=self.lo_broken=False; self.structure=0
        event=dict(bosL=False,bosS=False,sweepL=False,sweepS=False,fvgL=False,fvgS=False,sdL=False,sdS=False)
        self.bars.append((t,o,h,l,c,v))
        if not bad:
            event['bosL']=self.hi is not None and not self.hi_broken and c>self.hi
            event['bosS']=self.lo is not None and not self.lo_broken and c<self.lo
            event['sweepL']=self.lo is not None and l<self.lo and c>self.lo
            event['sweepS']=self.hi is not None and h>self.hi and c<self.hi
            if event['bosL']: self.hi_broken=True; self.structure=1
            if event['bosS']: self.lo_broken=True; self.structure=-1
            kept=[]
            for z in self.zones:
                fvg=abs(z.kind)==1; bullish=z.kind>0
                invalid=(l<=z.lo if bullish else h>=z.hi) if fvg else (c<z.lo if bullish else c>z.hi)
                if i-z.born>(100 if fvg else 200) or invalid: continue
                touch=h>=z.lo and l<=z.hi
                reject=touch and not z.touched and (c>z.hi if bullish else c<z.lo)
                if reject: event[{1:'fvgL',-1:'fvgS',2:'sdL',-2:'sdS'}[z.kind]]=True
                if touch: z.touched=True
                kept.append(z)
            self.zones=kept
            if self.contiguous>=3:
                prev=self.bars[-3]
                if l-prev[2]>=self.tick: self.add(Zone(prev[2],l,i,1))
                if prev[3]-h>=self.tick: self.add(Zone(h,prev[3],i,-1))
            width=self.left+self.right+1
            if self.contiguous>=width:
                window=self.bars[-width:]; pivot=window[self.left]
                others=window[:self.left]+window[self.left+1:]
                if all(pivot[2]>b[2] for b in others):
                    self.hi=pivot[2]; self.hi_broken=False
                    self.add(Zone(min(self.hi-self.tick,max(pivot[1],pivot[4])),self.hi,i,-2))
                if all(pivot[3]<b[3] for b in others):
                    self.lo=pivot[3]; self.lo_broken=False
                    self.add(Zone(self.lo,max(self.lo+self.tick,min(pivot[1],pivot[4])),i,2))
        return dict(**event,structure=self.structure,contiguous=self.contiguous,gap=gap,bad=bad,zones=len(self.zones))

def footprint_decision(core,mode,buy=None,sell=None,total=None,delta=None,threshold=.10):
    """Minimal arithmetic/NA policy shared by the documented pilot's default mode."""
    known=all(x is not None and math.isfinite(x) for x in (buy,sell,total,delta))
    known=known and total>0 and min(buy,sell)>=0
    if known:
        tol=max(1e-6,abs(total)*1e-8)
        known=abs(buy+sell-total)<=tol and abs(buy-sell-delta)<=tol
    passed=known and (delta/total>=threshold if core==1 else delta/total<=-threshold)
    return core if core and (mode=='Quality only' or passed) else 0

def load_prices(path):
    df=pd.read_csv(path)
    df['time']=pd.to_datetime(df.time,utc=True)
    return df

def audit(df,path):
    a=df[['open','high','low','close']]
    return dict(sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),rows=len(df),start=str(df.time.min()),end=str(df.time.max()),monotonic=bool(df.time.is_monotonic_increasing),duplicate_times=int(df.time.duplicated().sum()),missing_cells=int(df.isna().sum().sum()),ohlc_errors=int(((df.high<a[['open','close']].max(axis=1))|(df.low>a[['open','close']].min(axis=1))|(df.high<df.low)).sum()),tick_errors=int((np.abs(a/.25-np.round(a/.25))>1e-7).sum().sum()),negative_volume=int((df.volume<0).sum()),zero_volume=int((df.volume==0).sum()),gaps_gt_1m=int((df.time.diff().dt.total_seconds()>60).sum()),contract_column='symbol' in df.columns)

def replay(df):
    d=df.copy().reset_index(drop=True); c=d.close
    ema21=c.ewm(span=21,adjust=False).mean(); ema50=c.ewm(span=50,adjust=False).mean()
    change=c.diff(); up=change.clip(lower=0).ewm(alpha=1/14,adjust=False,min_periods=14).mean(); down=(-change.clip(upper=0)).ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    rsi=100-100/(1+up/down); rsi=rsi.mask((down==0)&(up>0),100)
    rv=d.volume/d.volume.rolling(20).mean().shift(1)
    path=change.abs().rolling(14).sum(); er=(c-c.shift(14)).abs()/path; er=er.mask(path==0,0)
    h=d.set_index('time').close.resample('15min',closed='left',label='right').agg(['last','count'])
    h=h[h['count']==15].copy(); h['ema']=h['last'].ewm(span=50,adjust=False).mean(); h['n']=np.arange(len(h)); h=h.reset_index().rename(columns={'time':'ht_closed_at'})
    ht=pd.merge_asof(d[['time']],h,left_on='time',right_on='ht_closed_at',direction='backward')
    local=d.time.dt.tz_convert('America/New_York'); minute=local.dt.hour*60+local.dt.minute
    session=(local.dt.dayofweek<5)&(minute>=570)&(minute<960)
    engine=PriceEngine(); out=[]
    for i,b in enumerate(d.itertuples(index=False)):
        event=engine.step(int(b.time.timestamp()),b.open,b.high,b.low,b.close,b.volume)
        span=b.high-b.low; body=abs(b.close-b.open)
        rejL=span>0 and b.close>b.open and min(b.open,b.close)-b.low>=max(body,.25) and b.close>=b.low+span*2/3
        rejS=span>0 and b.close<b.open and b.high-max(b.open,b.close)>=max(body,.25) and b.close<=b.low+span/3
        hknown=bool(ht.loc[i,'n']>=49)
        prevRSI=rsi.iloc[i-1] if i else np.nan
        L=[bool(b.close>ema50[i] and ema21[i]>ema50[i]) if i>=49 else None, bool(rsi[i]>50 and rsi[i]>prevRSI) if np.isfinite(prevRSI) else None, bool(rv[i]>=1.2 and b.close>b.open) if np.isfinite(rv[i]) else None, event['structure']==1,event['sweepL'],event['fvgL'],event['sdL'],rejL,bool(session[i]),bool(ht.loc[i,'last']>ht.loc[i,'ema']) if hknown else None,None]
        S=[bool(b.close<ema50[i] and ema21[i]<ema50[i]) if i>=49 else None, bool(rsi[i]<50 and rsi[i]<prevRSI) if np.isfinite(prevRSI) else None, bool(rv[i]>=1.2 and b.close<b.open) if np.isfinite(rv[i]) else None, event['structure']==-1,event['sweepS'],event['fvgS'],event['sdS'],rejS,bool(session[i]),bool(ht.loc[i,'last']<ht.loc[i,'ema']) if hknown else None,None]
        sl=sum(bool(x) for x in L); ss=sum(bool(x) for x in S)
        rl=any(event[x] for x in ['bosL','sweepL','fvgL','sdL']); rs=any(event[x] for x in ['bosS','sweepS','fvgS','sdS'])
        ok=not event['bad'] and event['contiguous']>=50 and all(x is not None for x in L[:-1]) and hknown and i>=49 and np.isfinite(rv[i]) and np.isfinite(er[i])
        block=(0 if ok else 1)+(4 if er[i]<.25 else 0)+(32 if rl and rs else 0)
        bl=block+(2 if sl<6 else 0); bs=block+(2 if ss<6 else 0)
        out.append(dict(time=b.time.isoformat(),raw_mask=int(rl)+2*int(rs),approved_mask=int(rl and bl==0)+2*int(rs and bs==0),score_L=sl,score_S=ss,known=sum(x is not None for x in L),mask_L=sum(2**j for j,x in enumerate(L) if x),mask_S=sum(2**j for j,x in enumerate(S) if x),block_L=bl,block_S=bs,rvol=rv[i],er=er[i],**event))
    return pd.DataFrame(out)

def main():
    p=argparse.ArgumentParser(); p.add_argument('--csv',default=str(Path(__file__).parent/'data/mnq_excerpt_10000.csv')); p.add_argument('--out',default=str(Path(__file__).parent/'results')); p.add_argument('--audit-only',action='store_true'); args=p.parse_args()
    out=Path(args.out); out.mkdir(parents=True,exist_ok=True); df=load_prices(args.csv)
    (out/'data_audit.json').write_text(json.dumps(audit(df,args.csv),indent=2))
    if args.audit_only: return
    result=replay(df); result.to_csv(out/'diagnostic_bars.csv',index=False)
    events=result[result.raw_mask>0]; events.to_csv(out/'diagnostic_events.csv',index=False)
    summary=dict(scope='diagnostic reference, NOT native Pine parity or performance',bars=len(result),raw_event_bars=len(events),raw_long=int((result.raw_mask%2==1).sum()),raw_short=int((result.raw_mask>=2).sum()),approved_event_bars=int((result.approved_mask>0).sum()),both_directions_blocked=int((result.raw_mask==3).sum()),max_live_zones=int(result.zones.max()),f11='unknown on every bar',parameters='single frozen default; no search')
    (out/'replay_summary.json').write_text(json.dumps(summary,indent=2)); print(json.dumps(summary))

if __name__=='__main__': main()
