from pathlib import Path
import sys,json,subprocess,hashlib
import numpy as np,pandas as pd
from reference import run
R=Path(__file__).resolve().parents[1]
def main():
 logs=[]
 for ds in ['master','legacy']:
  src=R/'work'/ds;o=np.fromfile(src/'outcomes.bin','<f8').reshape(-1,22);b=np.fromfile(src/'bars.bin','<f8').reshape(-1,10);seeds=pd.read_csv(src/'seeds.csv.gz');days=np.fromfile(src/'days.bin','<i4').reshape(-1,2);paths=np.fromfile(src/'paths.bin','<i4').reshape(-1,120)
  assert (o[:,2]==o[:,1]+1).all();assert (o[:,8]*(o[:,12]-o[:,13])>0).all();assert (o[:,8]*(o[:,14]-o[:,12])>0).all();assert np.allclose(o[:,16],o[:,17]-(2+(o[:,7]%2)));assert (o[:,18]>0).all()
  assert np.allclose(o[:,8],np.where(o[:,5]==2,1,-1)*seeds.source_direction.to_numpy()[o[:,0].astype(int)])
  # Direct bracket comparison against the unchanged source execution function.
  sys.path.insert(0,str(R.parent/'reverse01/baseline/code'));import execution
  rng=np.random.default_rng(178);checked=0
  for oid in rng.choice(len(o),min(1500,len(o)),replace=False):
   z=o[oid];e,j=int(z[2]),int(z[3]);sc=int(z[7]);scenario=execution.Scenario('R2',sc%2+1,1,sc>=2)
   if z[9] in [1,2,3,4]:
    h=execution.hit_bracket(int(z[8]),z[13],z[14],b[j,1],b[j,2],b[j,3],j==e,scenario)
    assert h is not None and abs(h[0]-z[15])<1e-8,(oid,h,z.tolist());checked+=1
  for sc in [0,3]:
   tmp=R/'work'/f'parity_{ds}_{sc}';tmp.mkdir(exist_ok=True)
   # Include chronological and bootstrap path prefixes, identically ordered in both engines.
   pp=paths[:len(days)+3]
   pp.tofile(tmp/'paths.bin')
   for name in ['outcomes.bin','days.bin']:
    p=tmp/name
    if not p.exists():p.symlink_to(src/name)
   subprocess.run([str(R/'work/engine'),'accounts',str(tmp),str(sc),str(len(pp)),'noaudit'],check=True)
   c=pd.read_csv(tmp/f'accounts_sc{sc}.csv.gz');index=[[[] for _ in days] for _ in range(12)]
   for k,z in enumerate(o):
    if z[5]<2 and z[7]==sc:index[int(z[5])*6+int(z[6])][int(z[4])].append(k)
   c=c[(c.path_id<5)|(c.path_id>=len(days)-2)]
   for row in c.itertuples(index=False):
    cfg=row.config_id;pol=cfg%3;v=cfg//3;ri=v%6;v//=6;ss=v%4;v//=4;rr=v%6;f=v//6
    expected,events=run(pp[row.path_id],days,o,index,(f,rr,ss,ri,pol),bool(row.bootstrap))
    got=np.array(list(row)[3:],float);assert np.allclose(got,expected,rtol=0,atol=1e-8),(ds,sc,cfg,row.path_id,got,expected)
   logs.append({'dataset':ds,'scenario':sc,'full_account_paths':len(c),'pass':True,'bracket_comparisons':checked})
 (R/'results/validation.json').write_text(json.dumps(logs,indent=2));print(json.dumps(logs),flush=True)
if __name__=='__main__':main()
