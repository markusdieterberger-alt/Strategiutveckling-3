"""Lossless join of delivered normalized ledger for one account/config.
The source ledger is authoritative, not reconstructed from a one-contract book.
"""
from pathlib import Path
import argparse,pandas as pd,numpy as np
R=Path(__file__).resolve().parents[1]
def main():
 a=argparse.ArgumentParser();a.add_argument('--dataset',choices=['master','legacy'],required=True);a.add_argument('--config',type=int,required=True);a.add_argument('--path',type=int,required=True);a.add_argument('--output',type=Path,required=True);a=a.parse_args();sc=(a.config//18)%4;w=R/'work'/a.dataset
 m=pd.read_csv(R/'BUCKO_REVERSE_02_Ledger_Manifest.csv');m=m[(m.dataset==a.dataset)&(m.scenario==sc)];found=[]
 for row in m.itertuples():
  p=R/'delivery_data'/row.filename
  for z in pd.read_csv(p,chunksize=200000):
   if z.config_id.min()>a.config:break
   hit=z[(z.config_id==a.config)&(z.path_id==a.path)]
   if len(hit):found.append(hit)
 if not found:raise ValueError('No executed events for this account')
 e=pd.concat(found,ignore_index=True);o=pd.read_csv(w/'candidate_outcomes.csv.gz');x=e.merge(o,on='outcome_id',validate='many_to_one');days=pd.read_csv(w/'days.csv');x['source_session']=days.date.to_numpy()[x.day_id.to_numpy()];x['entry_utc']=pd.to_datetime(x.entry_epoch,unit='s',utc=True);x['exit_utc']=pd.to_datetime(x.exit_epoch,unit='s',utc=True)
 x['net_usd']=x.quantity*x.net_one_mnq;x.loc[x.data_unresolved!=0,'net_usd']=np.nan;x['gross_usd']=x.quantity*x.gross_one_mnq;x['planned_stop_risk_usd']=x.quantity*x.planned_loss_one_mnq
 x['phase_equity_after_trade']=x.groupby('phase').net_usd.cumsum();x['phase_equity_before_trade']=x.phase_equity_after_trade-x.net_usd
 acc=pd.read_csv(w/f'accounts_sc{sc}.csv.gz');row=acc[(acc.config_id==a.config)&(acc.path_id==a.path)].iloc[0]
 assert len(x[x.phase==0])==row.eval_trades and len(x[x.phase==1])==row.funded_trades
 assert abs(x[x.phase==0].net_usd.sum()-row.eval_final_equity)<1e-8
 assert abs(x[x.phase==1].net_usd.sum()-row.funded_final_equity-row.cash/.9)<1e-8
 a.output.parent.mkdir(parents=True,exist_ok=True);x.to_csv(a.output,index=False);print({'trades':len(x),'status':int(row.status),'passed':bool(row.passed),'payout_cash':row.cash,'output':str(a.output)})
if __name__=='__main__':main()
