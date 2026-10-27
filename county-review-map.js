(()=>{'use strict';
const host=document.getElementById('county-map'),legend=document.getElementById('county-map-legend');
if(!host)return;
let geography=null,latest=null,selectedFips=null;
async function load(){
 try{
  const response=await fetch('https://cdn.jsdelivr.net/npm/us-atlas@3/counties-10m.json');
  if(!response.ok)throw Error('County boundary service unavailable');
  const atlas=await response.json();
  if(!window.topojson||!window.d3)throw Error('Map rendering libraries unavailable');
  geography=topojson.feature(atlas,atlas.objects.counties).features;
  draw();
 }catch(e){host.textContent='County geography unavailable. The validated county table remains accessible.';legend.textContent=String(e.message);}
}
function draw(){
 if(!geography||!latest)return;
 const {code,rows}=latest;
 selectedFips=null;
 const lookup=new Map(rows.map(r=>[String(r.fips).padStart(5,'0'),r]));
 const prefix=code==='TX'?'48':'37';
 const shapes=geography.filter(f=>String(f.id).padStart(5,'0').startsWith(prefix));
 const matched=shapes.filter(f=>lookup.has(String(f.id).padStart(5,'0'))).length;
 if(shapes.length!==rows.length||matched!==rows.length){
  host.textContent='County geography did not match the validated FIPS roster. Map withheld; review the table instead.';
  legend.textContent=code+' · '+matched+' of '+rows.length+' FIPS matched; county map not rendered.';
  return;
 }
 const width=850,height=510;
 const max=Math.max(1,...rows.map(r=>r.total));
 const collection={type:'FeatureCollection',features:shapes};
 const projection=d3.geoMercator().fitExtent([[20,20],[width-20,height-20]],collection);
 const path=d3.geoPath(projection);
 host.replaceChildren();
 const svg=d3.select(host).append('svg').attr('viewBox','0 0 '+width+' '+height).attr('role','img').attr('aria-label',code+' county early-ballot volume map, staging only');
 svg.selectAll('path').data(shapes).join('path').attr('d',path)
  .attr('data-fips',f=>String(f.id).padStart(5,'0'))
  .attr('tabindex',f=>lookup.has(String(f.id).padStart(5,'0'))?0:null)
  .attr('role',f=>lookup.has(String(f.id).padStart(5,'0'))?'button':null)
  .attr('aria-label',f=>{const r=lookup.get(String(f.id).padStart(5,'0'));return r?r.name+', '+r.total.toLocaleString('en-US')+' early ballots':null})
  .on('click',(e,f)=>choose(f))
  .on('keydown',(e,f)=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose(f)}})
  .attr('fill',f=>{const r=lookup.get(String(f.id).padStart(5,'0'));return r&&Number.isFinite(r.total)?d3.interpolateRgb('#15345d','#268cff')(0.15+0.85*Math.sqrt(r.total/max)):'#222b36'})
  .append('title').text(f=>{const id=String(f.id).padStart(5,'0'),r=lookup.get(id);return r?r.name+': '+r.total.toLocaleString('en-US')+' reported early ballots':'County '+id+': no staged observation'});
 legend.textContent=code+' · '+matched+' of '+rows.length+' staged counties matched to boundary FIPS · darker blue = fewer reported ballots, brighter blue = more · staging only';
}
function choose(f){const fips=String(f.id).padStart(5,'0');if(!latest||!latest.rows.some(r=>r.fips===fips))return;window.dispatchEvent(new CustomEvent('electionhq:county-map-select',{detail:{fips}}))}
window.addEventListener('electionhq:county-table-select',e=>{selectedFips=e.detail.fips;d3.select(host).selectAll('path').attr('stroke',function(){return this.dataset.fips===selectedFips?'#ffffff':'#273443'}).attr('stroke-width',function(){return this.dataset.fips===selectedFips?2:0.4})});
window.addEventListener('electionhq:county-preview',e=>{latest=e.detail;draw()});
load();
})();
