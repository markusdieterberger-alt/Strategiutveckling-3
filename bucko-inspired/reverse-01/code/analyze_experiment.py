"""Prespecified, descriptive economic comparisons; no model selection or tuning."""
from pathlib import Path
import json, math, importlib.util
import numpy as np
import pandas as pd
from reverse_adapter import ROOT, BASE, execution

spec=importlib.util.spec_from_file_location('recon04_analysis',BASE/'code/analyze.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
OUT=ROOT/'results/analysis'

def main():
    OUT.mkdir(exist_ok=True)
    matrix=pd.concat([pd.read_csv(ROOT/f'results/economic_{d}/summary.csv') for d in ['master','legacy']],ignore_index=True)
    assert len(matrix)==36
    for dataset in ['master','legacy']:
        assert json.loads((ROOT/f'results/economic_{dataset}/run_completed.json').read_text())['original_parity_pass']
    matrix.to_csv(ROOT/'BUCKO_REVERSE_01_Test_Matrix.csv',index=False)
    records={n:[] for n in ['bootstrap','monthly','yearly','breakdowns','halves','winner_concentration','candidate_dispositions','risk_diagnostics','weekly','before_after_costs','exit_diagnostics']}
    ledgers=[];daily_dates={};weights={};daily=[];ledger_qa=[];books={}
    for row in matrix.itertuples():
        folder=ROOT/f'results/economic_{row.dataset}'
        t=pd.read_csv(folder/(row.variant+'_trades.csv.gz'));c=pd.read_csv(folder/(row.variant+'_candidates.csv.gz'));d=pd.read_csv(folder/(row.variant+'_daily.csv'))
        ledgers.append(t);books[row.variant]=t
        meta=dict(variant=row.variant,dataset=row.dataset,model=row.model,scenario=row.scenario,rr=row.rr)
        gp=t.gross_before_costs_usd
        records['before_after_costs'].append(dict(**meta,gross_same_book_net_usd=float(gp.sum()),gross_same_book_pf=float(gp[gp>0].sum()/-gp[gp<0].sum()),gross_same_book_winrate=float((gp>0).mean()),net_usd=float(t.net_usd.sum()),friction_usd=float((gp-t.net_usd).sum())))
        for week,g in t.groupby(pd.to_datetime(t.trade_date).dt.to_period('W-SUN').astype(str)):records['weekly'].append(dict(**meta,week=week,**execution.summary(g)))
        for reason,g in c.groupby('disposition'):records['candidate_dispositions'].append(dict(**meta,reason=reason,count=len(g)))
        if row.dataset not in daily_dates:
            daily_dates[row.dataset]=sorted(d.trade_date.unique());weights[row.dataset]=old.boot_weights(len(daily_dates[row.dataset]))
        x=pd.DataFrame({'trade_date':t.trade_date,'profit':t.net_usd.clip(lower=0),'loss':(-t.net_usd).clip(lower=0),'net':t.net_usd,'n':1,'r':t.net_R}).groupby('trade_date').sum().reindex(daily_dates[row.dataset],fill_value=0)
        bx=weights[row.dataset]@x[['profit','loss','net','n','r']].to_numpy()
        with np.errstate(divide='ignore',invalid='ignore'):
            ep=bx[:,2]/bx[:,3];er=bx[:,4]/bx[:,3];pf=bx[:,0]/bx[:,1]
        records['bootstrap'].append(dict(**meta,days=len(x),draws=5000,block_days=5,net_usd_ci95_low=old.q(bx[:,2])[0],net_usd_ci95_high=old.q(bx[:,2])[1],expectancy_ci95_low=old.q(ep)[0],expectancy_ci95_high=old.q(ep)[1],expectancy_R_ci95_low=old.q(er)[0],expectancy_R_ci95_high=old.q(er)[1],pf_ci95_low=old.q(pf)[0],pf_ci95_high=old.q(pf)[1],expectancy_family98_333_low=old.q(ep,.05/6,1-.05/6)[0],expectancy_family98_333_high=old.q(ep,.05/6,1-.05/6)[1],bootstrap_positive_fraction=float((bx[:,2]>0).mean())))
        for month in sorted({x[:7] for x in daily_dates[row.dataset]}):
            g=t[t.trade_date.str[:7]==month];records['monthly'].append(dict(**meta,month=month,**execution.summary(g)))
        for year,g in t.groupby(t.trade_date.str[:4]):records['yearly'].append(dict(**meta,year=year,**execution.summary(g)))
        for field in ['direction','source_direction','score','signal_type','ema_regime','chop_regime','score_session']:
            for group,g in t.groupby(field):records['breakdowns'].append(dict(**meta,field=field,group=str(group),small_sample=len(g)<30,**execution.summary(g)))
        midpoint=pd.Timestamp('2026-04-01',tz='UTC') if row.dataset=='master' else pd.Timestamp(row.start_utc)+(pd.Timestamp(row.end_bar_utc)-pd.Timestamp(row.start_utc))/2
        et=pd.to_datetime(t.entry_time,utc=True)
        for part,sel in [('first',et<midpoint),('second',et>=midpoint)]:
            g=t[sel];records['halves'].append(dict(**meta,half=part,boundary_utc=midpoint.isoformat(),first_entry=g.entry_time.min(),last_exit=g.exit_time.max(),**execution.summary(g)))
        winners=t[t.net_usd>0].sort_values('net_usd',ascending=False)
        for name,k in [('top1',1),('top5',5),('top10',10),('top5pct_winners',int(math.ceil(len(winners)*.05)))]:
            removed=winners.head(k);remain=t.drop(removed.index)
            records['winner_concentration'].append(dict(**meta,remove=name,removed_trades=len(removed),removed_profit_usd=float(removed.net_usd.sum()),remaining_net_usd=float(remain.net_usd.sum()),remaining_expectancy_usd=float(remain.net_usd.mean()),share_of_positive_profit=float(removed.net_usd.sum()/winners.net_usd.sum()) if len(winners) else None))
        daily_net=t.groupby('trade_date').net_usd.sum()
        records['risk_diagnostics'].append(dict(**meta,risk_median=float(t.risk_usd.median()),risk_p95=float(t.risk_usd.quantile(.95)),risk_max=float(t.risk_usd.max()),initial_risk_over600=int((t.risk_usd>600).sum()),days_net_below_minus600=int((daily_net<-600).sum()),worst_closed_day=float(daily_net.min()),best_closed_day=float(daily_net.max())))
        for reason,g in t.groupby('exit_reason'):
            records['exit_diagnostics'].append(dict(**meta,exit_reason=reason,trades=len(g),net_usd=float(g.net_usd.sum()),mean_hold_minutes=float(g.holding_minutes.mean()),max_hold_minutes=float(g.holding_minutes.max())))
        dx=x.reset_index();dx['variant']=row.variant;daily.append(dx)
        g=t.sort_values('entry_time');eq=(g.effective_exit_price-g.entry_fill)*g.direction*2-g.commission_usd
        nonoverlap=(pd.to_datetime(g.entry_time.iloc[1:].reset_index(drop=True),utc=True)>=pd.to_datetime(g.exit_time.iloc[:-1].reset_index(drop=True),utc=True)).all()
        ledger_qa.append(dict(variant=row.variant,trades=len(g),unique_ids=bool(g.trade_id.is_unique),nonoverlap=bool(nonoverlap),pnl_max_error=float(np.max(np.abs(eq-g.net_usd))),grid_error_count=int((np.abs(g[['entry_fill','stop','target']]/.25-np.round(g[['entry_fill','stop','target']]/.25))>1e-8).sum().sum()),sl_side_correct=bool(((g.entry_fill-g.stop)*g.direction>0).all()),tp_side_correct=bool(((g.target-g.entry_fill)*g.direction>0).all()),source_direction_correct=bool((g.source_direction==(g.direction if row.model=='ORIGINAL' else -g.direction)).all())))
    alltr=pd.concat(ledgers,ignore_index=True);assert alltr.trade_id.is_unique
    alltr.to_csv(ROOT/'BUCKO_REVERSE_01_Trade_Ledger.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    for name,data in records.items():pd.DataFrame(data).to_csv(OUT/(name+'.csv'),index=False)
    daily=pd.concat(daily,ignore_index=True);daily.to_csv(OUT/'daily_trade_sums.csv',index=False)
    sig=pd.concat([pd.read_csv(ROOT/f'results/economic_{d}/signals_monthly.csv') for d in ['master','legacy']],ignore_index=True);sig.to_csv(OUT/'signals_monthly.csv',index=False)
    paired=[];book_overlap=[]
    for row in matrix[matrix.model=='REVERSE'].itertuples():
        orig=row.variant.replace('__REVERSE__','__ORIGINAL__')
        a=daily[daily.variant==orig].set_index('trade_date').loc[daily_dates[row.dataset]]
        b=daily[daily.variant==row.variant].set_index('trade_date').loc[daily_dates[row.dataset]]
        diff=b.net-a.net;bd=weights[row.dataset]@diff.to_numpy()
        paired.append(dict(dataset=row.dataset,scenario=row.scenario,rr=row.rr,reverse_minus_original_net_usd=float(diff.sum()),paired_difference_ci95_low=old.q(bd)[0],paired_difference_ci95_high=old.q(bd)[1],difference_family98_333_low=old.q(bd,.05/6,1-.05/6)[0],difference_family98_333_high=old.q(bd,.05/6,1-.05/6)[1],fraction_positive_difference=float((bd>0).mean())))
        aa=books[orig];bb=books[row.variant];common=aa.merge(bb,on=['signal_time','source_direction'],suffixes=('_original','_reverse'))
        book_overlap.append(dict(dataset=row.dataset,scenario=row.scenario,rr=row.rr,original_trades=len(aa),reverse_trades=len(bb),same_source_signal_trades=len(common),original_only=len(aa)-len(common),reverse_only=len(bb)-len(common),same_stop_count=int((common.stop_original==common.stop_reverse).sum()),same_target_count=int((common.target_original==common.target_reverse).sum())))
    pd.DataFrame(paired).to_csv(OUT/'paired_bootstrap.csv',index=False);pd.DataFrame(book_overlap).to_csv(OUT/'trade_book_overlap.csv',index=False)
    assert all(x['unique_ids'] and x['nonoverlap'] and x['pnl_max_error']<1e-7 and x['grid_error_count']==0 and x['sl_side_correct'] and x['tp_side_correct'] and x['source_direction_correct'] for x in ledger_qa)
    (OUT/'ledger_qa.json').write_text(json.dumps(ledger_qa,indent=2))
    # Combined gap/risk flags remain visible; these are diagnostics, never exclusions.
    gap=[]
    for row in matrix.itertuples():
        t=books[row.variant];g=t[t.exit_reason=='DATA_GAP']
        gap.append(dict(variant=row.variant,dataset=row.dataset,model=row.model,scenario=row.scenario,rr=row.rr,gap_exit_trades=len(g),gap_exit_net_usd=float(g.net_usd.sum()),non_gap_net_usd=float(t[t.exit_reason!='DATA_GAP'].net_usd.sum()),late_cutoff_exits=row.late_cutoff_exits,entry_gaps=row.entry_gaps))
    pd.DataFrame(gap).to_csv(OUT/'gap_diagnostics.csv',index=False)
    (OUT/'analysis_completed.json').write_text(json.dumps(dict(matrix_rows=len(matrix),ledger_rows=len(alltr),ledger_qa_all_pass=True,bootstrap_method='5000 circular five-observed-trade-day blocks, seed20261017, same weights for original/reverse; zero-trade days retained',post_hoc_exploratory=True),indent=2))
    print(matrix[matrix.scenario=='BASE1'][['dataset','model','rr','trades','winrate','pf','net_usd','expectancy_usd','expectancy_R','max_closed_dd_usd','max_barclose_mtm_dd_usd']].to_string(index=False))
    print('Ledger rows:',len(alltr))

if __name__=='__main__':main()
