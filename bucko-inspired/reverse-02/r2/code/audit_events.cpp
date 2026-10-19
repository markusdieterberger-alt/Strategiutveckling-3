// Independent streaming reconciliation of every normalized event.
#define main frozen_engine_main
#include "engine.cpp"
#undef main
#include <filesystem>
int main(int argc,char**argv){try{
 string dir=argv[1];int sc=atoi(argv[2]);auto out=readbin<Row<22>>(dir+"/outcomes.bin");auto days=readbin<array<int,2>>(dir+"/days.bin");auto paths=readbin<array<int,120>>(dir+"/paths.bin");
 GZ dest(dir+"/event_reconciliation_sc"+to_string(sc)+".csv.gz","config_id,path_id,eval_trades,funded_trades,eval_net,funded_net\n");
 int cfg=-1,pid=-1,laststep=-1,phase=-1,busy=-1,ne=0,nf=0,wd=0;double eq=0,fl=-1000,start=0,best=0,es=0,fs=0;bool locked=false,terminal=false;long long total=0;
 auto flush=[&](){if(cfg>=0){ostringstream s;s.precision(15);s<<cfg<<','<<pid<<','<<ne<<','<<nf<<','<<es<<','<<fs<<'\n';dest.put(s.str());}};
 for(int part=0;;part++){
  char file[300];snprintf(file,sizeof(file),"%s/events_sc%d_part%03d.csv.gz",dir.c_str(),sc,part);if(!filesystem::exists(file))break;
  gzFile input=gzopen(file,"rb");gzbuffer(input,1<<20);char line[512];assert(gzgets(input,line,sizeof(line)));
  while(gzgets(input,line,sizeof(line))){char *p=line;int v[6];for(int j=0;j<6;j++){v[j]=strtol(p,&p,10);if(j<5){assert(*p==',');p++;}}int c=v[0],id=v[1],step=v[2],ph=v[3],oid=v[4],q=v[5];
   if(c!=cfg||id!=pid){flush();cfg=c;pid=id;laststep=-1;phase=-1;busy=-1;ne=nf=wd=0;eq=0;fl=-1000;start=best=es=fs=0;locked=terminal=false;}
   assert(!terminal);int pol=cfg%3,ri=(cfg/3)%6,ss=(cfg/18)%4,rr=(cfg/72)%6,f=cfg/432;assert(ss==sc);auto z=out.at(oid);assert(z[FAMILY]==f&&z[RRID]==rr&&z[SC]==sc);assert(paths.at(pid).at(step)==z[DAY]);
   if(ph!=phase){assert(ph==0||phase==0);phase=ph;eq=0;fl=-1000;start=best=0;wd=0;laststep=-1;}
   if(step!=laststep){if(laststep>=0){double daynet=eq-start;fl=max(fl,min(100.,eq-1000));best=max(best,daynet);if(phase==1&&daynet>=100)wd++;}laststep=step;start=eq;locked=false;busy=-1;}
   assert(!locked&&z[SIGNAL]>=busy);double risk=phase==0?RISK[ri]:min(200.,RISK[ri]);int cap=phase==0||start>=1000?20:10;int expected=max(0,min(cap,(int)floor((min({risk,600+eq-start-25,eq-fl-25})+1e-9)/z[LOSS])));assert(q>0&&q==expected);
   if(phase==0)ne++;else nf++;total++;
   if(z[UNKNOWN]){terminal=true;continue;}
   double low=eq+q*z[MAE],net=q*z[NET];if(low<=start-600+1e-9)locked=true;if(low<=fl+1e-9)terminal=true;eq+=net;if(phase==0)es+=net;else fs+=net;busy=z[EXIT];double dn=eq-start;
   if(pol&&(dn>=(pol==1?300:600)||dn<=-300))locked=true;
   if(phase==0&&eq>=1250&&max(best,dn)<=eq*.5+1e-9)locked=true;
   if(phase==1&&wd+(dn>=100)>=5&&min(1000.,eq*.5)>=500&&eq-min(1000.,eq*.5)>100)locked=true;
  }
  int err;gzerror(input,&err);assert(err==Z_OK||err==Z_STREAM_END);assert(gzclose(input)==Z_OK);
 }
 flush();dest.close();ofstream n(dir+"/event_audit_sc"+to_string(sc)+".json");n<<"{\"rows\":"<<total<<",\"all_event_invariants\":true}";cout<<dir<<" sc"<<sc<<" audited "<<total<<endl;return 0;
 }catch(exception&e){cerr<<e.what()<<endl;return 3;}}
