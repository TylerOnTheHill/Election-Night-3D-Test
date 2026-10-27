(()=>{'use strict';
const $=id=>document.getElementById(id),fmt=n=>Number(n).toLocaleString('en-US'),clean=s=>String(s||'').toUpperCase().replace(/[^A-Z]/g,'');
let rows=[],statePct=0,stateBallots=0,stateRegistered=0,selected='',sortKey='cumulative_total',sortAsc=false;
const title=s=>s.toLowerCase().replace(/\\b\\w/g,c=>c.toUpperCase());
function showDetail(name){
 const row=rows.find(r=>clean(r.county)===clean(name));
 selected=row?clean(row.county):'';
 $('ev-detail-name').textContent=row?title(row.county)+' County':'Texas';
 $('ev-detail-ballots').textContent=fmt(row?row.cumulative_total:stateBallots);
 $('ev-state-pct').textContent=(row?Number(row.cumulative_early_voting_pct):statePct).toFixed(2)+'%';
 $('ev-registered').textContent=fmt(row?row.registered_voters:stateRegistered);
 $('ev-compare-row').hidden=!row;
 if(row){const diff=Number(row.cumulative_early_voting_pct)-statePct;$('ev-compare').textContent=(diff>=0?'+':'')+diff.toFixed(2)+' pp';}
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
 const lines=t.trim().split(/\\r?\\n/),keys=lines.shift().split(',');
 rows=lines.map(line=>Object.fromEntries(line.split(',').map((v,i)=>[keys[i],v])));
 stateBallots=rows.reduce((n,r)=>n+Number(r.cumulative_total),0);
 stateRegistered=rows.reduce((n,r)=>n+Number(r.registered_voters),0);
 if(rows.length!==254||stateBallots!==3724290||!stateRegistered)throw Error('County data did not reconcile');
 statePct=100*stateBallots/stateRegistered;
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