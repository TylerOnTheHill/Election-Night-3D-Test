(()=>{'use strict';
const $=id=>document.getElementById(id),fmt=n=>Number(n).toLocaleString('en-US'),clean=s=>String(s||'').toUpperCase().replace(/[^A-Z]/g,'');
let rows=[],statePct=0,stateBallots=0,stateRegistered=0,selected='',sortKey='cumulative_total',sortAsc=false;
const title=s=>s.toLowerCase().replace(/\b\w/g,c=>c.toUpperCase());
function showDetail(name){
 const row=rows.find(r=>clean(r.county)===clean(name));
 selected=row?clean(row.county):'';
 $('ev-detail-name').textContent=row?title(row.county)+' County':'Texas';
 $('ev-detail-ballots').textContent=fmt(row?row.cumulative_total:stateBallots);
 $('ev-state-pct').textContent=(row?Number(row.cumulative_early_voting_pct):statePct).toFixed(2)+'%';
 $('ev-registered').textContent=fmt(row?row.registered_voters:stateRegistered);
 $('ev-compare-row').hidden=!row;
 if(row){$('ev-compare').textContent='Unavailable';}
 $('ev-detail-source').textContent=row?'Official county snapshot · October 23, 2026':'Official Texas snapshot · October 23, 2026';
 document.querySelectorAll('#ev-county-body tr').forEach(tr=>tr.classList.toggle('ev-selected',clean(tr.dataset.county)===selected&&!!selected));
}
function render(){
 const q=clean($('ev-county-search').value);
 const match=rows.filter(r=>clean(r.county).includes(q)).sort((a,b)=>{
  const d=sortKey==='county'?a.county.localeCompare(b.county):Number(a[sortKey])-Number(b[sortKey]);
  return sortAsc?d:-d;
 });
 $('ev-county-body').innerHTML=match.length?match.map(r=>`<tr data-county="${r.county}" class="${clean(r.county)===selected?'ev-selected':''}"><td>${title(r.county)}</td><td>${fmt(r.registered_voters)}</td><td>${fmt(r.cumulative_total)}</td><td>${Number(r.cumulative_early_voting_pct).toFixed(2)}%</td><td>Official</td></tr>`).join(''):'<tr><td colspan="5">No matching counties</td></tr>';
}
fetch('./counties-2026-10-23.csv').then(r=>{if(!r.ok)throw Error('CSV unavailable');return r.text()}).then(t=>{
 const lines=t.trim().split(/\r?\n/),keys=lines.shift().split(',');
 rows=lines.map(line=>Object.fromEntries(line.split(',').map((v,i)=>[keys[i],v])));
 stateBallots=rows.reduce((n,r)=>n+Number(r.cumulative_total),0);
 stateRegistered=rows.reduce((n,r)=>n+Number(r.registered_voters),0);
 if(rows.length!==254||stateBallots!==3724290||!stateRegistered)throw Error('County data did not reconcile');
 statePct=100*stateBallots/stateRegistered;
 window.__electionhqCountyRows=rows;
 window.dispatchEvent(new Event('electionhq:texas-counties-ready'));
 $('ev-inperson').textContent=statePct.toFixed(2)+'%';
 $('ev-mail').textContent=fmt(stateRegistered);
 showDetail(null);render();
}).catch(e=>{$('ev-county-body').textContent='Unable to validate county data: '+e.message;});
$('ev-county-search').addEventListener('input',render);
document.querySelectorAll('.ev-sort').forEach(b=>b.addEventListener('click',()=>{if(sortKey===b.dataset.sort)sortAsc=!sortAsc;else{sortKey=b.dataset.sort;sortAsc=sortKey==='county';}render();}));
$('ev-county-body').addEventListener('click',e=>{const tr=e.target.closest('tr[data-county]');if(!tr)return;showDetail(tr.dataset.county);window.dispatchEvent(new CustomEvent('electionhq:select-county',{detail:{county:tr.dataset.county}}));});
window.addEventListener('electionhq:map-selection',e=>showDetail(e.detail&&e.detail.county));
document.querySelectorAll('.ev-mode').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('.ev-mode').forEach(x=>x.classList.toggle('selected',x===b));const m=b.dataset.evMode;$('ev-legend-title').textContent=m==='participation'?'Official early-vote participation · % of registered voters':'Party share unavailable · showing overall participation';$('ev-legend-description').textContent=m==='participation'?'Continuous 0–100% scale · enhanced low-range contrast':'No validated party figures; green overall participation retained';}));
})();

/* Contextual, sourced summary cards. National feed has state aggregates only. */
(()=>{
'use strict';
const stats=document.querySelector('.early-stats'),heading=document.querySelector('.early-heading strong');
if(!stats)return;
const cards=[...stats.querySelectorAll('.early-stat')];
const fmt=n=>n===null||n===undefined||!Number.isFinite(Number(n))?'Unavailable':Number(n).toLocaleString('en-US');
const set=(i,label,value,note)=>{const c=cards[i];c.querySelector('span').textContent=label;c.querySelector('b').textContent=value;c.querySelector('small').textContent=note;};
let feed=null,view='national',activeState='Texas',selected=null;
function render(){
 if(!document.body.classList.contains('early'))return;
 const name=view==='national'?selected:activeState;
 const state=feed?.states?.find(s=>s.state_name===name);
 const county=view==='state'&&activeState==='Texas'&&selected;
 const countyLabel=county?(window.__electionhqCountyRows?.find(r=>r.county.toLowerCase()===selected.toLowerCase())?.county||selected).toLowerCase().replace(/\b\w/g,c=>c.toUpperCase()):null;
 heading.textContent=county?countyLabel+' County · EARLY VOTE':name?name.toUpperCase()+' · EARLY VOTE':'NATIONAL EARLY VOTE DASHBOARD';
 if(county){
  // Existing official Texas county snapshot is authoritative for county values.
  const row=window.__electionhqCountyRows?.find(r=>r.county.toLowerCase()===selected.toLowerCase());
  if(row){
   set(0,'County early ballots',fmt(row.cumulative_total),'Texas official snapshot · October 23');
   set(1,'Registered voters',fmt(row.registered_voters),'Texas county registration');
   set(2,'County participation',Number(row.cumulative_early_voting_pct).toFixed(2)+'%','Ballots ÷ registered voters');
   set(3,'Reporting date','Oct 23, 2026','Verified Texas county snapshot');
   return;
  }
 }
 if(state){
  set(0,'Early ballots',fmt(state.total),'Reported through '+(state.counts_through||'date unavailable'));
  set(1,'Mail ballots',fmt(state.mail),'Source: '+(state.source_name||'Call the Map'));
  set(2,'In-person ballots',fmt(state.in_person),'Unavailable if not separately reported');
  set(3,'Vs 2022 · same stage',state.vs_2022_change||'Unavailable','Historical comparison where available');
  return;
 }
 if(name){
  set(0,'Early ballots','Unavailable','No verified state aggregate in national feed');
  set(1,'Mail ballots','Unavailable','No reported breakdown');
  set(2,'In-person ballots','Unavailable','No reported breakdown');
  set(3,'Vs 2022 · same stage','Unavailable','No validated comparison');
  return;
 }
 const national=feed?.national;
 set(0,'Nationwide early ballots',fmt(national?.total),'Sum of reporting states · dates vary');
 const allJurisdictions='AL AK AZ AR CA CO CT DC DE FL GA HI IA ID IL IN KS KY LA MA MD ME MI MN MO MS MT NC ND NE NH NJ NM NV NY OH OK OR PA RI SC SD TN TX UT VA VT WA WI WV WY'.split(' ');\n const reported=new Set((feed?.states||[]).map(s=>s.state));\n const missing=allJurisdictions.filter(code=>!reported.has(code));\n set(1,'Jurisdictions reporting',reported.size+' / 51',missing.length?'Not reported: '+missing.join(', ')+' · not zero':'All jurisdictions represented');
 set(2,'Reporting date range',national?.counts_through?.first&&national?.counts_through?.last?national.counts_through.first+' – '+national.counts_through.last:'Unavailable','State reporting dates vary');
 set(3,'Vs 2022 · matched states',national?.compared_with_2022?.change||'Unavailable','Only '+(national?.compared_with_2022?.states?.length||0)+' comparable states; not nationwide');
}
window.addEventListener('electionhq:geography-change',e=>{({view,activeState,selected}=e.detail);render();});
window.addEventListener('electionhq:national-early-loaded',()=>load());
window.addEventListener('electionhq:texas-counties-ready',render);
document.getElementById('tab-early')?.addEventListener('click',()=>setTimeout(render,0));
async function load(){try{const r=await fetch('./data/early-vote/US.json',{cache:'no-store'});if(!r.ok)throw Error('national feed unavailable');const j=await r.json();if(!Array.isArray(j.states)||!j.national)throw Error('invalid feed');feed=j;render();}catch(e){console.warn('Contextual early vote cards:',e);render();}}
load();
})();