"""Seven explicit lifecycle fixtures; compare every field to Python reference."""
from pathlib import Path
import numpy as np,pandas as pd,subprocess,json
from reference import run
R=Path(__file__).resolve().parents[1]
def test(name,net,mae,unknown,expected):
 w=R/'work'/('synthetic_'+name);w.mkdir(exist_ok=True)
 days=np.column_stack([np.arange(120,dtype=np.int32),np.ones(120,dtype=np.int32)]);days.tofile(w/'days.bin');path=np.arange(120,dtype=np.int32);path.tofile(w/'paths.bin')
 out=[]
 for d,(n,m,u) in enumerate(zip(net,mae,unknown)):
  out.append([d,d*3,d*3+1,d*3+1,d,0,0,0,1,4,0,u,100,96,110,110,n,n+2,10,m,d*86400,d*86400+60])
 o=np.array(out,dtype='<f8');o.tofile(w/'outcomes.bin');index=[[[] for _ in days] for _ in range(12)]
 for i,z in enumerate(o):index[0][int(z[4])].append(i)
 py,events=run(path,days,o,index,(0,0,0,0,0),False)
 subprocess.run([str(R/'work/engine'),'accounts',str(w),'0','1','noaudit'],check=True,stdout=subprocess.DEVNULL)
 a=pd.read_csv(w/'accounts_sc0.csv.gz');got=a[a.config_id==0].iloc[0,3:].to_numpy(float)
 assert np.allclose(got,py,atol=1e-8,rtol=0),(name,got,py)
 assert got[0]==expected,(name,got[0],expected)
 if name=='payout':assert got[21]==450 and got[3]==7
 if name=='dll_softlock':assert got[11]==1 and got[13]==0
 return {'case':name,'expected_status':expected,'fields_equal':27,'pass':True}
def main():
 cases=[('payout',[20]*20,[-2]*20,[0]*20,7),('gap_mll',[-120],[-120],[0],1),('dll_softlock',[-65],[-65],[0],2),('unresolved',[20],[-2],[1],9),('sample_end',[20],[-2],[2],8),('eval_timeout',[-.1]*120,[-2]*120,[0]*120,3),('funded_timeout',[20]*7+[-.1]*113,[-2]*120,[0]*120,6)]
 log=[test(*x) for x in cases];(R/'results/synthetic_tests.json').write_text(json.dumps(log,indent=2));print(log)
if __name__=='__main__':main()
