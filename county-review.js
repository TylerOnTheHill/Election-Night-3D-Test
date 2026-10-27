(()=>{"use strict";
const el=id=>document.getElementById(id),fmt=n=>n==null?"Unavailable":n.toLocaleString("en-US");
let data=null;
function validate(p){
 if(!p||p.schema!=="electionhq-county-preview-v1"||p.publication_approved!==false)throw Error("Not a staging-only county preview.");
 for(const [code,count,prefix] of [["TX",254,"48"],["NC",100,"37"]]){
  const s=p.states?.[code];
  if(!s||s.status!=="preview_only_not_approved_for_publication"||!Array.isArray(s.counties)||s.counties.length!==count)throw Error("Missing or incomplete "+code+" county coverage.");
  const seen=new Set(),sum=s.counties.reduce((n,r)=>{
   if(typeof r.fips!=="string"||!new RegExp("^"+prefix+"[0-9]{3}$").test(r.fips)||seen.has(r.fips)||!Number.isSafeInteger(r.total)||r.total<0)throw Error("Invalid or duplicate county FIPS/count.");
   seen.add(r.fips);return n+r.total;
  },0);
  if(sum!==s.total)throw Error(code+" county rows do not match their county-derived aggregate.");
 }
 return p;
}
function render(){
 const code=el("state").value,s=data.states[code],q=el("search").value.trim().toLowerCase();
 el("summary").textContent=code+" · "+s.county_count+" counties · "+fmt(s.total)+" early ballots";
 window.dispatchEvent(new CustomEvent("electionhq:county-preview",{detail:{code,rows:s.counties}}));
 const comparison=Number.isSafeInteger(s.provider_statewide_total)?" · Separate statewide headline: "+fmt(s.provider_statewide_total)+" (county difference: "+(s.total-s.provider_statewide_total>0?"+":"")+fmt(s.total-s.provider_statewide_total)+")":"";
 el("provenance").textContent="Displayed total: sum of "+s.county_count+" county reports · Provider: "+s.provider+" · Source cutoff: "+(s.statewide_cutoff||"Unavailable")+" · Checked: "+(s.provider_checked_at||"Unavailable")+" · Geography: "+s.census_geography_source+comparison;
 const body=el("rows");body.replaceChildren();
 for(const r of s.counties.filter(x=>x.name.toLowerCase().includes(q)||x.fips.includes(q)).sort((a,b)=>b.total-a.total)){
  const tr=document.createElement("tr");
  for(const [v,numeric] of [[r.name,false],[r.fips,false],[fmt(r.total),true],[fmt(r.mail),true],[fmt(r.in_person),true],[r.file_as_of||"Unavailable",false]]){
   const td=document.createElement("td");td.textContent=v;if(numeric)td.className="num";tr.append(td);
  }
  tr.title="Source: "+r.source_url+" · Credit: "+r.credit;
  tr.tabIndex=0;tr.setAttribute("aria-label","Select "+r.name+" county on the staging map");
  const select=()=>window.dispatchEvent(new CustomEvent("electionhq:county-table-select",{detail:{fips:r.fips}}));
  tr.addEventListener("click",select);
  tr.addEventListener("keydown",e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();select();}});
  body.append(tr);
 }
}
el("file").addEventListener("change",async e=>{
 data=null;el("results").hidden=true;
 try{
  const file=e.target.files?.[0];if(!file)return;
  if(file.size>4000000)throw Error("Preview file too large.");
  data=validate(JSON.parse(await file.text()));
  el("state").replaceChildren();
  for(const code of ["TX","NC"]){const o=document.createElement("option");o.value=code;o.textContent=code;el("state").append(o);}
  el("status").textContent="Staging preview loaded and validated locally. Nothing uploaded.";
  el("results").hidden=false;render();
 }catch(err){el("status").textContent="Cannot display: "+err.message;}
});
window.addEventListener("electionhq:county-map-select",e=>{if(!data)return;const r=data.states[el("state").value].counties.find(x=>x.fips===e.detail.fips);if(!r)return;el("search").value=r.name;render();window.dispatchEvent(new CustomEvent("electionhq:county-table-select",{detail:{fips:r.fips}}));el("rows").querySelector("tr")?.scrollIntoView({block:"nearest"});});
el("state").addEventListener("change",render);el("search").addEventListener("input",render);
})();