"""Readable independent Python reference for the account state machine (R2)."""
import math
RISK=[100,200,300,400,500,575]
def run(path,days,outcomes,index,config,bootstrap=False):
 f,rr,sc,rid,pol=config
 eq=0.;floor=-1000.;peak=0.;dd=0.;best=0.;evaleq=0.;phase=0;last=0;ps=0;wd=0;et=ft=ae=af=de=df=0;passstep=passcal=status=elapsed=used=0;cash=0.;prev=-1;events=[]
 for step,day in enumerate(path):
  if day<0:status=8;break
  if step:
   gap=days[day,0]-days[prev,0] if not bootstrap or day==prev+1 else days[day,0]-days[day-1,0] if day>0 else 1
   elapsed+=max(1,gap)
  prev=day
  if phase==1 and ps==0:last=elapsed
  if elapsed-last>=30:status=2 if phase==0 else 5;break
  used+=1;ps+=1;start=eq;locked=False;traded=False;busy=-1
  for oid in index[f*6+rr][day]:
   z=outcomes[oid]
   if locked or z[1]<busy:continue
   risk=RISK[rid] if phase==0 else min(200,RISK[rid]);cap=20 if phase==0 or start>=1000 else 10
   q=max(0,min(cap,math.floor((min(risk,600+eq-start-25,eq-floor-25)+1e-9)/z[18])))
   if not q:continue
   events.append((step,phase,oid,q));traded=True
   if phase==0:et+=1
   else:ft+=1
   if z[11]:status=8 if z[11]==2 else 9;break
   low=eq+q*z[19];net=q*z[16];dd=max(dd,peak-low);dll=low<=start-600+1e-9;mll=low<=floor+1e-9
   if dll:
    if phase==0:de+=1
    else:df+=1
    locked=True
   eq+=net
   if abs(net)>=1:last=elapsed
   peak=max(peak,eq);busy=z[3]
   if mll:status=1 if phase==0 else 4;break
   dn=eq-start
   if pol and (dn>=(300 if pol==1 else 600) or dn<=-300):locked=True
   if phase==0 and eq>=1250 and max(best,dn)<=eq*.5+1e-9:locked=True
   req=min(1000,eq*.5)
   if phase==1 and wd+(dn>=100)>=5 and req>=500 and eq-req>100:locked=True
  if traded:
   if phase==0:ae+=1
   else:af+=1
  if status:break
  daily=eq-start;best=max(best,daily);floor=max(floor,min(100,eq-1000))
  if phase==0 and eq>=1250 and best<=eq*.5+1e-9:
   passstep=used;passcal=elapsed+1;evaleq=eq;phase=1;eq=0.;floor=-1000.;peak=best=0.;ps=0;last=elapsed;continue
  if phase==1:
   if daily>=100:wd+=1
   req=min(1000,eq*.5)
   if wd>=5 and req>=500 and eq-req>100:cash=.9*req;eq-=req;floor=100;status=7;break
  if ps>=60:status=3 if phase==0 else 6;break
 if not status:status=8
 if phase==0:evaleq=eq
 return [status,int(passstep>0),int(status==7),passstep,passcal,ae,af,used,elapsed+1,et,ft,de,df,int(status==1),int(status==4),int(status==2),int(status==5),int(status==3),int(status==6),int(status==8),int(status==9),cash,eq,dd,evaleq,eq if phase else 0,wd],events
