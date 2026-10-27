(()=>{'use strict';
const WATCH=[['AK','Alaska'],['AZ','Arizona'],['FL','Florida'],['GA','Georgia'],['IA','Iowa'],['KS','Kansas'],['ME','Maine'],['MI','Michigan'],['MN','Minnesota'],['MS','Mississippi'],['NE','Nebraska'],['NV','Nevada'],['NH','New Hampshire'],['NC','North Carolina'],['OH','Ohio'],['SC','South Carolina'],['TX','Texas'],['VA','Virginia'],['WI','Wisconsin']];
const EXTRA=new Set(['AZ','MN','MS']),$=id=>document.getElementById(id),fmt=n=>n==null?'—':Number(n).toLocaleString('en-US');
let data=[],checked='—',selectedCode='TX',visibleRows=[];
const safe=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function selectState(code){selectedCode=code;const x=data.find(v=>v.code===code);if(!x)return;for(const [id,value] of Object.entries({'detail-name':x.name+' · '+x.code,'detail-total':fmt(x.total),'detail-date':x.date||'Unavailable','detail-mail':fmt(x.mail),'detail-inperson':x.code==='NH'?'Not offered':fmt(x.inPerson),'detail-credit':x.sourceName||(x.code==='NH'?'NH absentee voting · count not available':'No verified statewide count'),'detail-description':x.code==='NH'?'No regular in-person early voting. Excuse-required absentee voting is available; no verified statewide absentee ballot total is in this feed. Missing is not zero.':x.reported?'Reported early ballots; not candidate votes.':'Missing does not mean zero.'}))$(id).textContent=value;const sum=(x.mail||0)+(x.inPerson||0),valid=x.mail!=null&&x.inPerson!=null&&sum>0;$('method-person').style.width=valid?100*x.inPerson/sum+'%':'0';$('method-mail').style.width=valid?100*x.mail/sum+'%':'0';$('method-note').textContent=valid?'In-person '+(100*x.inPerson/sum).toFixed(1)+'% · mail '+(100*x.mail/sum).toFixed(1)+'%':'Complete breakdown unavailable';const link=$('detail-source-link');link.hidden=!x.sourceUrl;if(x.sourceUrl)link.href=x.sourceUrl;else link.removeAttribute('href');
 $('detail-coverage-note').textContent=x.code==='NH'?'No regular in-person early voting; statewide absentee count unavailable.':!x.reported?'No verified statewide ballot count is available in this snapshot.':x.mail==null||x.inPerson==null?'Statewide total available; method breakdown incomplete.':'Statewide total and method breakdown supplied by the source; reporting cutoff may differ from other states.';
 document.querySelectorAll('#rows tr').forEach(tr=>{const active=tr.dataset.code===code;tr.classList.toggle('selected-row',active);if(active)tr.setAttribute('aria-selected','true');else tr.removeAttribute('aria-selected')});
 window.dispatchEvent(new CustomEvent('electionhq:battleground-select',{detail:{code}}));}
function render(){
 const q=$('search').value.trim().toLowerCase(),filter=$('filter').value,sort=$('sort').value;
 let rows=data.filter(x=>(x.name.toLowerCase().includes(q)||x.code.toLowerCase().includes(q))&&(filter==='all'||filter==='reported'&&x.reported||filter==='missing'&&!x.reported||filter==='added'&&EXTRA.has(x.code)));
 rows.sort((a,b)=>sort==='total'?(b.total??-1)-(a.total??-1)||a.name.localeCompare(b.name):sort==='date'?(b.date||'').localeCompare(a.date||'')||a.name.localeCompare(b.name):a.name.localeCompare(b.name));
 visibleRows=rows;
 $('rows').innerHTML=rows.length?rows.map(x=>'<tr data-code="'+safe(x.code)+'"'+(x.code===selectedCode?' class="selected-row" aria-selected="true"':'')+'><td><strong>'+safe(x.name)+'</strong> <span class="source">'+safe(x.code)+'</span></td><td><span class="pill'+(EXTRA.has(x.code)?' warn':'')+'">'+(EXTRA.has(x.code)?'Added':'VoteHub selection')+'</span></td><td class="num">'+fmt(x.total)+'</td><td class="num">'+fmt(x.mail)+'</td><td class="num">'+(x.code==='NH'?'Not offered':fmt(x.inPerson))+'</td><td>'+safe(x.date||'Not reported')+'</td><td>'+(x.sourceUrl?'<a href="'+safe(x.sourceUrl)+'" target="_blank" rel="noopener noreferrer">'+safe(x.sourceName||'Source')+'</a>':(x.code==='NH'?'<a href="https://www.nh.vote/mail" target="_blank" rel="noopener noreferrer">NH absentee voting rules</a>':'No current count'))+'</td></tr>').join(''):'<tr><td colspan="7">No matching states</td></tr>';
 document.querySelectorAll('#rows tr').forEach((tr,i)=>{tr.tabIndex=0;tr.addEventListener('click',e=>{if(e.target.closest('a'))return;selectState(rows[i].code)});tr.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();selectState(rows[i].code)}})});
 $('status').textContent='Showing '+rows.length+' of 19 selected states. Ballot figures are not adjusted to a common reporting date.';
}
async function load(){
 try{
  const r=await fetch('./data/early-vote/US.json',{cache:'no-store'});if(!r.ok)throw Error('National snapshot unavailable');
  const j=await r.json();if(!Array.isArray(j.states))throw Error('Invalid state list');
  const byCode=new Map(j.states.map(x=>[x.state,x]));
  data=WATCH.map(([code,name])=>{const s=byCode.get(code);return{code,name,reported:!!s&&Number.isFinite(s.total),total:s?.total??null,mail:s?.mail??null,inPerson:code==='NH'?null:s?.in_person??null,date:s?.counts_through??null,sourceName:s?.source_name??null,sourceUrl:s?.source_url??null};});
  checked=j.checked_at||'Unavailable';
  $('state-count').textContent=WATCH.length;
  $('reported-count').textContent=data.filter(x=>x.reported).length+' / '+WATCH.length;
  $('ballot-total').textContent=fmt(data.reduce((sum,x)=>sum+(x.total||0),0));
  $('feed-date').textContent=checked.slice(0,16).replace('T',' ')+' UTC';
  window.dispatchEvent(new CustomEvent('electionhq:battleground-data',{detail:{states:data}}));
  render();selectState(selectedCode);
 }catch(e){$('rows').innerHTML='<tr><td colspan="7">Early-vote snapshot unavailable. Please try again later.</td></tr>';$('status').textContent=e.message;console.warn('Battlegrounds:',e);}
}
function csvCell(value){
 const raw=value==null?'':String(value);
 const trimmed=raw.trimStart();
 const safeValue=trimmed.length&&'=+@-'.includes(trimmed[0])?"'"+raw:raw;
 return '"'+safeValue.replace(/"/g,'""')+'"';
}
function exportVisible(){
 const headers=['State','Code','Reported early ballots','Mail / absentee','Early in person','Reporting cutoff','Source','Source URL','Feed checked UTC','Coverage'];
 const records=visibleRows.map(x=>[x.name,x.code,x.total,x.mail,x.code==='NH'?'Not offered':x.inPerson,x.date,x.sourceName,x.sourceUrl,checked,x.reported?'Reported':'No verified statewide total']);
 const lineEnding=String.fromCharCode(13,10);
 const csv=String.fromCharCode(65279)+[headers,...records].map(row=>row.map(csvCell).join(',')).join(lineEnding)+lineEnding;
 const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));
 const link=document.createElement('a');link.href=url;link.download='electionhq-battleground-watchlist-2026.csv';document.body.append(link);link.click();link.remove();
 setTimeout(()=>URL.revokeObjectURL(url),1000);
}
$('export-watchlist').addEventListener('click',exportVisible);
['search','sort','filter'].forEach(id=>$(id).addEventListener(id==='search'?'input':'change',render));
window.addEventListener('electionhq:battleground-map-click',e=>selectState(e.detail.code));
load();
})();
