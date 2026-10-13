(()=>{
'use strict';
const REPO='markusdieterberger-alt/Strategiutveckling-3',API='https://api.github.com/repos/'+REPO;
const dataState={lastSuccessful:null,lastGithub:null,status:null,github:null};
const el=(tag,cls,text)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e};
const add=(p,...children)=>{children.forEach(c=>p.appendChild(c));return p};
const safeHref=url=>/^https:\/\/(github\.com|docs\.google\.com|drive\.google\.com|api\.github\.com)\//.test(url||'')?url:'#';
const link=(text,url)=>{const a=el('a','cc-link',text);a.href=safeHref(url);a.target='_blank';a.rel='noopener noreferrer';return a};
const fmtTime=v=>{if(!v)return 'Ej synkat';const d=new Date(v);return isNaN(d.getTime())?'Okänt':d.toLocaleString('sv-SE',{dateStyle:'short',timeStyle:'short'})};
const updateText=(id,v)=>{const e=document.getElementById(id);if(e)e.textContent=v};
function buildShell(){
 const header=document.querySelector('header');const stamp=el('div','cc-live-stamp');stamp.id='cc-live-stamp';stamp.textContent='Läser projektdata…';header.appendChild(stamp);
 const nav=document.querySelector('nav');[['results','Resultat'],['activity','GitHub-aktivitet'],['sources','Källor']].forEach(([id,name])=>{const b=el('button','',name);b.dataset.tab=id;nav.appendChild(b)});
 const root=document.querySelector('.shell'),footer=root.querySelector('footer');
 const sResults=el('section');sResults.id='results';sResults.hidden=true;sResults.innerHTML='<div class="panel"><h2>Strategiernas dokumenterade resultat</h2><p class="sub">Resultat är inte jämförbara mellan olika perioder, riskmodeller eller exekveringsmotorer. Inget nedan är live-validerat.</p><div id="cc-results"></div></div><div class="panel"><h2>Python ↔ TradingView – valideringsläge</h2><div id="cc-validation"></div></div>';
 const sActivity=el('section');sActivity.id='activity';sActivity.hidden=true;sActivity.innerHTML='<div class="panel"><div class="cc-title-row"><h2>Senaste GitHub-aktiviteten</h2><button class="cc-refresh" id="cc-refresh" type="button">Uppdatera</button></div><p class="sub">Läses automatiskt från publika GitHub-API:t. Commit-historik är inte Work-progress.</p><div id="cc-activity-list" class="cc-feed">Laddar…</div></div><div class="panel"><h2>Öppna issues och pull requests</h2><div id="cc-issues-list" class="cc-feed">Laddar…</div></div>';
 const sSources=el('section');sSources.id='sources';sSources.hidden=true;sSources.innerHTML='<div class="panel"><h2>Projektets källor och dokument</h2><div id="cc-sources"></div></div><div class="panel"><h2>Synkronisering och integritet</h2><p class="sub">Den här öppna hubben läser <code>status.json</code> från GitHub Pages och offentlig repoaktivitet direkt från GitHub. Statusfilen behöver uppdateras när Work eller projektledaren fattar nya beslut. Automatisk Drive-synk eller läsning av Work-sessioners interna progress finns ännu inte. Privata Drive-dokument laddas aldrig in i sidan.</p><p class="sub" style="margin-top:12px">När sidan är öppen uppdateras källorna var femte minut. Ett versionsnummer visas för spårbarhet; inga strategiregler ändras automatiskt.</p></div>';
 root.insertBefore(sResults,footer);root.insertBefore(sActivity,footer);root.insertBefore(sSources,footer);
 nav.querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>{nav.querySelectorAll('button').forEach(x=>x.classList.toggle('active',x===b));root.querySelectorAll('section').forEach(s=>s.hidden=s.id!==b.dataset.tab)}));
 document.getElementById('cc-refresh').addEventListener('click',()=>refresh(true));
}
function strategyCard(s){
 const card=el('article','cc-result-card'),top=el('div','cc-title-row');
 add(top,el('h3','',s.name),el('span','status '+(s.status==='REVISE'?'warn':s.status==='VÄNTAR'?'wait':'hold'),s.status));
 card.appendChild(top);card.appendChild(el('p','sub',s.summary));card.appendChild(el('p','cc-stage','Steg: '+s.stage));
 const metrics=el('div','cc-metric-grid');(s.metrics||[]).forEach(m=>{const box=el('div','cc-metric');add(box,el('span','',m.label),el('strong','',m.value),el('small','',m.note));metrics.appendChild(box)});
 if(s.metrics?.length)card.appendChild(metrics);
 const links=el('div','cc-links');(s.links||[]).forEach((l)=>links.appendChild(link(l.title+' ↗',l.url)));card.appendChild(links);return card;
}
function renderStatus(d){
 dataState.status=d;
 updateText('cc-live-stamp','Statusfil: '+fmtTime(d.updated_at)+' · GitHub: '+(dataState.lastGithub?fmtTime(dataState.lastGithub):'hämtar…'));
 const results=document.getElementById('cc-results');results.replaceChildren(...d.strategies.map(strategyCard));
 const val=document.getElementById('cc-validation');val.replaceChildren();
 const bars=[['CT Scalper','EAB A/B/C: ej verifierad'],['HMA Midday','A/B: ej verifierad'],['AMT Micro Prime','Python PASS; TradingView väntar'],['XAC Recovery','Originalresultat ej reproducerat']];
 bars.forEach(([name,state])=>{const item=el('div','cc-validation-row');add(item,el('b','',name),el('span','',state));val.appendChild(item)});
 const sources=document.getElementById('cc-sources');sources.replaceChildren();
 const holder=el('div','cc-link-list');d.links.forEach(l=>holder.appendChild(link(l.title+' ↗',l.url)));sources.appendChild(holder);
 const research=el('div','cc-research');add(research,el('h3','','Forskningsrapportering'));
 d.research.forEach(r=>{const line=el('div','cc-validation-row');add(line,link(r.name+' ↗',r.url),el('span','',r.status+' · '+r.description));research.appendChild(line)});sources.appendChild(research);
 const decisions=document.querySelector('#overview .panel:nth-child(2)');if(decisions){const cards=decisions.querySelectorAll('.task');cards.forEach(x=>x.remove());d.decisions.forEach(v=>{const c=el('div','task');add(c,link(v.title+' ↗',v.url),el('p','',v.text));decisions.appendChild(c)})}
 const list=document.getElementById('all-strategies');if(list)list.replaceChildren(...d.strategies.map(s=>{const c=el('article','strategy');add(c,el('h3','',s.name),el('div','description',s.summary),el('div','meta',s.stage+' · '+s.status));return c}));
 updateText('cc-data-state','Senaste statusfil: '+fmtTime(d.updated_at));
}
const ghGet=async(path)=>{const r=await fetch(API+path,{headers:{'Accept':'application/vnd.github+json'}});if(!r.ok)throw Error('GitHub HTTP '+r.status);return r.json()};
function renderGithub(data){
 const container=document.getElementById('cc-activity-list');container.replaceChildren();
 const branches=[['main',data.main],['gh-pages',data.pages]];
 for(const [branch,commits] of branches){
  const heading=el('h3','',branch==='main'?'Strategikod (main)':'Webbplats (gh-pages)');container.appendChild(heading);
  if(!Array.isArray(commits)||!commits.length){container.appendChild(el('p','sub','Inga hämtade commits.'));continue}
  commits.slice(0,6).forEach(c=>{const box=el('div','cc-feed-item');const name=(c.commit?.message||'Commit').split('\n')[0];add(box,link(name,c.html_url),el('span','',fmtTime(c.commit?.committer?.date)+' · '+(c.sha||'').slice(0,7)));container.appendChild(box)})
 }
 const issues=document.getElementById('cc-issues-list');issues.replaceChildren();
 const items=(data.issues||[]).filter(i=>!i.pull_request).slice(0,10),prs=(data.prs||[]).slice(0,6);
 if(!items.length&&!prs.length)issues.appendChild(el('p','sub','Inga öppna issues eller pull requests hittades.'));
 [...items,...prs].forEach(i=>{const row=el('div','cc-feed-item');add(row,link('#'+i.number+' '+i.title,i.html_url),el('span','',i.pull_request?'Pull request':'Issue'));issues.appendChild(row)});
 dataState.lastGithub=new Date().toISOString();updateText('cc-live-stamp','Statusfil: '+fmtTime(dataState.status?.updated_at)+' · GitHub: '+fmtTime(dataState.lastGithub));
}
async function refresh(manual=false){
 const now=new Date().toISOString();if(manual)updateText('cc-live-stamp','Uppdaterar…');
 const a=await Promise.allSettled([
 fetch('./status.json?ts='+Date.now(),{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('Status HTTP '+r.status);return r.json()}),
 Promise.all([ghGet('/commits?sha=main&per_page=6'),ghGet('/commits?sha=gh-pages&per_page=6'),ghGet('/issues?state=open&per_page=15'),ghGet('/pulls?state=open&per_page=6')]).then(([main,pages,issues,prs])=>({main,pages,issues,prs}))
 ]);
 if(a[0].status==='fulfilled'){renderStatus(a[0].value);dataState.lastSuccessful=now}
 else{if(!dataState.status)updateText('cc-results','Statusfil kunde inte hämtas. Försök ladda om sidan.')}
 if(a[1].status==='fulfilled'){renderGithub(a[1].value);dataState.github=a[1].value}
 else{const c=document.getElementById('cc-activity-list');if(!dataState.github)c.textContent='GitHub-data tillfälligt otillgänglig (API-gräns eller nätverk).';updateText('cc-live-stamp','Statusfil: '+fmtTime(dataState.status?.updated_at)+' · GitHub: tillfälligt otillgänglig')}
 if(manual)updateText('cc-data-state','Manuell uppdatering: '+fmtTime(now));
}
buildShell();
const footer=document.querySelector('.footer');footer.prepend(el('div','cc-footnote','V2: automatiskt liveflöde från public GitHub, statusmanifest för beslut.'));footer.prepend(el('div','cc-footnote',''));
const line=el('div','cc-footnote','');line.id='cc-data-state';footer.prepend(line);
refresh();setInterval(()=>{if(!document.hidden)refresh()},5*60*1000);
})();