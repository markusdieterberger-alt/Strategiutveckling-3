// R2 recovered protocol. Fixed double layouts make transport inspectable in Python.
#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
#include <zlib.h>
using namespace std;
template<int N> using Row=array<double,N>;
template<class T> vector<T> readbin(string p){ifstream f(p,ios::binary|ios::ate);if(!f)throw runtime_error(p);size_t n=f.tellg();if(n%sizeof(T))throw runtime_error("binary size");vector<T> r(n/sizeof(T));f.seekg(0);f.read((char*)r.data(),n);if(!f)throw runtime_error("binary read");return r;}
struct GZ {gzFile f;long long rows=0;GZ(string p,string h){f=gzopen(p.c_str(),"wb1");if(!f)throw runtime_error(p);gzbuffer(f,1<<20);put(h);}void put(string s){if(gzwrite(f,s.data(),s.size())!=(int)s.size())throw runtime_error("gzip write");}void close(){if(f){int z=gzclose(f);f=nullptr;if(z!=Z_OK)throw runtime_error("gzip close");}}~GZ(){close();}};
const double RR[6]={1,.75,.5,.33,.2,.1};const double RISK[6]={100,200,300,400,500,575};
enum {SEED,SIGNAL,ENTRY,EXIT,DAY,FAMILY,RRID,SC,DIR,REASON,BOTH,UNKNOWN,OPEN,STOP,TARGET,REFERENCE,NET,GROSS,LOSS,MAE,ENTRYTIME,EXITTIME,NC};
const string OH="outcome_id,seed_id,signal_bar,entry_bar,exit_bar,day_id,family,rr_id,scenario_id,direction,exit_reason,both_touch,data_unresolved,entry_open,stop,target,exit_reference,net_one_mnq,gross_one_mnq,planned_loss_one_mnq,adverse_pnl_one_mnq,entry_epoch,exit_epoch\n";
struct Hit {double price;int reason;bool both;};
Hit hit(int s,double st,double tp,double o,double h,double l,bool allow){if(s*(o-st)<=0)return{o,1,false};if(allow&&s*(o-tp)>=.25)return{tp,2,false};bool sh=s==1?l<=st:h>=st;bool th=allow&&(s==1?h>=tp+.25:l<=tp-.25);if(sh)return{st,3,th};if(th)return{tp,4,false};return{0,0,false};}
double floorEOD(double f,double eq){return max(f,min(100.,eq-1000));}
int sizeq(double risk,double dllroom,double mllroom,double loss,int cap){return max(0,min(cap,(int)floor((min(risk,min(dllroom-25,mllroom-25))+1e-9)/loss)));}
bool pass(double eq,double best){return eq>=1250&&best<=eq*.5+1e-9;}
double payout(double eq,int winDays){double x=min(1000.,eq*.5);return winDays>=5&&x>=500&&eq-x>100?x:0;}
void outcomes(string dir){auto b=readbin<Row<10>>(dir+"/bars.bin");auto seed=readbin<Row<7>>(dir+"/seeds.bin");vector<Row<NC>> out;GZ csv(dir+"/candidate_outcomes.csv.gz",OH);ofstream disp(dir+"/candidate_dispositions.csv");disp<<"seed_id,family,disposition\n";
 for(int k=0;k<(int)seed.size();k++){auto a=seed[k];int i=a[0],e=i+1,orig=a[1];
  for(int f=0;f<3;f++){
   int s=f==2?orig:-orig;int validationSide=f==0?s:orig;double oldstop=validationSide==1?a[2]-.25:a[3]+.25;
   string why="ELIGIBLE";if(!isfinite(oldstop))why="SL_MISSING";else if(validationSide*(a[4]-oldstop)<=0)why="SL_INVALID_CLOSE";else if(!a[5])why="SIGNAL_WINDOW";else if(e>=(int)b.size()||b[e][6]!=b[i][6])why="SEGMENT_END";else if(!b[e][7]||b[e][5]!=a[6])why="NEXT_OPEN_WINDOW";else if(validationSide*(b[e][1]-oldstop)<=0)why="NEXT_OPEN_STOP";
   disp<<k<<','<<f<<','<<why<<'\n';if(why!="ELIGIBLE")continue;
   for(int r=0;r<(f==2?1:6);r++)for(int sc=0;sc<4;sc++){
    double o=b[e][1],slip=(sc%2+1)*.25,cost=1+4*slip;double st=oldstop,tp;
    if(f==0){double actual=o+s*slip,dist=s*(actual-st);tp=actual+s*RR[r]*dist;}
    else {double dist=abs(o-oldstop);st=o-s*dist;tp=o+s*RR[r]*dist;}
    tp=s==1?ceil(tp/.25-1e-10)*.25:floor(tp/.25+1e-10)*.25;
    assert(s*(o-st)>0&&s*(tp-o)>0);double mae=-cost,ref=b.back()[4];int j=e,reason=7,both=0,unknown=2;bool atopen=false;
    for(;j<(int)b.size();j++){
     auto c=b[j];atopen=false;Hit h{0,0,false};
     if(j>e&&c[6]!=b[e][6]){j--;ref=b[j][4];reason=7;unknown=1;break;}
     if(j>e&&c[0]-b[j-1][0]!=60){h={c[1],5,false};atopen=true;unknown=(c[5]!=b[e][5]||c[9]>=1005)?1:0;}
     else if(j>e&&(c[5]!=b[e][5]||c[8])){h={c[1],6,false};atopen=true;unknown=(c[5]!=b[e][5]||c[9]>=1005)?1:0;}
     else {h=hit(s,st,tp,c[1],c[2],c[3],!(sc>=2&&j==e));atopen=h.reason==1||h.reason==2;unknown=0;}
     if(atopen)mae=min(mae,2*s*(c[1]-o)-cost);
     else {double adverse=s==1?max(st,c[3]):min(st,c[2]);mae=min(mae,2*s*(adverse-o)-cost);}
     if(h.reason){ref=h.price;reason=h.reason;both=h.both;break;}
     if(j==(int)b.size()-1){ref=c[4];reason=7;unknown=2;break;}
    }
    double gross=2*s*(ref-o),net=gross-cost,loss=2*s*(o-st)+cost;mae=min(mae,net);
    Row<NC> z={(double)k,(double)i,(double)e,(double)j,b[e][5],(double)f,(double)r,(double)sc,(double)s,(double)reason,(double)both,(double)unknown,o,st,tp,ref,net,gross,loss,mae,b[e][0],b[j][0]+(atopen?0:60)};
    ostringstream line;line.precision(15);line<<out.size();for(auto v:z)line<<','<<v;line<<'\n';csv.put(line.str());out.push_back(z);
   }
  }
 }
 ofstream bf(dir+"/outcomes.bin",ios::binary);bf.write((char*)out.data(),out.size()*sizeof(Row<NC>));csv.close();cout<<"outcomes "<<out.size()<<endl;
}
const string AH="config_id,path_id,bootstrap,status,passed,payout,pass_sessions,pass_calendar_days,active_eval_days,active_funded_days,total_sessions,total_calendar_days,eval_trades,funded_trades,eval_dll_days,funded_dll_days,eval_mll,funded_mll,eval_inactive,funded_inactive,eval_timeout,funded_timeout,censored,data_unresolved,cash,final_equity,max_drawdown,eval_final_equity,funded_final_equity,qualifying_funded_days\n";
const string EH="config_id,path_id,step,phase,outcome_id,quantity\n";
struct Account{double eq=0,floor=-1000,peak=0,maxdd=0,best=0,evaleq=0;int phase=0,lastActivity=0,phaseSessions=0,winDays=0,evalTrades=0,fundTrades=0,adE=0,adF=0,dllE=0,dllF=0,passStep=0,passCal=0,status=0,elapsed=0,used=0;double cash=0;};
// A single normalized event contains a full join key; outcomes supply all prices/cash.
void lifecycle(string dir,int scenario,int limit=0,bool audit=true){auto o=readbin<Row<NC>>(dir+"/outcomes.bin");auto days=readbin<array<int,2>>(dir+"/days.bin");auto paths=readbin<array<int,120>>(dir+"/paths.bin");int nchrono=days.size()-2,nd=days.size();
 vector<vector<vector<int>>> index(12,vector<vector<int>>(nd));for(int k=0;k<(int)o.size();k++)if(o[k][FAMILY]<2&&o[k][SC]==scenario)index[(int)o[k][FAMILY]*6+(int)o[k][RRID]][o[k][DAY]].push_back(k);
 GZ accounts(dir+"/accounts_sc"+to_string(scenario)+".csv.gz",AH);GZ* events=nullptr;long long total=0;int part=0;auto emit=[&](int cfg,int pid,int step,int phase,int oid,int q){if(!audit)return;if(total%4000000==0){if(events){events->close();delete events;}char name[200];snprintf(name,sizeof(name),"/events_sc%d_part%03d.csv.gz",scenario,part++);events=new GZ(dir+name,EH);}char s[150];int n=snprintf(s,sizeof(s),"%d,%d,%d,%d,%d,%d\n",cfg,pid,step,phase,oid,q);events->put(string(s,n));total++;};
 for(int f=0;f<2;f++)for(int rr=0;rr<6;rr++)for(int riskid=0;riskid<6;riskid++)for(int pol=0;pol<3;pol++){
 int cfg=((((f*6+rr)*4+scenario)*6+riskid)*3+pol);
 for(int pid=0;pid<(int)paths.size()&&(!limit||pid<limit);pid++){
  Account a;bool mc=pid>=nchrono;int previous=-1;
  for(int step=0;step<120;step++){
   int day=paths[pid][step];if(day<0){a.status=8;break;}
   if(step){int gap= (!mc || day==previous+1) ? days[day][0]-days[previous][0] : day>0?days[day][0]-days[day-1][0]:1;a.elapsed+=max(1,gap);}previous=day;
   if(a.phase==1&&a.phaseSessions==0)a.lastActivity=a.elapsed;
   if(a.elapsed-a.lastActivity>=30){a.status=a.phase==0?2:5;break;}
   a.used++;a.phaseSessions++;double start=a.eq;bool locked=false,traded=false;int busy=-1;
   for(int oid:index[f*6+rr][day]){
    auto z=o[oid];if(locked||z[SIGNAL]<busy)continue;
    double risk=a.phase==0?RISK[riskid]:min(200.,RISK[riskid]);int cap=a.phase==0?20:(start>=1000?20:10);int q=sizeq(risk,600+(a.eq-start),a.eq-a.floor,z[LOSS],cap);if(q<1)continue;
    assert(q<=cap&&q*z[LOSS]<=risk+1e-7&&q*z[LOSS]<=a.eq-a.floor-25+1e-7);
    emit(cfg,pid,step,a.phase,oid,q);traded=true;if(a.phase==0)a.evalTrades++;else a.fundTrades++;
    if(z[UNKNOWN]){a.status=z[UNKNOWN]==2?8:9;break;}
    double low=a.eq+q*z[MAE],net=q*z[NET];a.maxdd=max(a.maxdd,a.peak-low);
    bool dll=low<=start-600+1e-9,mll=low<=a.floor+1e-9;
    // Only gap overshoots can cross a rule threshold: sizing reserves USD25.
    if(dll){if(a.phase==0)a.dllE++;else a.dllF++;locked=true;}
    a.eq+=net;if(abs(net)>=1)a.lastActivity=a.elapsed;a.peak=max(a.peak,a.eq);busy=z[EXIT];
    if(mll){a.status=a.phase==0?1:4;break;}
    double daynet=a.eq-start;if(pol&& (daynet>=(pol==1?300:600)||daynet<=-300))locked=true;
    if(a.phase==0&&pass(a.eq,max(a.best,daynet)))locked=true;
    if(a.phase==1&&payout(a.eq,a.winDays+(daynet>=100)))locked=true;
   }
   if(traded){if(a.phase==0)a.adE++;else a.adF++;}
   if(a.status)break;
   double daily=a.eq-start;a.best=max(a.best,daily);a.floor=floorEOD(a.floor,a.eq);
   if(a.phase==0&&pass(a.eq,a.best)){a.passStep=a.used;a.passCal=a.elapsed+1;a.evaleq=a.eq;a.phase=1;a.eq=0;a.floor=-1000;a.peak=0;a.best=0;a.phaseSessions=0;a.lastActivity=a.elapsed;continue;}
   if(a.phase==1){if(daily>=100)a.winDays++;double request=payout(a.eq,a.winDays);if(request){a.cash=.9*request;a.eq-=request;a.floor=100;a.status=7;break;}}
   if(a.phaseSessions>=60){a.status=a.phase==0?3:6;break;}
  }
  if(!a.status)a.status=8;
  if(a.phase==0)a.evaleq=a.eq;
  ostringstream line;line.precision(15);line<<cfg<<','<<pid<<','<<mc<<','<<a.status<<','<<(a.passStep>0)<<','<<(a.status==7)<<','<<a.passStep<<','<<a.passCal<<','<<a.adE<<','<<a.adF<<','<<a.used<<','<<a.elapsed+1<<','<<a.evalTrades<<','<<a.fundTrades<<','<<a.dllE<<','<<a.dllF<<','<<(a.status==1)<<','<<(a.status==4)<<','<<(a.status==2)<<','<<(a.status==5)<<','<<(a.status==3)<<','<<(a.status==6)<<','<<(a.status==8)<<','<<(a.status==9)<<','<<a.cash<<','<<a.eq<<','<<a.maxdd<<','<<a.evaleq<<','<<(a.phase?a.eq:0)<<','<<a.winDays<<'\n';accounts.put(line.str());
 }
 }
 accounts.close();if(events){events->close();delete events;}ofstream m(dir+"/events_sc"+to_string(scenario)+"_count.txt");m<<total<<'\n';cout<<dir<<" scenario "<<scenario<<" events "<<total<<endl;
}
void selftest(){assert(hit(1,99,101,100,102,98,true).reason==3);assert(hit(1,99,101,98,102,97,true).price==98);assert(hit(-1,101,99,100,102,98,true).reason==3);assert(hit(1,99,101,100,101.1,100,true).reason==0);assert(hit(1,99,101,100,102,100,false).reason==0);assert(sizeq(575,600,1000,30,20)==19);assert(sizeq(200,20,1000,10,20)==0);assert(floorEOD(-1000,1200)==100);assert(floorEOD(100,0)==100);assert(!pass(1250,700));assert(pass(1300,650));assert(payout(1000,5)==500);assert(payout(999,5)==0);assert(payout(2500,5)==1000);assert(payout(1000,4)==0);cout<<"15 deterministic primitive checks PASS\n";}
int main(int argc,char**argv){try{if(argc<2)return 1;string mode=argv[1];if(mode=="test")selftest();else if(mode=="outcomes")outcomes(argv[2]);else if(mode=="accounts")lifecycle(argv[2],atoi(argv[3]),argc>4?atoi(argv[4]):0,argc<=5||string(argv[5])!="noaudit");else return 2;return 0;}catch(exception&e){cerr<<e.what()<<endl;return 3;}}
