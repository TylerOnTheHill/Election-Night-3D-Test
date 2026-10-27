(()=>{"use strict";
const $=id=>document.getElementById(id),ns="http://www.w3.org/2000/svg";
const point=p=>Array.isArray(p)&&p.length>=2&&p.slice(0,2).every(x=>typeof x==="number"&&Number.isFinite(x));
function rings(g){
 if(g.type==="Polygon")return g.coordinates;
 if(g.type==="MultiPolygon")return g.coordinates.flatMap(x=>x);
 throw Error("Only Polygon and MultiPolygon precinct boundaries are supported.");
}
function validate(d,g){
 if(d.schema!=="electionhq-local-returns-v1"||d.state!=="TX"||d.publication_approved!==false||d.coverage_complete===true||d.area_type!=="voting_precinct")throw Error("Unsupported or publication-approved local dataset.");
 if(!["ballots_cast","prior_primary_participation"].includes(d.metric_kind)||!d.file_as_of||!d.geometry_vintage||!/^https:\/\//.test(d.source_url||"")||!/^https:\/\//.test(d.geometry_source_url||""))throw Error("Missing required data provenance.");
 if(g.type!=="FeatureCollection"||!Array.isArray(g.features))throw Error("Invalid GeoJSON.");
 if(!Array.isArray(d.areas)||!d.areas.length||d.areas.length>20000||g.features.length>20000)throw Error("Invalid or excessive precinct count.");
 const data=new Map(),shapes=new Map();let sum=0;
 for(const a of d.areas){
  if(!/^48[0-9]{3}$/.test(a.county_fips)||typeof a.area_id!=="string"||!a.area_id||!Number.isSafeInteger(a.ballots_total)||a.ballots_total<0||a.candidate_dem_votes!=null||a.candidate_rep_votes!=null)throw Error("Invalid local-area record.");
  const key=a.county_fips+"|"+a.area_id;if(data.has(key))throw Error("Duplicate data key: "+key);
  data.set(key,a);sum+=a.ballots_total;
 }
 if(!Number.isSafeInteger(d.reported_area_total)||sum!==d.reported_area_total)throw Error("Reported subtotal does not reconcile.");
 const points=[];
 for(const f of g.features){
  const p=f.properties||{},county=String(p.county_fips??""),id=String(p.area_id??"");
  if(!/^48[0-9]{3}$/.test(county)||!id)throw Error("GeoJSON requires properties.county_fips and properties.area_id.");
  const key=county+"|"+id;if(shapes.has(key))throw Error("Duplicate geometry key: "+key);
  const rr=rings(f.geometry||{});if(!rr.length)throw Error("Empty precinct geometry.");
  for(const ring of rr){if(!Array.isArray(ring)||ring.length<4||!ring.every(point))throw Error("Invalid polygon ring.");points.push(...ring);}
  shapes.set(key,{feature:f,rings:rr});
 }
 const unmatched=[...data.keys()].filter(k=>!shapes.has(k));
 if(unmatched.length)throw Error(unmatched.length+" precinct counts lack matching geometry. Nothing rendered.");
 if(!points.length)throw Error("No valid coordinates.");
 return {data,shapes,points,extra:[...shapes.keys()].filter(k=>!data.has(k))};
}
$("render").addEventListener("click",async()=>{
 $("map-wrap").hidden=true;
 try{
  const df=$("data").files[0],gf=$("geo").files[0];if(!df||!gf)throw Error("Select both files.");
  if(df.size>8e6||gf.size>40e6)throw Error("Input exceeds local review size limit.");
  const d=JSON.parse(await df.text()),g=JSON.parse(await gf.text()),v=validate(d,g);
  const xs=v.points.map(p=>p[0]),ys=v.points.map(p=>p[1]),minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys);
  const scale=Math.min(950/Math.max(maxX-minX,1e-9),510/Math.max(maxY-minY,1e-9));
  const ox=(1000-(maxX-minX)*scale)/2,oy=(560-(maxY-minY)*scale)/2;
  const coord=p=>[(ox+(p[0]-minX)*scale).toFixed(2),(560-oy-(p[1]-minY)*scale).toFixed(2)];
  const svg=$("map");svg.replaceChildren();
  for(const [key,shape] of v.shapes){
   const path=document.createElementNS(ns,"path");
   path.setAttribute("d",shape.rings.map(r=>r.map((p,i)=>(i?"L":"M")+coord(p).join(",")).join(" ")+" Z").join(" "));
   path.setAttribute("fill-rule","evenodd");
   const row=v.data.get(key);
   path.setAttribute("aria-label",key+(row?" "+row.ballots_total+" ballots":" unavailable"));
   path.addEventListener("click",()=>$("details").textContent=key+"\n"+(row?row.ballots_total.toLocaleString()+" ballots":"No verified ballot total")+"\nCutoff: "+d.file_as_of+"\nSource: "+d.source_url+"\nNeutral geography only; not candidate votes.");
   svg.append(path);
  }
  $("status").textContent="Local staging join: "+v.data.size+" matched; "+v.extra.length+" additional polygons without data. Not approved for publication.";
  $("map-wrap").hidden=false;
 }catch(e){$("status").textContent="Preview blocked: "+e.message;}
});
})();