"""Reconcile every account's phase P&L and event counts after streaming audit."""
from pathlib import Path
import pandas as pd,numpy as np,json
R=Path(__file__).resolve().parents[1]
def main():
 checks=[]
 for ds in ['master','legacy']:
  for sc in range(4):
   w=R/'work'/ds;a=pd.read_csv(w/f'accounts_sc{sc}.csv.gz').set_index(['config_id','path_id']);e=pd.read_csv(w/f'event_reconciliation_sc{sc}.csv.gz').set_index(['config_id','path_id']).reindex(a.index,fill_value=0)
   assert (a.eval_trades==e.eval_trades).all() and (a.funded_trades==e.funded_trades).all()
   assert np.allclose(a.eval_final_equity,e.eval_net,atol=1e-8,rtol=0)
   assert np.allclose(a.funded_final_equity+a.cash/.9,e.funded_net,atol=1e-8,rtol=0)
   n=json.loads((w/f'event_audit_sc{sc}.json').read_text())['rows'];assert n==int((a.eval_trades+a.funded_trades).sum())
   checks.append(dict(dataset=ds,scenario=sc,accounts=len(a),events=n,all_phase_cash_and_counts_equal=True));print(checks[-1],flush=True)
 assert sum(x['accounts'] for x in checks)==8731584;assert sum(x['events'] for x in checks)==231893069
 (R/'results/event_reconciliation.json').write_text(json.dumps(checks,indent=2))
if __name__=='__main__':main()
