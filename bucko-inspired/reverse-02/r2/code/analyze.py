"""Reporting-only reconstruction, 19 Oct 2026. Does not alter R2 model outputs.
Rebuilds the released account matrix and auditable single-contract diagnostics.
"""
from pathlib import Path
import sys,json,math
import numpy as np,pandas as pd
R=Path(__file__).resolve().parents[1]; OUT=R/'results'; OUT.mkdir(exist_ok=True)
RR=[1,.75,.5,.33,.2,.1]; RISKS=[100,200,300,400,500,575]; SC=['BASE1','SLIP2','DELAY60','DELAY60_SLIP2']
def config(c):
 p=c%3;c//=3;ri=c%6;c//=6;sc=c%4;c//=4;r=c%6;f=c//6
 return dict(family=['S','M'][f],rr=RR[r],scenario=SC[sc],risk_usd=RISKS[ri],funded_risk_usd=min(200,RISKS[ri]),policy=['P0','P300','P600'][p])
def wilson(k,n):
 z=1.959963984540054;p=k/n; d=1+z*z/n;mid=(p+z*z/(2*n))/d;half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
 return mid-half,mid+half
def account_stat(g):
 n=len(g); passed=g[g.passed==1]; paid=g[g.payout==1];fail=g[g.status.isin([1,2,4,5])]
 pc=wilson(g.passed.sum(),n);qc=wilson(g.payout.sum(),n)
 d=dict(accounts=n,passrate=g.passed.mean(),payout_rate=g.payout.mean(),challenge_failrate=(g.eval_mll+g.eval_inactive).mean(),funded_failure_per_start=(g.funded_mll+g.funded_inactive).mean(),pass_ci_low=pc[0],pass_ci_high=pc[1],payout_ci_low=qc[0],payout_ci_high=qc[1],median_sessions_to_pass=passed.pass_sessions.median(),median_active_days_to_pass=passed.active_eval_days.median(),median_calendar_days_to_pass=passed.pass_calendar_days.median(),median_sessions_to_fail=fail.total_sessions.median(),median_sessions_to_payout_request=paid.total_sessions.median(),median_calendar_days_to_payout_request=paid.total_calendar_days.median(),mean_eval_trades=g.eval_trades.mean(),mean_total_trades=(g.eval_trades+g.funded_trades).mean(),max_drawdown=g.max_drawdown.max(),dll_challenge_rate=(g.eval_dll_days>0).mean(),dll_funded_per_start=(g.funded_dll_days>0).mean(),mll_challenge_rate=g.eval_mll.mean(),mll_funded_per_start=g.funded_mll.mean(),inactivity_challenge_rate=g.eval_inactive.mean(),inactivity_funded_per_start=g.funded_inactive.mean(),eval_timeout_rate=g.eval_timeout.mean(),funded_timeout_rate=g.funded_timeout.mean(),censored_rate=g.censored.mean(),data_unknown_rate=g.data_unresolved.mean(),expected_cash_per_start=g.cash.mean(),mean_cash_if_paid=paid.cash.mean(),ev_fee50=g.cash.mean()-50,break_even_fee=g.cash.mean())
 for k in [5,10,15]:
  eligible=~((g.censored.eq(1)|g.data_unresolved.eq(1))&g.total_sessions.lt(k)&g.passed.eq(0))
  d[f'pass_within_{k}_denominator']=int(eligible.sum());d[f'pass_within_{k}']=((g.passed.eq(1)&g.pass_sessions.le(k))&eligible).sum()/eligible.sum() if eligible.any() else np.nan
 return d
def accounts(ds):
 w=R/'work'/ds;days=pd.read_csv(w/'days.csv');n=len(days)-2; rows=[];conv=[];months=[]
 for sc in range(4):
  a=pd.read_csv(w/f'accounts_sc{sc}.csv.gz')
  for cid,g in a.groupby('config_id',sort=False):
   base=dict(dataset=ds,config_id=int(cid),**config(int(cid)))
   ch=g[g.bootstrap==0]; mc=g[g.bootstrap==1]
   cohorts={'BOOTSTRAP5':mc,'CHRONO_ALL':ch,'CHRONO_FIRST_HALF':ch[ch.path_id<n//2],'CHRONO_SECOND_HALF':ch[ch.path_id>=n//2],'CHRONO_FULL120':ch[ch.path_id<=len(days)-122]}
   for label,z in cohorts.items():rows.append(dict(**base,cohort=label,**account_stat(z)))
   for k in [1024,2048,4096]:
    z=mc.iloc[:k]; conv.append(dict(**base,draws=k,passrate=z.passed.mean(),payout_rate=z.payout.mean(),expected_cash_per_start=z.cash.mean()))
   ch=ch.copy();ch['start_month']=days.date.str[:7].to_numpy()[ch.path_id.to_numpy()+1]
   for mon,z in ch.groupby('start_month'):months.append(dict(**base,start_month=mon,**account_stat(z)))
  print(ds,'accounts scenario',sc,flush=True)
 result=pd.DataFrame(rows);result.to_csv(OUT/f'{ds}_challenge_recomputed.csv',index=False)
 pd.DataFrame(conv).to_csv(OUT/f'{ds}_convergence.csv',index=False);pd.DataFrame(months).to_csv(OUT/f'{ds}_chronological_start_month.csv',index=False)
 return result
def metric(g):
 x=g.net_one_mnq.to_numpy();gross=g.gross_one_mnq.to_numpy();risk=g.planned_loss_one_mnq.to_numpy();r=x/risk;eq=np.r_[0,np.cumsum(x)];er=np.r_[0,np.cumsum(r)]
 streak=best=0
 for v in x:streak=streak+1 if v<0 else 0;best=max(best,streak)
 wins=x[x>0];loss=x[x<0]
 return dict(trades=len(x),wins=int((x>0).sum()),losses=int((x<0).sum()),winrate=float((x>0).mean()) if len(x) else np.nan,profit_factor=wins.sum()/-loss.sum() if len(loss) else np.nan,net_usd=x.sum(),gross_usd=gross.sum(),costs_usd=(gross-x).sum(),expectancy_usd=x.mean() if len(x) else np.nan,expectancy_r=r.mean() if len(x) else np.nan,max_closed_drawdown_usd=(np.maximum.accumulate(eq)-eq).max(),max_closed_drawdown_r=(np.maximum.accumulate(er)-er).max(),mean_win_usd=wins.mean() if len(wins) else np.nan,mean_loss_usd=loss.mean() if len(loss) else np.nan,mean_win_r=r[x>0].mean() if len(wins) else np.nan,mean_loss_r=r[x<0].mean() if len(loss) else np.nan,longest_loss_streak=best,data_unresolved=int((g.data_unresolved>0).sum()))
def independent(z):
 chosen=[];busy=-1
 for k,r in z.iterrows():
  if r.signal_bar<busy:continue
  chosen.append(k);busy=r.exit_bar
 return z.loc[chosen].copy()
def books(ds):
 w=R/'work'/ds;o=pd.read_csv(w/'candidate_outcomes.csv.gz');seeds=pd.read_csv(w/'seeds.csv.gz');days=pd.read_csv(w/'days.csv');rows=[];groups=[];ledgers=[];robust=[]
 rng=np.random.default_rng(20261018 if ds=='master' else 20261019);nd=len(days);idx=np.concatenate([(rng.integers(0,nd,size=(4096,1))+np.arange(5))%nd for _ in range(math.ceil(nd/5))],axis=1)[:,:nd]
 for (f,ri,sc),z in o.groupby(['family','rr_id','scenario_id'],sort=False):
  z=independent(z);base=dict(dataset=ds,family=['S','M','ORIGINAL'][f],rr=RR[ri],scenario=SC[sc]);z['month']=days.date.str[:7].to_numpy()[z.day_id.to_numpy()];s=seeds.iloc[z.seed_id.to_numpy()]
  z['source_score']=np.where(s.source_direction.to_numpy()==1,s.score_L,s.score_S);z['source_type']=s.signal_model.to_numpy();z['source_regime']=s.ema_regime.to_numpy();z['half']=np.where(z.day_id<nd//2,'FIRST','SECOND')
  rows.append(dict(**base,**metric(z)));z['dataset']=ds;ledgers.append(z)
  for key in ['month','direction','source_score','source_type','source_regime','half']:
   for value,g in z.groupby(key,dropna=False):groups.append(dict(**base,split=key,value=value,**metric(g)))
  daily=z.groupby('day_id').net_one_mnq.sum().reindex(range(nd),fill_value=0).to_numpy();draw=daily[idx].sum(axis=1);tops=np.sort(z.net_one_mnq.to_numpy())[::-1]
  robust.append(dict(**base,net_without_top1=z.net_one_mnq.sum()-tops[:1].sum(),net_without_top5=z.net_one_mnq.sum()-tops[:5].sum(),net_without_top10=z.net_one_mnq.sum()-tops[:10].sum(),block_net_p025=np.quantile(draw,.025),block_net_median=np.median(draw),block_net_p975=np.quantile(draw,.975),fraction_bootstrap_net_positive=(draw>0).mean(),bootstrap_draws=4096,block_sessions=5))
 pd.DataFrame(rows).to_csv(OUT/f'{ds}_single_contract_summary.csv',index=False);pd.DataFrame(groups).to_csv(OUT/f'{ds}_single_contract_groups.csv',index=False);pd.DataFrame(robust).to_csv(OUT/f'{ds}_single_contract_robustness.csv',index=False);pd.concat(ledgers).to_csv(OUT/f'{ds}_single_contract_trades.csv.gz',index=False)
 orig=independent(o[(o.family==2)&(o.scenario_id==0)]);mirror=o[(o.family==1)&(o.rr_id==0)&(o.scenario_id==0)].set_index('seed_id').loc[orig.seed_id].reset_index();orig=orig.reset_index(drop=True)
 pair=pd.DataFrame({'seed_id':orig.seed_id,'original_outcome_id':orig.outcome_id,'fixed_mirror_outcome_id':mirror.outcome_id,'original_net':orig.net_one_mnq,'forced_inverse_net':-orig.gross_one_mnq-2,'fixed_bracket_net':mirror.net_one_mnq,'gross_complementary':np.isclose(orig.gross_one_mnq+mirror.gross_one_mnq,0),'same_exit_bar':orig.exit_bar==mirror.exit_bar,'same_exit_epoch':orig.exit_epoch==mirror.exit_epoch,'either_both_touch':(orig.both_touch>0)|(mirror.both_touch>0),'either_gap':orig.exit_reason.isin([1,2,5])|mirror.exit_reason.isin([1,2,5]),'both_net_negative':(orig.net_one_mnq<0)&(mirror.net_one_mnq<0)})
 pair.to_csv(OUT/f'{ds}_exact_mirror_pairs.csv.gz',index=False)
 summary=dict(dataset=ds,opportunities=len(pair),gross_complementary=int(pair.gross_complementary.sum()),same_exit_bar=int(pair.same_exit_bar.sum()),strict_complementary=int((pair.same_exit_epoch&pair.gross_complementary).sum()),both_touch=int(pair.either_both_touch.sum()),gap_any=int(pair.either_gap.sum()),both_net_negative=int(pair.both_net_negative.sum()),forced_net=pair.forced_inverse_net.sum(),forced_winrate=(pair.forced_inverse_net>0).mean(),fixed_bracket_net=pair.fixed_bracket_net.sum(),fixed_bracket_winrate=(pair.fixed_bracket_net>0).mean())
 (OUT/f'{ds}_exact_mirror.json').write_text(json.dumps(summary,indent=2));print(summary,flush=True)
def compare():
 new=pd.concat([pd.read_csv(OUT/f'{ds}_challenge_recomputed.csv') for ds in ['master','legacy']]);old=pd.read_csv(R/'BUCKO_REVERSE_02_Challenge_Results.csv');key=['dataset','config_id','cohort'];new=new.set_index(key).sort_index();old=old.set_index(key).sort_index();assert new.index.equals(old.index)
 bad=[]
 for col in old.columns:
  a,b=new[col],old[col]
  if pd.api.types.is_numeric_dtype(b):
   ok=np.isclose(a,b,rtol=0,atol=1e-8,equal_nan=True)
  else:ok=(a==b).to_numpy()
  if not ok.all():bad.append({'column':col,'mismatches':int((~ok).sum()),'sample':[str(old.index[i]) for i in np.flatnonzero(~ok)[:3]],'new':a.iloc[np.flatnonzero(~ok)[:3]].tolist(),'released':b.iloc[np.flatnonzero(~ok)[:3]].tolist()})
 (OUT/'report_recomputation_check.json').write_text(json.dumps({'rows':len(old),'mismatches':bad},indent=2));print('Matrix comparison',bad,flush=True)
 if bad:raise AssertionError('Released matrix comparison failed')
if __name__=='__main__':
 if sys.argv[1]=='compare':compare()
 else:
  ds=sys.argv[1];accounts(ds);books(ds)
