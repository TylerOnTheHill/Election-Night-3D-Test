(()=>{'use strict';
const host=document.getElementById('county-map'),legend=document.getElementById('county-map-legend');
if(!host)return;
let geography=null,latest=null;
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
 const lookup=new Map(rows.map(r=>[String(r.fips).padStart(5,'0'),r]));
 const prefix=code==='TX'?'48':'37';
 const shapes=geography.filter(f=>String(f.id).padStart(5,'0').startsWith(prefix));
 const width=850,height=510;
 const max=Math.max(1,...rows.map(r=>r.total));
 const collection={type:'FeatureCollection',features:shapes};
 const projection=d3.geoMercator().fitExtent([[20,20],[width-20,height-20]],collection);
 const path=d3.geoPath(projection);
 host.replaceChildren();
 const svg=d3.select(host).append('svg').attr('viewBox','0 0 '+width+' '+height).attr('role','img').attr('aria-label',code+' county early-ballot volume map, staging only');
 svg.selectAll('path').data(shapes).join('path').attr('d',path)
  .attr('fill',f=>{const r=lookup.get(String(f.id).padStart(5,'0'));return r&&Number.isFinite(r.total)?d3.interpolateRgb('#15345d','#268cff')(0.15+0.85*Math.sqrt(r.total/max)):'#222b36'})
  .append('title').text(f=>{const id=String(f.id).padStart(5,'0'),r=lookup.get(id);return r?r.name+': '+r.total.toLocaleString('en-US')+' reported early ballots':'County '+id+': no staged observation'});
 const matched=shapes.filter(f=>lookup.has(String(f.id).padStart(5,'0'))).length;
 legend.textContent=code+' · '+matched+' of '+rows.length+' staged counties matched to boundary FIPS · darker blue = fewer reported ballots, brighter blue = more · staging only';
}
window.addEventListener('electionhq:county-preview',e=>{latest=e.detail;draw()});
load();
})();
