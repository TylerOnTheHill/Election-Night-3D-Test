(()=>{'use strict';
const WATCH=[['AK','Alaska'],['AZ','Arizona'],['FL','Florida'],['GA','Georgia'],['IA','Iowa'],['KS','Kansas'],['ME','Maine'],['MI','Michigan'],['MN','Minnesota'],['MS','Mississippi'],['NE','Nebraska'],['NV','Nevada'],['NH','New Hampshire'],['NC','North Carolina'],['OH','Ohio'],['SC','South Carolina'],['TX','Texas'],['VA','Virginia'],['WI','Wisconsin']];
const EXTRA=new Set(['AZ','MN','MS']),$=id=>document.getElementById(id),fmt=n=>n==null?'—':Number(n).toLocaleString('en-US');
let data=[],checked='—',selectedCode='TX';
const safe=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function selectState(code){selectedCode=code;const x=data.find(v=>v.code===code);if(!x)return;for(const [id,value] of Object.entries({'detail-name':x.name+' · '+x.code,'detail-total':fmt(x.total),'detail-date':x.date||'Unavailable','detail-mail':fmt(x.mail),'detail-inperson':fmt(x.inPerson),'detail-credit':x.sourceName||'No verified statewide count','detail-description':x.reported?'Reported early ballots; not candidate votes.':'Missing does not mean zero.'}))$(id).textContent=value;const sum=(x.mail||0)+(x.inPerson||0),valid=x.mail!=null&&x.inPerson!=null&&sum>0;$('method-person').style.width=valid?100*x.inPerson/sum+'%':'0';$('method-mail').style.width=valid?100*x.mail/sum+'%':'0';$('method-note').textContent=valid?'In-person '+(100*x.inPerson/sum).toFixed(1)+'% · mail '+(100*x.mail/sum).toFixed(1)+'%':'Complete breakdown unavailable';window.dispatchEvent(new CustomEvent('electionhq:battleground-select',{detail:{code}}));}
function render(){
 const q=$('search').value.trim().toLowerCase(),filter=$('filter').value,sort=$('sort').value;
 let rows=data.filter(x=>(x.name.toLowerCase().includes(q)||x.code.toLowerCase().includes(q))&&(filter==='all'||filter==='reported'&&x.reported||filter==='missing'&&!x.reported||filter==='added'&&EXTRA.has(x.code)));
 rows.sort((a,b)=>sort==='total'?(b.total??-1)-(a.total??-1)||a.name.localeCompare(b.name):sort==='date'?(b.date||'').localeCompare(a.date||'')||a.name.localeCompare(b.name):a.name.localeCompare(b.name));
 $('rows').innerHTML=rows.length?rows.map(x=>'<tr><td><strong>'+safe(x.name)+'</strong> <span class="source">'+safe(x.code)+'</span></td><td><span class="pill'+(EXTRA.has(x.code)?' warn':'')+'">'+(EXTRA.has(x.code)?'Added':'VoteHub selection')+'</span></td><td class="num">'+fmt(x.total)+'</td><td class="num">'+fmt(x.mail)+'</td><td class="num">'+fmt(x.inPerson)+'</td><td>'+safe(x.date||'Not reported')+'</td><td>'+(x.sourceUrl?'<a href="'+safe(x.sourceUrl)+'" target="_blank" rel="noopener noreferrer">'+safe(x.sourceName||'Source')+'</a>':'No current count')+'</td></tr>').join(''):'<tr><td colspan="7">No matching states</td></tr>';
 $('status').textContent='Showing '+rows.length+' of 19 selected states. Ballot figures are not adjusted to a common reporting date.';
}
async function load(){
 try{
  const r=await fetch('./data/early-vote/US.json',{cache:'no-store'});if(!r.ok)throw Error('National snapshot unavailable');
  const j=await r.json();if(!Array.isArray(j.states))throw Error('Invalid state list');
  const byCode=new Map(j.states.map(x=>[x.state,x]));
  data=WATCH.map(([code,name])=>{const s=byCode.get(code);return{code,name,reported:!!s&&Number.isFinite(s.total),total:s?.total??null,mail:s?.mail??null,inPerson:s?.in_person??null,date:s?.counts_through??null,sourceName:s?.source_name??null,sourceUrl:s?.source_url??null};});
  checked=j.checked_at||'Unavailable';
  $('state-count').textContent=WATCH.length;
  $('reported-count').textContent=data.filter(x=>x.reported).length+' / '+WATCH.length;
  $('ballot-total').textContent=fmt(data.reduce((sum,x)=>sum+(x.total||0),0));
  $('feed-date').textContent=checked.slice(0,16).replace('T',' ')+' UTC';
  render();selectState(selectedCode);
 }catch(e){$('rows').innerHTML='<tr><td colspan="7">Early-vote snapshot unavailable. Please try again later.</td></tr>';$('status').textContent=e.message;console.warn('Battlegrounds:',e);}
}
['search','sort','filter'].forEach(id=>$(id).addEventListener(id==='search'?'input':'change',render));
load();
})();
