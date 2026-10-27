(()=>{'use strict';
const $=id=>document.getElementById(id),fmt=n=>n.toLocaleString('en-US');
const COUNTY_STATES={TX:{name:'Texas',fips:'48',count:254},NC:{name:'North Carolina',fips:'37',count:100},FL:{name:'Florida',fips:'12',count:67},VA:{name:'Virginia',fips:'51',count:133},IA:{name:'Iowa',fips:'19',count:99},WI:{name:'Wisconsin',fips:'55',count:72},SC:{name:'South Carolina',fips:'45',count:46}};
let preview=null,selected=new URLSearchParams(location.search).get('state')?.toUpperCase()||'TX',atlas=null,renderVersion=0;
function validate(p){
 if(p?.schema!=='electionhq-county-preview-v1'||p.publication_approved!==true)throw Error('County dataset is not approved for publication.');
 for(const [code,s] of Object.entries(p.states||{})){
  const config=COUNTY_STATES[code];if(!config)throw Error('Unsupported published county state: '+code);
  const n=config.count,prefix=config.fips,seen=new Set();
  if(s.status!=='published'||!Array.isArray(s.counties)||s.counties.length<1||s.counties.length>n)throw Error('Invalid '+code+' published county coverage.');
  if(s.total_basis!=='sum_of_reported_counties'||!Number.isSafeInteger(s.total)||s.total<0||(s.statewide_cutoff!=null&&(typeof s.statewide_cutoff!=='string'||!s.statewide_cutoff.trim()))||!s.provider||!s.credit)throw Error('Missing verified county total provenance: '+code);
  let sum=0;
  for(const r of s.counties){
   if(typeof r.name!=='string'||!r.name.trim()||typeof r.fips!=='string'||!new RegExp('^'+prefix+'[0-9]{3}$').test(r.fips)||seen.has(r.fips)||!Number.isSafeInteger(r.total)||r.total<0)throw Error('Invalid or duplicate '+code+' county observation.');
   seen.add(r.fips);sum+=r.total;
  }
  if(s.coverage_complete!==(s.counties.length===n)||s.geographic_count!==n)throw Error('Invalid reporting coverage: '+code);
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
 if(!preview.states[code]){window.electionhqCounty3dPayload=null;window.dispatchEvent(new Event('electionhq:county-3d-clear'));host.hidden=true;status.textContent='County-level ballot totals have not yet been published for '+(COUNTY_STATES[code]?.name||'this state')+'.';return;}
 const s=preview.states[code];host.hidden=false;
 $('county-selected-detail').textContent='Select a county to see its reported early-ballot total.';
 status.textContent=(s.coverage_complete?'Fully reported':'Partially reported')+' · '+s.counties.length+' of '+s.geographic_count+' counties · '+(s.statewide_cutoff||'Reporting cutoff unavailable');
 $('county-preview-title').textContent=COUNTY_STATES[code].name+' counties';
 $('county-preview-total').textContent='County ballots reported: '+fmt(s.total);
 // County observations are a geographic subset; never present their sum as a statewide total.
 $('county-preview-complete-note').hidden=!s.coverage_complete;
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
  const shapes=topojson.feature(geo,geo.objects.counties).features.filter(f=>String(f.id).padStart(5,'0').startsWith(COUNTY_STATES[code].fips));
  const lookup=new Map(s.counties.map(r=>[r.fips,r]));
  if(shapes.length!==s.geographic_count||s.counties.some(r=>!shapes.some(f=>String(f.id).padStart(5,'0')===r.fips)))throw Error('County boundary coverage mismatch; county table remains available.');
  const w=850,h=510,collection={type:'FeatureCollection',features:shapes};
  const projection=d3.geoMercator().fitExtent([[20,20],[w-20,h-20]],collection),path=d3.geoPath(projection),max=Math.max(1,...s.counties.map(r=>r.total));
  map.replaceChildren();
  const svg=d3.select(map).append('svg').attr('viewBox','0 0 '+w+' '+h).attr('role','img').attr('aria-label',$('county-preview-title').textContent+' reported early-ballot map');
  svg.selectAll('path').data(shapes).join('path').attr('d',path).attr('data-fips',f=>String(f.id).padStart(5,'0'))
   .attr('tabindex',0).attr('role','button')
   .attr('aria-label',f=>{const r=lookup.get(String(f.id).padStart(5,'0'));return r?r.name+', '+fmt(r.total)+' early ballots':'County not yet reported'})
   .attr('fill',f=>{const r=lookup.get(String(f.id).padStart(5,'0'));return r?d3.interpolateRgb('#15345d','#268cff')(0.15+0.85*Math.sqrt(r.total/max)):'#30343b';})
   .on('click',(e,f)=>highlight(String(f.id).padStart(5,'0')))
   .on('keydown',(e,f)=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();highlight(String(f.id).padStart(5,'0'));}})
   .append('title').text(f=>{const r=lookup.get(String(f.id).padStart(5,'0'));return r?r.name+': '+fmt(r.total)+' ballots':'Not yet reported'});
  window.electionhqCounty3dPayload={code,features:shapes,rows:s.counties};
  window.dispatchEvent(new CustomEvent('electionhq:county-3d-data',{detail:window.electionhqCounty3dPayload}));
  legend.textContent=s.counties.length+' of '+s.geographic_count+' counties reporting · Gray means not reported · Brighter blue means more reported ballots, not partisan preference.';
 }catch(e){if(version!==renderVersion)return;map.textContent=e.message;legend.textContent='County totals remain available in the table.';}
}
window.addEventListener('electionhq:county-map-select',e=>highlight(e.detail.fips));
function highlight(fips){
 const row=preview?.states?.[selected]?.counties?.find(r=>r.fips===fips);
 if(!row)return;
 window.dispatchEvent(new CustomEvent('electionhq:county-map-highlight',{detail:{fips}}));
 $('county-selected-detail').textContent=row.name+' · '+fmt(row.total)+' reported early ballots'+(row.file_as_of?' · As of '+row.file_as_of:' · County reporting cutoff unavailable');
 document.querySelectorAll('#county-preview-map path').forEach(p=>{const on=p.dataset.fips===fips;p.setAttribute('stroke',on?'#fff':'#273443');p.setAttribute('stroke-width',on?'2':'.4');});
 document.querySelectorAll('#county-preview-rows tr').forEach(tr=>{tr.classList.toggle('selected-row',tr.dataset.fips===fips);});
}
// Geometry-only fallback: display authentic county boundaries when publication is pending.
async function renderBoundariesOnly(){
 const version=++renderVersion,code=selected,host=$('battleground-county-preview'),status=$('county-preview-status');
 window.electionhqCounty3dPayload=null;window.dispatchEvent(new Event('electionhq:county-3d-clear'));
 if(!COUNTY_STATES[code]){host.hidden=true;status.textContent='County geography is not yet available for this state.';return;}
 host.hidden=false;
 $('county-preview-title').textContent=COUNTY_STATES[code].name+' county geography';
 $('county-preview-total').textContent='County totals awaiting publication';
 $('county-preview-complete-note').hidden=true;
 $('county-preview-rows').replaceChildren();
 $('county-selected-detail').textContent='County boundaries only. No county-level ballot totals are published in this view.';
 $('county-preview-legend').textContent='Neutral county boundaries · County reporting not yet published';
 status.textContent='County geography shown · Reported county totals not yet published';
 const map=$('county-preview-map');map.textContent='Loading county geography…';
 try{
  const geo=await getAtlas();if(version!==renderVersion)return;
  if(!window.topojson||!window.d3)throw Error('County geography libraries unavailable');
  const prefix=COUNTY_STATES[code].fips,count=COUNTY_STATES[code].count;
  const features=topojson.feature(geo,geo.objects.counties).features.filter(f=>String(f.id).padStart(5,'0').startsWith(prefix));
  if(features.length!==count)throw Error('County boundary coverage mismatch');
  const w=850,h=510,collection={type:'FeatureCollection',features};
  const projection=d3.geoMercator().fitExtent([[20,20],[w-20,h-20]],collection),path=d3.geoPath(projection);
  map.replaceChildren();
  const svg=d3.select(map).append('svg').attr('viewBox','0 0 '+w+' '+h).attr('role','img').attr('aria-label',$('county-preview-title').textContent+' (boundaries only)');
  svg.selectAll('path').data(features).join('path').attr('d',path).attr('fill','#414246').attr('stroke','#787a80').attr('stroke-width',.65)
    .append('title').text('County boundary · No published early-ballot total');
  window.electionhqCounty3dPayload={code,features,rows:[]};
  window.dispatchEvent(new CustomEvent('electionhq:county-3d-data',{detail:window.electionhqCounty3dPayload}));
 }catch(e){if(version!==renderVersion)return;map.textContent='County boundaries unavailable';console.warn('County geography fallback:',e.message);}
}
async function loadPublished(){
 try{
  const response=await fetch('./data/early-vote/battleground-counties.json',{cache:'no-store'});
  if(response.status===404){await renderBoundariesOnly();return;}
  if(!response.ok)throw Error('County feed unavailable');
  preview=validate(await response.json());await render();
 }catch(e){preview=null;renderVersion++;$('battleground-county-preview').hidden=true;
  window.electionhqCounty3dPayload=null;window.dispatchEvent(new Event('electionhq:county-3d-clear'));
  $('county-preview-status').textContent='County map temporarily unavailable; statewide reporting remains accessible.';
  console.warn('Battleground county data:',e.message);
 }
}
window.addEventListener('electionhq:battleground-select',e=>{selected=e.detail.code;if(preview)render();else renderBoundariesOnly();});
// Keep county geography synchronized with the visible state picker even if a separate state detail update is delayed.
document.getElementById('explorer-state')?.addEventListener('change',e=>{const code=e.target.value?.toUpperCase();if(code&&code!==selected){selected=code;if(preview)render();else renderBoundariesOnly();}});
loadPublished();
})();