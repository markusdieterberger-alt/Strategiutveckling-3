"""Deterministic input audit and calendar-roll construction. No economic outcomes."""
from pathlib import Path
import argparse,hashlib,json,re
import numpy as np
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar,GoodFriday
ROOT=Path(__file__).resolve().parents[1]

def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def trade_dates(t):
 n=t.dt.tz_convert('America/New_York').dt.tz_localize(None)
 return (n+pd.Timedelta(hours=6)).dt.strftime('%Y-%m-%d')
def holidays():
 d=set(USFederalHolidayCalendar().holidays('2019-01-01','2026-12-31').strftime('%Y-%m-%d'))
 d.update(GoodFriday.dates('2019-01-01','2026-12-31').strftime('%Y-%m-%d'))
 for y in range(2019,2027):
  th=pd.date_range(f'{y}-11-01',f'{y}-11-30',freq='W-THU')[3]
  d.update([(th+pd.Timedelta(days=1)).strftime('%Y-%m-%d'),f'{y}-07-03',f'{y}-12-24'])
 d.add('2025-01-09')
 return pd.DataFrame({'trade_date':sorted(d),'policy':'entire-session execution blackout, not exact CME hours'})
def audit(d):
 prices=d[['open','high','low','close']]
 return dict(rows=len(d),first_bar_utc=d.time.min().isoformat(),last_bar_utc=d.time.max().isoformat(),calendar_days_inclusive=(d.time.max().date()-d.time.min().date()).days+1,observed_utc_dates=d.time.dt.date.nunique(),observed_trade_dates=trade_dates(d.time).nunique(),duplicate_timestamps=int(d.time.duplicated().sum()),monotonic=bool(d.time.is_monotonic_increasing),missing_cells=int(d.isna().sum().sum()),ohlc_errors=int(((d.high<d[['open','close']].max(axis=1))|(d.low>d[['open','close']].min(axis=1))|(d.high<d.low)).sum()),tick_errors=int((abs(prices/.25-np.round(prices/.25))>1e-7).sum().sum()),negative_volume=int((d.volume<0).sum()),zero_volume=int((d.volume==0).sum()),gaps_gt_1m=int((d.time.diff().dt.total_seconds()>60).sum()))
def roll_table():
 rows=[];prior='2019-01-01'
 for y in range(2019,2027):
  for month,code in [(3,'H'),(6,'M'),(9,'U'),(12,'Z')]:
   friday=pd.date_range(f'{y}-{month:02d}-01',periods=31,freq='D');expiry=friday[friday.weekday==4][2]
   roll=(expiry-pd.Timedelta(days=8)).strftime('%Y-%m-%d')
   rows.append(dict(symbol=f'MNQ{code}{y%10}',from_trade_date=prior,to_trade_date_exclusive=roll,calendar_expiry=expiry.strftime('%Y-%m-%d')));prior=roll
 return pd.DataFrame(rows)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--master',required=True);ap.add_argument('--legacy',required=True);a=ap.parse_args()
 (ROOT/'data').mkdir(exist_ok=True);(ROOT/'results').mkdir(exist_ok=True)
 assert digest(a.master)=='45db4ed9f6cea058828e1bec57dc2f88b384bfaa5f87b42c780510dde3f5dc91'
 assert digest(a.legacy)=='3b5e1a64723ad5dbb0753922d9b925075eef07fa6a4a032d9b11a4cddc45f140'
 d=pd.read_csv(a.master);d['time']=pd.to_datetime(d.time,utc=True)
 ma=audit(d);ma['source_sha256']=digest(a.master);ma['contract_provenance']='not supplied'
 assert ma['duplicate_timestamps']==ma['missing_cells']==ma['ohlc_errors']==ma['tick_errors']==ma['negative_volume']==0 and ma['monotonic']
 d.to_csv(ROOT/'data/master.csv.gz',index=False,compression={'method':'gzip','mtime':0});(ROOT/'results/master_audit.json').write_text(json.dumps(ma,indent=2))
 holidays().to_csv(ROOT/'data/holiday_blackout.csv',index=False)
 roll=roll_table();roll.to_csv(ROOT/'data/roll_calendar.csv',index=False)
 days=pd.date_range('2019-01-01','2026-12-31');mapping={}
 for row in roll.itertuples():
  for day in days[(days>=row.from_trade_date)&(days<row.to_trade_date_exclusive)]:mapping[day.strftime('%Y-%m-%d')]=row.symbol
 parts=[];raw=outrights=0
 for c in pd.read_csv(a.legacy,chunksize=250000):
  raw+=len(c);c=c[c.symbol.str.fullmatch(r'MNQ[HMUZ][0-9]')].copy();outrights+=len(c)
  c['time']=pd.to_datetime(c.ts_event,utc=True);c['trade_date']=trade_dates(c.time)
  c=c[(c.symbol==c.trade_date.map(mapping))&(c.time<pd.Timestamp('2025-10-01',tz='UTC'))]
  parts.append(c[['time','open','high','low','close','volume','symbol','instrument_id']])
  print('legacy source rows',raw,'selected so far',sum(len(x) for x in parts),flush=True)
 legacy=pd.concat(parts,ignore_index=True).sort_values('time').reset_index(drop=True)
 la=audit(legacy);la.update(source_rows=raw,outright_rows=outrights,source_sha256=digest(a.legacy),contracts=legacy.symbol.nunique(),roll_changes=int((legacy.symbol!=legacy.symbol.shift()).sum()-1),selection='fixed calendar, no adjustment, no fill-forward, no overlap with master')
 assert la['duplicate_timestamps']==la['missing_cells']==la['ohlc_errors']==la['tick_errors']==la['negative_volume']==0 and la['monotonic']
 legacy.to_csv(ROOT/'data/legacy_calendar_roll.csv.gz',index=False,compression={'method':'gzip','mtime':0})
 legacy.groupby('symbol',sort=False).agg(start=('time','min'),end=('time','max'),bars=('time','size')).to_csv(ROOT/'results/legacy_segments.csv')
 gaps=legacy[['time','symbol']].copy();gaps['gap_minutes']=legacy.time.diff().dt.total_seconds()/60;gaps[gaps.gap_minutes>1].to_csv(ROOT/'results/legacy_gaps.csv.gz',index=False,compression={'method':'gzip','mtime':0})
 (ROOT/'results/legacy_audit.json').write_text(json.dumps(la,indent=2));print(json.dumps({'master':ma,'legacy':la},indent=2))
if __name__=='__main__':main()
