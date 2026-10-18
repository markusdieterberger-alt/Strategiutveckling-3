"""R2: transport unchanged RECON04/REVERSE01 causal traces; no signal recomputation."""
from pathlib import Path
import pandas as pd,numpy as np,json,hashlib,sys
ROOT=Path(__file__).resolve().parents[1]; PRIOR=ROOT.parent/'reverse01'
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(ds):
 out=ROOT/'work'/ds;out.mkdir(parents=True,exist_ok=True)
 black=set(pd.read_csv(PRIOR/'baseline/data/holiday_blackout.csv').trade_date)
 names=['master'] if ds=='master' else pd.read_csv(PRIOR/'baseline/results/legacy_segments.csv').symbol.tolist()
 allbars=[];allseeds=[];hashes=[];offset=0;raw=0;monthly=[]
 for seg,name in enumerate(names):
  p=PRIOR/f'cache/signals/{ds}_{name}.csv.gz';d=pd.read_csv(p);t=pd.to_datetime(d.time,utc=True);ny=t.dt.tz_convert('America/New_York');cny=(t+pd.Timedelta(minutes=1)).dt.tz_convert('America/New_York')
  td=(ny.dt.tz_localize(None)+pd.to_timedelta((ny.dt.hour>=18).astype(int),unit='D')).dt.strftime('%Y-%m-%d');ctd=(cny.dt.tz_localize(None)+pd.to_timedelta((cny.dt.hour>=18).astype(int),unit='D')).dt.strftime('%Y-%m-%d')
  m=ny.dt.hour*60+ny.dt.minute;cm=cny.dt.hour*60+cny.dt.minute
  ok=(~td.isin(black)) & (pd.to_datetime(td).dt.weekday<5);cok=(~ctd.isin(black)) & (pd.to_datetime(ctd).dt.weekday<5)
  est=(t.dt.hour*60+t.dt.minute-300)%1440
  b=pd.DataFrame({'epoch':t.astype('int64')//10**9,'open':d.open,'high':d.high,'low':d.low,'close':d.close,'day':td,'segment':seg,'enter':(ok&((m<960)|(m>=1080))&((est<1005)|(est>=1080))).astype(int),'flat':((~ok)|((m>=990)&(m<1080))).astype(int),'minute':m})
  ii=np.flatnonzero(d.approved_mask.to_numpy()>0);s=d.iloc[ii].copy();s.insert(0,'signal_bar',ii+offset);s['source_direction']=np.where(s.approved_mask==1,1,-1);s['signal_allowed']=(cok&((cm<960)|(cm>=1080))).iloc[ii].to_numpy().astype(int);s['signal_day']=ctd.iloc[ii].to_numpy();s['close_day']=td.iloc[ii].to_numpy();allseeds.append(s);allbars.append(b)
  raw+=int((d.raw_mask>0).sum());monthly.append(pd.DataFrame({'month':td.str[:7],'raw':(d.raw_mask>0).astype(int),'approved':(d.approved_mask>0).astype(int),'source_long':(d.approved_mask==1).astype(int),'source_short':(d.approved_mask==2).astype(int)}).groupby('month').sum())
  hashes.append({'path':str(p.relative_to(PRIOR)),'sha256':sha(p),'bars':len(d)});offset+=len(d)
 b=pd.concat(allbars,ignore_index=True);s=pd.concat(allseeds,ignore_index=True);s.insert(0,'seed_id',np.arange(len(s)))
 days=sorted(b.day.unique());di={d:i for i,d in enumerate(days)};b.day=b.day.map(di);s['day_id']=s.signal_day.map(di)
 b.to_numpy(dtype='<f8').tofile(out/'bars.bin')
 seedcols=['signal_bar','source_direction','swing_low_close','swing_high_close','close','signal_allowed','day_id']
 s[seedcols].to_numpy(dtype='<f8').tofile(out/'seeds.bin');s.to_csv(out/'seeds.csv.gz',index=False)
 daydf=pd.DataFrame({'day_id':range(len(days)),'date':days});daydf['ordinal']=(pd.to_datetime(daydf.date)-pd.Timestamp('1970-01-01')).dt.days;daydf['complete_start']=1;daydf.loc[[0,len(days)-1],'complete_start']=0
 daydf.to_csv(out/'days.csv',index=False);daydf[['ordinal','complete_start']].to_numpy(dtype='<i4').tofile(out/'days.bin')
 pd.concat(monthly).groupby(level=0).sum().to_csv(out/'signals_monthly.csv')
 meta={'dataset':ds,'bars':len(b),'approved':len(s),'raw_events':raw,'first_utc':pd.to_datetime(b.epoch.iloc[0],unit='s',utc=True).isoformat(),'last_utc':pd.to_datetime(b.epoch.iloc[-1],unit='s',utc=True).isoformat(),'sessions':len(days),'complete_start_sessions':len(days)-2,'trace_hashes':hashes,'bar_columns':b.columns.tolist(),'seed_columns':seedcols,'version':'R2_RECOVERED_PROTOCOL'}
 (out/'metadata.json').write_text(json.dumps(meta,indent=2));print(ds,len(b),len(s),len(days),flush=True)
 # Chronological paths then 4096 circular five-session blocks, same paths for all models.
 rng=np.random.default_rng(20261018 if ds=='master' else 20261019);paths=[];pm=[]
 for start in range(1,len(days)-1):
  row=np.full(120,-1,dtype='int32');n=min(120,len(days)-start);row[:n]=np.arange(start,start+n);paths.append(row);pm.append((len(pm),0,start,n))
 for k in range(4096):
  row=np.concatenate([1+(rng.integers(0,len(days)-2)+np.arange(5))%(len(days)-2) for _ in range(24)]).astype('int32');paths.append(row);pm.append((len(pm),1,int(row[0]),120))
 np.array(paths,dtype='<i4').tofile(out/'paths.bin');pd.DataFrame(pm,columns=['path_id','bootstrap','source_start_day','observed_sessions']).to_csv(out/'paths.csv',index=False)
 np.save(out/'paths.npy',np.array(paths,dtype='int32'))
if __name__=='__main__':main(sys.argv[1])
