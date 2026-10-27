(()=>{"use strict";
const $=id=>document.getElementById(id),ns="http://www.w3.org/2000/svg";
function validate(g){
 if(g?.type!=="FeatureCollection"||!Array.isArray(g.features)||!g.features.length||g.features.length>1000)throw Error("Expected nonempty precinct FeatureCollection (maximum 1,000 polygons).");
 const shapes=[],ids=new Set(),bounds=[Infinity,Infinity,-Infinity,-Infinity];
 let vertices=0;
 const addPoint=p=>{
  if(!Array.isArray(p)||p.length<2||!p.slice(0,2).every(x=>typeof x==="number"&&Number.isFinite(x)))throw Error("Invalid coordinate.");
  const [x,y]=p;if(x< -180||x>180||y< -90||y>90)throw Error("Not WGS84 coordinates.");
  bounds[0]=Math.min(bounds[0],x);bounds[1]=Math.min(bounds[1],y);
  bounds[2]=Math.max(bounds[2],x);bounds[3]=Math.max(bounds[3],y);
  if(++vertices>2000000)throw Error("Excessive polygon vertices.");
 };
 for(const f of g.features){
  const p=f.properties||{},id=p.area_id;
  if(p.county_fips!=="48085"||typeof id!=="string"||!id||ids.has(id))throw Error("Invalid or duplicate Collin precinct identifier.");
  ids.add(id);
  const geom=f.geometry||{},polys=geom.type==="Polygon"?[geom.coordinates]:geom.type==="MultiPolygon"?geom.coordinates:null;
  if(!Array.isArray(polys)||!polys.length)throw Error("Expected Polygon or MultiPolygon.");
  const rings=[];
  for(const poly of polys){
   if(!Array.isArray(poly)||!poly.length)throw Error("Empty polygon.");
   for(const ring of poly){
    if(!Array.isArray(ring)||ring.length<4)throw Error("Invalid polygon ring.");
    if(JSON.stringify(ring[0])!==JSON.stringify(ring[ring.length-1]))throw Error("Unclosed polygon ring.");
    ring.forEach(addPoint);rings.push(ring);
   }
  }
  shapes.push({id,rings});
 }
 if(bounds[0]<-98||bounds[2]>-95||bounds[1]<32||bounds[3]>35)throw Error("Coordinates outside expected Collin County region.");
 return {shapes,bounds,vertices};
}
$("render").addEventListener("click",async()=>{
 $("map-wrap").hidden=true;
 try{
  const f=$("geo").files[0];if(!f)throw Error("Choose a local GeoJSON file.");
  if(f.size>45e6)throw Error("File too large for local viewer.");
  const v=validate(JSON.parse(await f.text())),[minX,minY,maxX,maxY]=v.bounds;
  const scale=Math.min(950/Math.max(maxX-minX,1e-9),510/Math.max(maxY-minY,1e-9));
  const ox=(1000-(maxX-minX)*scale)/2,oy=(560-(maxY-minY)*scale)/2;
  const coord=p=>[(ox+(p[0]-minX)*scale).toFixed(2),(560-oy-(p[1]-minY)*scale).toFixed(2)];
  const svg=$("map");svg.replaceChildren();
  for(const shape of v.shapes){
   const path=document.createElementNS(ns,"path");
   path.setAttribute("d",shape.rings.map(r=>r.map((p,i)=>(i?"L":"M")+coord(p).join(",")).join(" ")+" Z").join(" "));
   path.setAttribute("fill-rule","evenodd");
   path.setAttribute("tabindex","0");path.setAttribute("role","button");path.setAttribute("aria-label","Precinct "+shape.id);
   const detail=()=>{$("details").textContent="Collin precinct "+shape.id+"\nGeometry only — TLC 2026 primary boundaries.\nNot certified for November 2026 general election. No turnout or candidate results."};
   path.addEventListener("click",detail);path.addEventListener("keydown",e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();detail()}});
   svg.append(path);
  }
  $("status").textContent=v.shapes.length+" Collin primary precinct polygons; "+v.vertices.toLocaleString()+" vertices. Staging only; not November-general verified.";
  $("details").textContent="Select a precinct to inspect its identifier. No turnout data loaded.";
  $("map-wrap").hidden=false;
 }catch(e){$("status").textContent="Boundary preview blocked: "+e.message}
});
})();