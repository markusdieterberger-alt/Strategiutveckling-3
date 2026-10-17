"""Preregistered economic summaries, clustered uncertainty and concentration checks."""
from pathlib import Path
import json,math
import numpy as np
import pandas as pd
from execution import summary,simulate,SCENARIOS
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/analysis'

def boot_weights(n):
 rng=np.random.default_rng(20261017);starts=rng.integers(0,n,size=(5000,math.ceil(n/5)))
 idx=((starts[:,:,None]+np.arange(5))%n).reshape(5000,-1)[:,:n]
 return np.array([np.bincount(row,minlength=n) for row in idx],dtype=np.int16)
def q(x,lo=.025,hi=.975):
 x=x[np.isfinite(x)];return [float(np.quantile(x,lo)),float(np.quantile(x,hi))] if len(x) else [None,None]
def clean(v):
 if isinstance(v,dict):return {k:clean(x) for k,x in v.items()}
 if isinstance(v,list):return [clean(x) for x in v]
 if isinstance(v,np.generic):return v.item()
 if isinstance(v,float) and not np.isfinite(v):return None
 return v

def main():
 OUT.mkdir(exist_ok=True);matrix=pd.concat([pd.read_csv(ROOT/f'results/economic_{d}/summary.csv') for d in ['master','legacy']],ignore_index=True)
 matrix.to_csv(ROOT/'BUCKO_RECON_04_Test_Matrix.csv',index=False)
 ledgers=[];candidate_counts=[];monthly=[];split=[];halves=[];tops=[];boots=[];yearly=[];risk=[];weights={};daily_dates={};trade_map={};daily_base=[];weekly=[];costs=[]
 for row in matrix.itertuples():
  folder=ROOT/f'results/economic_{row.dataset}'
  t=pd.read_csv(folder/(row.variant+'_trades.csv.gz'));c=pd.read_csv(folder/(row.variant+'_candidates.csv.gz'));d=pd.read_csv(folder/(row.variant+'_daily.csv'))
  ledgers.append(t);trade_map[row.variant]=t
  gp=t.gross_before_costs_usd;costs.append(dict(variant=row.variant,gross_same_book_net_usd=float(gp.sum()),gross_same_book_pf=float(gp[gp>0].sum()/-gp[gp<0].sum()),gross_same_book_winrate=float((gp>0).mean()),net_usd=float(t.net_usd.sum()),friction_usd=float((gp-t.net_usd).sum())))
  for week,g in t.groupby(pd.to_datetime(t.trade_date).dt.to_period("W-SUN").astype(str)):weekly.append(dict(variant=row.variant,week=week,**summary(g)))
  for reason,g in c.groupby('disposition'):candidate_counts.append(dict(variant=row.variant,reason=reason,count=len(g)))
  if row.dataset not in daily_dates:daily_dates[row.dataset]=sorted(d.trade_date.unique());weights[row.dataset]=boot_weights(len(daily_dates[row.dataset]))
  x=pd.DataFrame({'trade_date':t.trade_date,'profit':t.net_usd.clip(lower=0),'loss':(-t.net_usd).clip(lower=0),'net':t.net_usd,'n':1,'r':t.net_R}).groupby('trade_date').sum().reindex(daily_dates[row.dataset],fill_value=0)
  bx=weights[row.dataset]@x[['profit','loss','net','n','r']].to_numpy()
  with np.errstate(divide='ignore',invalid='ignore'):
   ep=bx[:,2]/bx[:,3];er=bx[:,4]/bx[:,3];pf=bx[:,0]/bx[:,1]
  boots.append(dict(variant=row.variant,days=len(x),draws=5000,block_days=5,net_usd_ci95_low=q(bx[:,2])[0],net_usd_ci95_high=q(bx[:,2])[1],expectancy_ci95_low=q(ep)[0],expectancy_ci95_high=q(ep)[1],expectancy_R_ci95_low=q(er)[0],expectancy_R_ci95_high=q(er)[1],pf_ci95_low=q(pf)[0],pf_ci95_high=q(pf)[1],expectancy_family98_333_low=q(ep,.05/6,1-.05/6)[0],expectancy_family98_333_high=q(ep,.05/6,1-.05/6)[1],bootstrap_positive_fraction=float((bx[:,2]>0).mean())))
  for month,g in t.groupby(t.trade_date.str[:7]):monthly.append(dict(variant=row.variant,dataset=row.dataset,signal_model=row.signal_model,rr=row.rr,month=month,**summary(g)))
  for year,g in t.groupby(t.trade_date.str[:4]):yearly.append(dict(variant=row.variant,dataset=row.dataset,signal_model=row.signal_model,rr=row.rr,year=year,**summary(g)))
  for field in ['direction','score','signal_type','ema_regime','chop_regime','score_session']:
   for group,g in t.groupby(field):split.append(dict(variant=row.variant,dataset=row.dataset,signal_model=row.signal_model,rr=row.rr,field=field,group=str(group),small_sample=len(g)<30,**summary(g)))
  midpoint=pd.Timestamp('2026-04-01',tz='UTC') if row.dataset=='master' else pd.Timestamp(row.start_utc)+(pd.Timestamp(row.end_bar_utc)-pd.Timestamp(row.start_utc))/2
  et=pd.to_datetime(t.entry_time,utc=True)
  for part,sel in [('first',et<midpoint),('second',et>=midpoint)]:
   g=t[sel];halves.append(dict(variant=row.variant,dataset=row.dataset,signal_model=row.signal_model,rr=row.rr,half=part,boundary_utc=midpoint.isoformat(),first_entry=g.entry_time.min(),last_exit=g.exit_time.max(),**summary(g)))
  winners=t[t.net_usd>0].sort_values('net_usd',ascending=False)
  for name,k in [('top1',1),('top5',5),('top10',10),('top5pct_winners',int(math.ceil(len(winners)*.05)))]:
   removed=winners.head(k);remain=t.drop(removed.index);tops.append(dict(variant=row.variant,dataset=row.dataset,signal_model=row.signal_model,rr=row.rr,remove=name,removed_trades=len(removed),removed_profit_usd=float(removed.net_usd.sum()),remaining_net_usd=float(remain.net_usd.sum()),remaining_expectancy_usd=float(remain.net_usd.mean()),share_of_positive_profit=float(removed.net_usd.sum()/winners.net_usd.sum()) if len(winners) else None))
  daily=t.groupby('trade_date').net_usd.sum();risk.append(dict(variant=row.variant,risk_median=float(t.risk_usd.median()),risk_p95=float(t.risk_usd.quantile(.95)),risk_max=float(t.risk_usd.max()),initial_risk_over600=int((t.risk_usd>600).sum()),days_net_below_minus600=int((daily<-600).sum()),worst_closed_day=float(daily.min()),best_closed_day=float(daily.max())))
  dx=x.reset_index();dx['variant']=row.variant;daily_base.append(dx)
 alltr=pd.concat(ledgers,ignore_index=True);assert alltr.trade_id.is_unique
 alltr.to_csv(ROOT/'BUCKO_RECON_04_Trade_Ledger.csv',index=False)
 for name,data in [('bootstrap',boots),('monthly',monthly),('yearly',yearly),('breakdowns',split),('halves',halves),('winner_concentration',tops),('candidate_dispositions',candidate_counts),('risk_diagnostics',risk),('weekly',weekly),('before_after_costs',costs)]:pd.DataFrame(data).to_csv(OUT/(name+'.csv'),index=False)
 pd.concat(daily_base).to_csv(OUT/'daily_trade_sums.csv',index=False)
 sigmonths=pd.concat([pd.read_csv(ROOT/f'results/economic_{d}/signals_monthly.csv') for d in ['master','legacy']],ignore_index=True);sigmonths.to_csv(OUT/'signals_monthly.csv',index=False)
 # Pair same-source native-semantics approximations against the frozen reference.
 parity=[]
 for rr in [1.5,2.,3.]:
  a=trade_map[f'master__PRIMARY_ORIGINAL__BASE1__R{rr:g}'];b=trade_map[f'master__PINE_SEMANTICS_04_1__BASE1__R{rr:g}']
  m=a.merge(b,on=['signal_time','direction'],how='outer',suffixes=('_original','_approx'),indicator=True)
  cols=['entry_time','exit_time','stop','target','net_usd'];common=m[m._merge=='both'];same=np.ones(len(common),bool)
  for col in cols:same&=(common[col+'_original']==common[col+'_approx']).to_numpy()
  parity.append(dict(rr=rr,common_signal_keys=len(common),identical_trades=int(same.sum()),only_original=int((m._merge=='left_only').sum()),only_approx=int((m._merge=='right_only').sum()),net_difference_usd=float(b.net_usd.sum()-a.net_usd.sum())))
 pd.DataFrame(parity).to_csv(OUT/'pine_semantics_trade_comparison.csv',index=False)
 # Exposed RECON03 excerpt: frequency only, not a fourth economic validation period.
 e=pd.read_csv(ROOT/'results/signals/excerpt_excerpt.csv.gz');e['time']=pd.to_datetime(e.time,utc=True);black=set(pd.read_csv(ROOT/'data/holiday_blackout.csv').trade_date)
 ex=[]
 for rr in [1.5,2.,3.]:
  tr,ca,_,_=simulate(e,rr,SCENARIOS['BASE1'],black,'excerpt_exposed')
  ex.append(dict(rr=rr,raw_bars=int((e.raw_mask>0).sum()),approved_bars=int((e.approved_mask>0).sum()),entry_candidates=int(ca.entry_candidate.sum()),position_blocked=int((ca.disposition=='POSITION_OPEN').sum()),trades=len(tr),dispositions=ca.disposition.value_counts().to_dict()))
 sig=e[e.approved_mask>0];from prepare_data import trade_dates
 sd=trade_dates(sig.time);episodes=int(((sig.approved_mask!=sig.approved_mask.shift())|(sig.time.diff()>pd.Timedelta(minutes=15))|(sd!=sd.shift())).sum())
 (OUT/'excerpt_frequency.json').write_text(json.dumps({'start':e.time.min().isoformat(),'end':e.time.max().isoformat(),'approved_episode_groups_15min':episodes,'variants':ex},indent=2))
 # Ledger economic identities and chronological non-overlap, for every variant.
 checks=[]
 for variant,g in alltr.groupby('variant',sort=False):
  g=g.sort_values('entry_time');eq=(g.effective_exit_price-g.entry_fill)*g.direction*2-g.commission_usd
  nonoverlap=(pd.to_datetime(g.entry_time.iloc[1:].reset_index(drop=True),utc=True)>=pd.to_datetime(g.exit_time.iloc[:-1].reset_index(drop=True),utc=True)).all()
  checks.append(dict(variant=variant,trades=len(g),unique_ids=bool(g.trade_id.is_unique),nonoverlap=bool(nonoverlap),pnl_max_error=float(np.max(np.abs(eq-g.net_usd))),grid_error_count=int((np.abs(g[['entry_fill','stop','target']]/.25-np.round(g[['entry_fill','stop','target']]/.25))>1e-8).sum().sum())))
 assert all(x['unique_ids'] and x['nonoverlap'] and x['pnl_max_error']<1e-7 and x['grid_error_count']==0 for x in checks)
 (OUT/'ledger_qa.json').write_text(json.dumps(checks,indent=2))
 main=matrix[(matrix.dataset=='master')&(matrix.signal_model=='PRIMARY_ORIGINAL')&(matrix.scenario=='BASE1')]
 print(main[['rr','trades','winrate','pf','net_usd','expectancy_usd','expectancy_R','max_closed_dd_usd','max_barclose_mtm_dd_usd']].to_string(index=False))
 print('Ledger rows',len(alltr),'matrix rows',len(matrix))
 (OUT/'analysis_summary.json').write_text(json.dumps(clean({'primary':main.to_dict('records'),'bootstrap':boots,'pine_semantics_comparison':parity,'total_ledger_rows':len(alltr),'matrix_rows':len(matrix),'ledger_qa_all_passed':True}),ensure_ascii=False,indent=2,allow_nan=False))
if __name__=='__main__':main()
