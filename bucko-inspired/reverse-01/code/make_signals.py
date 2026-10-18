"""Regenerate exact frozen RECON04 signal telemetry from delivered normalized prices."""
from reverse_adapter import ROOT,BASE,source
from pathlib import Path
import pandas as pd,json,time,hashlib

def main():
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--dataset',choices=['master','legacy'],required=True);a=ap.parse_args()
 folder=ROOT/'cache/signals';folder.mkdir(parents=True,exist_ok=True)
 prices=pd.read_csv(BASE/('data/master.csv.gz' if a.dataset=='master' else 'data/legacy_calendar_roll.csv.gz'))
 groups=[('master',prices)] if a.dataset=='master' else prices.groupby('symbol',sort=False)
 audit=[]
 for name,b in groups:
  start=time.monotonic();r=source.run_original(b)
  p=folder/f'{a.dataset}_{name}.csv.gz';temp=p.with_suffix('.tmp')
  r.to_csv(temp,index=False,compression={'method':'gzip','mtime':0});temp.replace(p)
  item=dict(file=p.name,bars=len(r),approved=int((r.approved_mask>0).sum()),raw=int((r.raw_mask>0).sum()),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),seconds=time.monotonic()-start)
  audit.append(item);print(json.dumps(item),flush=True)
 (ROOT/f'results/{a.dataset}_signal_replay.json').write_text(json.dumps(audit,indent=2))
if __name__=='__main__':main()
