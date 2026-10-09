
# DAE research engine v0.2 - current-bar volume profile ingestion fix; preliminary parity only.
# Reference: DAE-20 frozen Pine; do not use as full TV equivalence proof.
import pandas as pd, numpy as np, math
p='/mnt/data/MNQ_1m_MASTER_2025-10-01_to_2026-10-01 (1)(1).csv'
d=pd.read_csv(p,parse_dates=['time'])
d['time']=pd.to_datetime(d.time,utc=True)
d=d[(d.time>='2026-09-14')&(d.time<'2026-09-29')].reset_index(drop=True)
d['bucket']=d.time.dt.floor('30min')
htf=d.groupby('bucket',sort=True).agg(open=('open','first'),high=('high','max'),low=('low','min'),close=('close','last'))
keys=list(htf.index); htf=htf.reset_index()
signal={}
for j in range(3,len(htf)):
    a=htf.iloc[j-1]; b=htf.iloc[j-2]; old=htf.iloc[j-3]
    bull=a.low<b.low and b.low<=a.close<=b.high
    bear=a.high>b.high and b.low<=a.close<=b.high
    gapBull=a.low>old.high
    gapBear=a.high<old.low
    if (bull or bear) and (gapBull or gapBear):
        direction=1 if bull and not bear else -1 if bear and not bull else 0
        signal[htf.iloc[j]['bucket']]=(direction, bool(gapBull),float(a.high),float(a.low),
            float(a.low if gapBull else old.low),float(old.high if gapBull else a.high),float(a.close),
            htf.iloc[j-1]['bucket'])
def tick(x): return np.floor(x*4+0.5)/4
def vp(profile):
    hh=np.array([x[1] for x in profile]); ll=np.array([x[2] for x in profile]); vv=np.array([x[3] for x in profile])
    lo=ll.min(); hi=hh.max(); span=hi-lo
    if span<=0:return None
    step=span/60; hist=np.zeros(60)
    for h,l,v in zip(hh,ll,vv):
        first=max(0,min(59,int(math.floor((l-lo)/step))))
        last=max(0,min(59,int(math.floor((h-lo)/step))))
        if h>l:
            for k in range(first,last+1):
                overlap=max(0,min(h,lo+(k+1)*step)-max(l,lo+k*step))
                if overlap:hist[k]+=v*overlap/(h-l)
        else:hist[first]+=v
    poc=int(hist.argmax()); left=right=poc; accum=hist[poc]; total=hist.sum()
    while accum<total*.70:
        lv=hist[left-1] if left>0 else -1
        rv=hist[right+1] if right<59 else -1
        if rv>lv and right<59: right+=1;accum+=hist[right]
        elif left>0:left-=1;accum+=hist[left]
        elif right<59:right+=1;accum+=hist[right]
        else:break
    return lo+left*step,lo+(right+1)*step
active=False; profile=[]; pending=None; position=None; trades=[]; logs=[]
prev_bucket=None; prev_close=None
rows=d.itertuples(index=False)
for r in rows:
    t=r.time; bucket=r.bucket
    # Historical 1m candle path, TradingView-style nearest-extreme assumption.
    # A stop/limit may fill only after the order is live; exits must occur after entry.
    path=[float(r.open),float(r.high),float(r.low),float(r.close)] if abs(r.open-r.high)<abs(r.open-r.low) else [float(r.open),float(r.low),float(r.high),float(r.close)]
    def cross(x,y,level):
        return min(x,y)<=level<=max(x,y)
    def entry_hit(x,y,order):
        e=order['entry']; side=order['side']; typ=order['type']
        if typ=='stop': return max(x,y)>=e if side==1 else min(x,y)<=e
        return min(x,y)<=e if side==1 else max(x,y)>=e
    # Process the intrabar path in sequence, including a possible same-bar exit.
    current=path[0]
    for nxt in path[1:]:
        if pending is not None and position is None and entry_hit(current,nxt,pending):
            e=pending['entry']
            fill=e
            # Gap-through order is executed at the opening price (approximation).
            if current==path[0] and ((pending['type']=='stop' and ((pending['side']==1 and current>e) or (pending['side']==-1 and current<e))) or (pending['type']=='limit' and ((pending['side']==1 and current<e) or (pending['side']==-1 and current>e)))):
                fill=current
            position=dict(pending,entry_time=t,entry=fill)
            pending=None
            current=fill
        if position is not None:
            side=position['side']; sl=position['sl'];tp=position['tp']
            sl_hit=cross(current,nxt,sl)
            tp_hit=cross(current,nxt,tp)
            if sl_hit or tp_hit:
                # When both lie on a segment, the closest to segment start hits first.
                sl_first=sl_hit and (not tp_hit or abs(sl-current)<=abs(tp-current))
                ex=sl if sl_first else tp
                trades.append(dict(entry_time=position['entry_time'],exit_time=t,side=side,entry=position['entry'],exit=ex,pnl=(ex-position['entry'])*side*2,reason='SL' if sl_first else 'TP',ambiguous=False))
                position=None
        current=nxt
    # 2. New 30m signal on bucket transition, including cancellation
    new_bucket=bucket!=prev_bucket
    if new_bucket and bucket in signal:
        if position is None: pending=None
        active=True;profile=[]
        side,gapBull,creatorHi,creatorLo,gapTop,gapBottom,creatorClose,born=signal[bucket]
        born_time=born
        activation=t
        submitted=False
        # Pine cacheT is 120 recent 1m candles; CRT candle is 30m, reconstruct it
        for row in cache[-120:]:
            if row[0]>=born_time:profile.append(row)
    # DAE-20 Pine ingests the completed current 1m candle BEFORE evaluating profile.
    if active:
        profile.append((t,r.high,r.low,r.volume))
        if len(profile)>4000:profile.pop(0)
    if active and t>activation:
        if (r.low<=gapTop if gapBull else r.high>=gapBottom):active=False
    if active and new_bucket and t>activation:
        prev30=htf[htf.bucket==bucket-pd.Timedelta(minutes=30)]
        if len(prev30):
            c=float(prev30.iloc[0]['close'])
            if (c>creatorHi if gapBull else c<creatorLo):active=False
    if active and not submitted and position is None and profile:
        va=vp(profile)
        if va is not None and side:
            val,vah=va; entry=tick(vah if side==1 else val)
            targets=[x for x in (gapTop,gapBottom) if (x>entry if side==1 else x<entry)]
            if targets:
                tp=tick(min(targets,key=lambda x:abs(x-entry)))
                if abs(tp-entry)>=.25:
                    sl=tick(entry-side*abs(tp-entry))
                    sl=tick(max(sl,entry-100) if side==1 else min(sl,entry+100))
                    typ='stop' if (entry>r.close if side==1 else entry<r.close) else 'limit'
                    pending=dict(entry=entry,tp=tp,sl=sl,side=side,type=typ,submit_time=t)
                    submitted=True
                    logs.append((t,'order',side,entry,sl,tp,typ))
    # 3. expire pending if profile no longer active
    if not active and pending is not None and position is None:pending=None
    if 'cache' not in globals():cache=[]
    cache.append((t,r.high,r.low,r.volume))
    if len(cache)>120:cache.pop(0)
    prev_bucket=bucket
res=pd.DataFrame(trades)
sel=res[(res.exit_time>='2026-09-21')&(res.exit_time<'2026-09-28')]
print('Signals',len(signal),'orders',len(logs),'all trades',len(res))
print('TEST WEEK',len(sel),'wins',sum(sel.pnl>0),'NET',round(sel.pnl.sum(),2),'DD realized',round((sel.pnl.cumsum().cummax().clip(lower=0)-sel.pnl.cumsum()).max(),2) if len(sel) else 0)
print(sel.to_string(index=False))
print('Orders in week:')
print(*[str(x) for x in logs if pd.Timestamp('2026-09-21',tz='UTC')<=x[0]<pd.Timestamp('2026-09-28',tz='UTC')],sep='\n')