"""Deterministic rerun. Run in a new extraction directory, never over prior work."""
from pathlib import Path
import argparse,subprocess,sys,json,hashlib,concurrent.futures
R=Path(__file__).resolve().parents[1]
def call(args):subprocess.run([str(x) for x in args],check=True,cwd=R)
def main():
 p=argparse.ArgumentParser();p.add_argument('--from-traces',action='store_true');p.add_argument('--workers',type=int,default=4);a=p.parse_args()
 (R/'work').mkdir(exist_ok=True);(R/'results').mkdir(exist_ok=True)
 for name,h in json.loads((R/'R2_CODE_LOCK.json').read_text())['sha256'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==h,name
 for src,exe in [('engine.cpp','engine'),('audit_events.cpp','audit_events')]:call(['g++','-O3','-std=c++17',R/'code'/src,'-lz','-o',R/'work'/exe])
 call([R/'work/engine','test'])
 for ds in ['master','legacy']:
  if a.from_traces:call([sys.executable,R/'code/prepare.py',ds])
  else:assert all((R/'work'/ds/f).exists() for f in ['bars.bin','seeds.bin','days.bin','paths.bin']), 'Extract Frozen_Inputs.zip first'
  call([R/'work/engine','outcomes',R/'work'/ds])
 call([sys.executable,R/'code/validate.py']);call([sys.executable,R/'code/synthetic_tests.py'])
 jobs=[(ds,sc) for ds in ['master','legacy'] for sc in range(4)]
 with concurrent.futures.ThreadPoolExecutor(a.workers) as ex:
  for _ in ex.map(lambda j:call([R/'work/engine','accounts',R/'work'/j[0],j[1]]),jobs):pass
 with concurrent.futures.ThreadPoolExecutor(a.workers) as ex:
  for _ in ex.map(lambda j:call([R/'work/audit_events',R/'work'/j[0],j[1]]),jobs):pass
 call([sys.executable,R/'code/reconcile.py'])
 for ds in ['master','legacy']:call([sys.executable,R/'code/analyze.py',ds])
 call([sys.executable,R/'code/analyze.py','compare']);call([sys.executable,R/'code/stage_delivery.py'])
 print('Complete. Financial matrix verified against the released reference; all ledger hashes checked.')
if __name__=='__main__':main()
