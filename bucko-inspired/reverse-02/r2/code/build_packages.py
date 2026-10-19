"""Deterministic package writer; no account or signal mutations."""
from pathlib import Path
import json,hashlib,zipfile
R=Path(__file__).resolve().parents[1]
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def writezip(target,entries):
 with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p,name in sorted(entries,key=lambda x:x[1]):
   zi=zipfile.ZipInfo(name,date_time=(2026,10,19,0,0,0));zi.external_attr=0o100644<<16;zi.compress_type=zipfile.ZIP_STORED if p.suffix=='.gz' else zipfile.ZIP_DEFLATED;z.writestr(zi,p.read_bytes(),compresslevel=6)
 with zipfile.ZipFile(target) as z:assert z.testzip() is None
 print(target.name,target.stat().st_size,sha(target),flush=True)
def main():
 inputs=[]
 names=['bars.bin','seeds.bin','seeds.csv.gz','days.bin','days.csv','paths.bin','paths.npy','paths.csv','metadata.json','signals_monthly.csv','candidate_outcomes.csv.gz','candidate_dispositions.csv']
 for ds in ['master','legacy']:
  for name in names:
   p=R/'work'/ds/name;assert p.is_file();inputs.append((p,'reverse02/work/'+ds+'/'+name))
 ip=R/'INPUT_MANIFEST_SHA256.json';ip.write_text(json.dumps({n:sha(p) for p,n in inputs},indent=2));inputs.append((ip,'reverse02/'+ip.name));writezip(R/'BUCKO_REVERSE_02_Frozen_Inputs.zip',inputs)
 core=[]
 for folder in ['code','sources','results']:
  for p in sorted((R/folder).rglob('*')):
   if p.is_file() and '__pycache__' not in p.parts:core.append((p,'reverse02/'+str(p.relative_to(R))))
 for name in ['README.md','DELIVERY_RECOVERY.md','RECOVERY.md','PROTOCOL.md','R2_CODE_LOCK.json','BUCKO_REVERSE_02_Executive_Decision.pdf','BUCKO_REVERSE_02_Monte_Carlo_Report.pdf','BUCKO_REVERSE_02_Challenge_Results.csv','BUCKO_REVERSE_02_Payout_Economics.xlsx','BUCKO_REVERSE_02_QA.md','BUCKO_REVERSE_02_Ledger_Manifest.csv']:
  core.append((R/name,'reverse02/'+name))
 for name in ['execution.py','prepare_data.py']:
  p=R.parent/'reverse01/baseline/code'/name;core.append((p,'reverse01/baseline/code/'+name))
 manifest=R/'MANIFEST_SHA256.json';manifest.write_text(json.dumps({n:sha(p) for p,n in core},indent=2));core.append((manifest,'reverse02/'+manifest.name));writezip(R/'BUCKO_REVERSE_02_Reproducible_Package.zip',core)
 text=''.join(sha(R/n)+'  '+n+'\n' for n in ['BUCKO_REVERSE_02_Reproducible_Package.zip','BUCKO_REVERSE_02_Frozen_Inputs.zip'])
 (R/'BUCKO_REVERSE_02_Package_Hashes.txt').write_text(text)
if __name__=='__main__':main()
