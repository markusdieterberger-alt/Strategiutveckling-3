"""Descriptive exit/vendor-quality audit; does not alter trades or select periods."""
from pathlib import Path
import json,hashlib
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
def main():
 out=ROOT/'results/analysis';t=pd.read_csv(ROOT/'BUCKO_RECON_04_Trade_Ledger.csv')
 t.groupby(['variant','exit_reason'],dropna=False).agg(trades=('net_usd','size'),net_usd=('net_usd','sum')).reset_index().to_csv(out/'exit_diagnostics.csv',index=False)
 c=pd.read_json(ROOT/'sources/databento/condition.json');d=c[c.condition!='available'].copy();d['date']=pd.to_datetime(d.date).dt.strftime('%Y-%m-%d');d.to_csv(out/'vendor_degraded_dates.csv',index=False)
 entry=pd.to_datetime(t.entry_time,utc=True).dt.strftime('%Y-%m-%d');exit_=pd.to_datetime(t.exit_time,utc=True).dt.strftime('%Y-%m-%d')
 flag=entry.isin(d.date)|exit_.isin(d.date)
 t[flag].groupby('variant').agg(trades=('net_usd','size'),net_usd=('net_usd','sum')).reset_index().to_csv(out/'vendor_degraded_trade_diagnostic.csv',index=False)
 checks=[]
 for row in pd.read_csv(ROOT/'BUCKO_RECON_04_Test_Matrix.csv').itertuples():
  g=t[t.variant==row.variant]
  assert len(g)==row.trades and abs(g.net_usd.sum()-row.net_usd)<1e-8
  months=pd.read_csv(out/'monthly.csv');m=months[months.variant==row.variant]
  assert m.trades.sum()==row.trades and abs(m.net_usd.sum()-row.net_usd)<1e-8
  checks.append(dict(variant=row.variant,summary_ledger_months_match=True))
 (ROOT/'results/summary_reconciliation.json').write_text(json.dumps(checks,indent=2))
 print('21 variants reconciled; vendor-quality flags retained without exclusions.')
if __name__=='__main__':main()
