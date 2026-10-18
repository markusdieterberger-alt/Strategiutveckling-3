"""Direction inversion AFTER frozen signal approval, without editing source engines."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'baseline'
sys.path.insert(0,str(BASE/'code'))
import execution as execution
import signal_adapter as source
from prepare_data import trade_dates

SIDE_PAIRS=[('score_L','score_S'),('mask_L','mask_S')]+[(x+'L',x+'S') for x in ['bos','sweep','fvg','sd']]
def execution_view(bars,reverse):
 """Swap approval and source attribution only. NEVER swap swing/prices/regime."""
 assert bars.approved_mask.isin([0,1,2]).all()
 v=bars.copy(deep=True)
 if reverse:
  v['approved_mask']=bars.approved_mask.map({0:0,1:2,2:1})
  for left,right in SIDE_PAIRS:v[left]=bars[right];v[right]=bars[left]
  v['signal_model']='REVERSE_01'
 return v

def simulate(bars,rr,scenario,blackouts,dataset,reverse):
 v=execution_view(bars,reverse)
 t,c,d,m=execution.simulate(v,rr,scenario,blackouts,dataset)
 for x in [t,c]:
  if len(x):
   x['source_direction']=-x.direction if reverse else x.direction
   x['model']='REVERSE' if reverse else 'ORIGINAL'
 return t,c,d,m
