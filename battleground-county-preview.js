(()=>{'use strict';
const $=id=>document.getElementById(id),fmt=n=>n.toLocaleString('en-US');
let preview=null,selected='TX',atlas=null,renderVersion=0;
function validate(p){
 if(p?.schema!=='electionhq-county-preview-v1'||p.publication_approved!==true)throw Error('County dataset is not approved for publication.');
 for(const [code,n,prefix] of [['TX',254,'48'],['NC',100,'37']]){
  const s=p.states?.[code],seen=new Set();
  if(!s||s.status!=='published'||s.counties?.length!==n)throw Error('Incomplete '+code+' published county coverage.');
  if(s.total_basis!=='sum_of_complete_county_reports'||!Number.isSafeInteger(s.total)||s.total<0||!s.statewide_cutoff||!s.provider||!s.credit)throw Error('Missing verified county total provenance: '+code);
  let sum=0;
  for(const r of s.counties){
   if(typeof r.name!=='string'||!r.name.trim()||typeof r.fips!=='string'||!new RegExp('^'+prefix+'[0-9]{3}$').test(r.fips)||seen.has(r.fips)||!Number.isSafeInteger(r.total)||r.total<0)throw Error('Invalid or duplicate '+code+' county observation.');
   seen.add(r.fips);sum+=r.total;
  }
  if(!Number.isSafeInteger(sum)||sum!==s.total)throw Error(code+' county aggregate mismatch.');
 }
 return p;
}
async function getAtlas(){
 if(atlas)return atlas;
 const r=await fetch('https://cdn.jsdelivr.net/npm/us-atlas@3/counties-10m.json');
 if(!r.ok)throw Error('County geography unavailable');
 atlas=await r.json();return atlas;
}
async function render(){
 const version=++renderVersion,code=selected;
 const host=$('battleground-county-preview'),status=$('county-preview-status');
 if(!preview)return;
 if(!preview.states[code]){host.hidden=true;status.textContent='County-level reporting is currently available for Texas and North Carolina. Select either state to explore.';return;}
 const s=preview.states[code];host.hidden=false;
 $('county-selected-detail').textContent='Select a county to see its reported early-ballot total.';
 status.textContent='County data available · '+(s.statewide_cutoff||'Reporting cutoff unavailable');
 $('county-preview-title').textContent=code==='TX'?'Texas counties':'North Carolina counties';
 $('county-preview-total').textContent='State total: '+fmt(s.total)+'*';
 const body=$('county-preview-rows');body.replaceChildren();
 for(const r of [...s.counties].sort((a,b)=>b.total-a.total)){
  const tr=document.createElement('tr');tr.tabIndex=0;tr.dataset.fips=r.fips;
  const name=document.createElement('td');name.textContent=r.name;
  const value=document.createElement('td');value.className='num';value.textContent=fmt(r.total);
  tr.append(name,value);body.append(tr);
  tr.addEventListener('click',()=>highlight(r.fips));
  tr.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();highlight(r.fips);}});
 }
 const map=$('county-preview-map'),legend=$('county-preview-legend');
 map.textContent='Loading county boundaries…';
 try{
  const geo=await getAtlas();if(version!==renderVersion)return;if(!window.d3||!window.topojson)throw Error('Map libraries unavailable');
  const shapes=topojson.feature(geo,geo.objects.counties).features.filter(f=>String(f.id).padStart(5,'0').startsWith(code==='TX'?'48':'37'));
  const lookup=new Map(s.counties.map(r=>[r.fips,r]));
  if(shapes.length!==s.counties.length||shapes.some(f=>!lookup.has(String(f.id).padStart(5,'0'))))throw Error('County boundary coverage mismatch; county table remains available.');
  const w=850,h=510,collection={type:'FeatureCollection',features:shapes};
  const projection=d3.geoMercator().fitExtent([[20,20],[w-20,h-20]],collection),path=d3.geoPath(projection),max=Math.max(1,...s.counties.map(r=>r.total));
  map.replaceChildren();
  const svg=d3.select(map).append('svg').attr('viewBox','0 0 '+w+' '+h).attr('role','img').attr('aria-label',$('county-preview-title').textContent+' reported early-ballot map');
  svg.selectAll('path').data(shapes).join('path').attr('d',path).attr('data-fips',f=>String(f.id).padStart(5,'0'))
   .attr('tabindex',0).attr('role','button')
   .attr('aria-label',f=>{const r=lookup.get(String(f.id).padStart(5,'0'));return r.name+', '+fmt(r.total)+' early ballots'})
   .attr('fill',f=>{const r=lookup.get(String(f.id).padStart(5,'0'));return d3.interpolateRgb('#15345d','#268cff')(0.15+0.85*Math.sqrt(r.total/max));})
   .on('click',(e,f)=>highlight(String(f.id).padStart(5,'0')))
   .on('keydown',(e,f)=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();highlight(String(f.id).padStart(5,'0'));}})
   .append('title').text(f=>{const r=lookup.get(String(f.id).padStart(5,'0'));return r.name+': '+fmt(r.total)+' ballots'});
  legend.textContent=s.counties.length+' counties · Brighter blue means more reported ballots, not partisan preference.';
 }catch(e){if(version!==renderVersion)return;map.textContent=e.message;legend.textContent='County totals remain available in the table.';}
}
function highlight(fips){
 const row=preview?.states?.[selected]?.counties?.find(r=>r.fips===fips);
 if(!row)return;
 $('county-selected-detail').textContent=row.name+' · '+fmt(row.total)+' reported early ballots';
 document.querySelectorAll('#county-preview-map path').forEach(p=>{const on=p.dataset.fips===fips;p.setAttribute('stroke',on?'#fff':'#273443');p.setAttribute('stroke-width',on?'2':'.4');});
 document.querySelectorAll('#county-preview-rows tr').forEach(tr=>{tr.classList.toggle('selected-row',tr.dataset.fips===fips);});
}
async function loadPublished(){
 try{
  const response=await fetch('./data/early-vote/battleground-counties.json',{cache:'no-store'});
  if(response.status===404){$('county-preview-status').textContent='County-level maps are being prepared. Statewide early-vote totals are available above.';return;}
  if(!response.ok)throw Error('County feed unavailable');
  preview=validate(await response.json());await render();
 }catch(e){preview=null;renderVersion++;$('battleground-county-preview').hidden=true;
  $('county-preview-status').textContent='County map temporarily unavailable; statewide reporting remains accessible.';
  console.warn('Battleground county data:',e.message);
 }
}
window.addEventListener('electionhq:battleground-select',e=>{selected=e.detail.code;if(preview)render();});
loadPublished();
})();