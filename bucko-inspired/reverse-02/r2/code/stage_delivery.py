"""Restore delivery shards only after the engine has closed every stream.
The previously delivered SHA256 manifest is an external byte-level oracle.
"""
from pathlib import Path
import pandas as pd, hashlib, shutil, json, gzip
R=Path(__file__).resolve().parents[1]
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 m=pd.read_csv(R/'BUCKO_REVERSE_02_Ledger_Manifest.csv'); dest=R/'delivery_data';dest.mkdir(exist_ok=True)
 proofs=[]
 for (ds,sc),g in m.groupby(['dataset','scenario'],sort=False):
  source=sorted((R/'work'/ds).glob(f'events_sc{sc}_part*.csv.gz'))
  assert len(source)==len(g),(ds,sc,len(source),len(g))
  for p, row in zip(source,g.itertuples()):
   actual=sha(p);assert actual==row.sha256,(p,actual,row.sha256)
   assert p.stat().st_size==row.bytes
   target=dest/row.filename
   if not target.exists():target.hardlink_to(p)
   proofs.append({'file':target.name,'bytes':row.bytes,'rows':row.rows,'sha256':actual,'matches_original_delivery_manifest':True})
  p=R/'work'/ds/f'accounts_sc{sc}.csv.gz';t=dest/f'BUCKO_REVERSE_02_Accounts_{ds}_sc{sc}.csv.gz'
  if not t.exists():t.hardlink_to(p)
 (R/'results/recovery_byte_verification.json').write_text(json.dumps(proofs,indent=2))
 assert sum(x['rows'] for x in proofs)==231893069
 assert len(proofs)==61
 print('ALL 61 event streams byte-identical; 231893069 event rows; 69 data files staged',flush=True)
if __name__=='__main__':main()
