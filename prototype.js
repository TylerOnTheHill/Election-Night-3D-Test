import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
const $=id=>document.getElementById(id), stage=$('stage'), load=$('loading'), mode=$('mode'), detail=$('details'), search=$('search'), suggestions=$('suggestions'), zoom=$('zoom'), zoomLabel=$('zoom-label');
const renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.outputColorSpace=THREE.SRGBColorSpace;stage.prepend(renderer.domElement);
const scene=new THREE.Scene(), camera=new THREE.PerspectiveCamera(38,1,.1,500);camera.up.set(0,0,1);camera.position.set(0,-38,45);const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=.055;controls.mouseButtons={LEFT:THREE.MOUSE.PAN,MIDDLE:THREE.MOUSE.DOLLY,RIGHT:THREE.MOUSE.ROTATE};controls.rotateSpeed=.19;controls.zoomSpeed=.72;controls.panSpeed=.6;controls.minDistance=.65;controls.maxDistance=70;controls.minPolarAngle=.16;controls.maxPolarAngle=.94;controls.target.set(0,0,0);
scene.add(new THREE.HemisphereLight(0xe2e2e2,0x151515,1.65));const sun=new THREE.DirectionalLight(0xffffff,1.9);sun.position.set(-16,20,36);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);sun.shadow.camera.left=-38;sun.shadow.camera.right=38;sun.shadow.camera.top=38;sun.shadow.camera.bottom=-38;sun.shadow.bias=-.0006;scene.add(sun);
const rim=new THREE.DirectionalLight(0xd4d6da,.55);rim.position.set(18,-10,16);scene.add(rim);
// Floating sculpture: no ground plane or grid.
let projectionRegion='';let group=new THREE.Group();scene.add(group);let meshes=[], selected=null, rows=new Map(), activeState='Texas', activeStateFips='48', view='state', projection={lon:-99.5,lat:31,sx:.85,sy:1.05}, stateFeatures=null, countyFeatures=null, stateMap=new Map(), regionNames=[];const raycaster=new THREE.Raycaster(), pointer=new THREE.Vector2();const ease=()=>matchMedia('(prefers-reduced-motion: reduce)').matches?1:.14;
function clean(x){return String(x||'').trim().toUpperCase()}function number(x){return Number(x).toLocaleString('en-US')}
function polygonToShape(rings){const outer=rings[0];if(!outer||outer.length<4)return null;const shape=new THREE.Shape();outer.forEach((p,i)=>i?shape.lineTo(...project(p)):shape.moveTo(...project(p)));for(const hole of rings.slice(1)){if(hole.length<4)continue;const path=new THREE.Path();hole.forEach((p,i)=>i?path.lineTo(...project(p)):path.moveTo(...project(p)));shape.holes.push(path)}return shape}
function project(p){
 if(view==='national'){
  // Transform whole state consistently, including Aleutian islands crossing the date line.
  if(projectionRegion==='Alaska'){
   const lon=p[0]>0?p[0]-360:p[0];
   return [(lon+153)*.26-18,(p[1]-64)*.26-11];
  }
  if(projectionRegion==='Hawaii')return [(p[0]+157)*.62-4,(p[1]-20.5)*.62-13.3];
  return [(p[0]+98)*.62,(p[1]-38)*.76];
 }
 return [(p[0]-projection.lon)*projection.sx,(p[1]-projection.lat)*projection.sy];
}
function eachPoly(feature,fn){const g=feature.geometry;if(!g)return;if(g.type==='Polygon')fn(g.coordinates);else if(g.type==='MultiPolygon')g.coordinates.forEach(fn)}
function makeRegion(feature,name){projectionRegion=name;const shapes=[];eachPoly(feature,rings=>{const s=polygonToShape(rings);if(s)shapes.push(s)});if(!shapes.length)return;const geom=new THREE.ExtrudeGeometry(shapes,{depth:.15,bevelEnabled:true,bevelSegments:1,steps:1,bevelSize:.018,bevelThickness:.018,curveSegments:1});const color='#35373c';const mesh=new THREE.Mesh(geom,[new THREE.MeshStandardMaterial({color,metalness:.25,roughness:.65,emissive:'#090909'}),new THREE.MeshStandardMaterial({color:'#232429',metalness:.2,roughness:.7})]);mesh.castShadow=true;mesh.receiveShadow=true;mesh.userData={name,baseColor:color,level:0,target:0,selected:false};group.add(mesh);meshes.push(mesh);const edges=new THREE.LineSegments(new THREE.EdgesGeometry(geom,24),new THREE.LineBasicMaterial({color:0x777a80,transparent:true,opacity:.48}));mesh.add(edges);mesh.userData.edges=edges;
// Keep a subtly illuminated footprint beneath the raised geographic piece.
const cavity=new THREE.Group();
const glow=new THREE.Mesh(new THREE.ShapeGeometry(shapes),new THREE.MeshBasicMaterial({color:0x7e848c,transparent:true,opacity:.22,depthWrite:false,side:THREE.DoubleSide}));glow.position.z=.024;cavity.add(glow);
for(const shape of shapes){const points=shape.getPoints(120);const path=new THREE.BufferGeometry().setFromPoints(points.map(v=>new THREE.Vector3(v.x,v.y,.052)));const line=new THREE.LineLoop(path,new THREE.LineBasicMaterial({color:0xc5c8cc,transparent:true,opacity:.9,depthTest:true,depthWrite:false}));line.renderOrder=0;cavity.add(line);const halo=new THREE.LineLoop(path.clone(),new THREE.LineBasicMaterial({color:0x92969e,transparent:true,opacity:.32,depthTest:true,depthWrite:false}));halo.position.z=.012;halo.renderOrder=0;cavity.add(halo)}
cavity.visible=false;group.add(cavity);mesh.userData.cavity=cavity;
const sheenGeo=new THREE.ShapeGeometry(shapes);
const sheenMat=new THREE.ShaderMaterial({transparent:true,depthWrite:false,side:THREE.DoubleSide,uniforms:{uTime:{value:0},uMin:{value:0},uSpan:{value:1}},vertexShader:`varying vec2 vPos; void main(){vPos=position.xy;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`,fragmentShader:`uniform float uTime;uniform float uMin;uniform float uSpan;varying vec2 vPos;void main(){float progress=mod(uTime,6.2)/6.2;float pos=(vPos.x+vPos.y*.75-uMin)/max(uSpan,.01);float sweep=progress*1.4-.2;float band=exp(-pow((pos-sweep)/.075,2.0));float envelope=smoothstep(.0,.09,progress)*(1.0-smoothstep(.75,.83,progress));gl_FragColor=vec4(.93,.94,.97,band*.16*envelope);}`});
const sheen=new THREE.Mesh(sheenGeo,sheenMat);sheen.position.z=.172;sheen.visible=false;mesh.add(sheen);mesh.userData.sheen=sheen;
const box=new THREE.Box3().setFromObject(sheen),sz=box.getSize(new THREE.Vector3());sheenMat.uniforms.uMin.value=box.min.x+box.min.y*.75;sheenMat.uniforms.uSpan.value=Math.max(.1,sz.x+sz.y*.75);
}
const metalTop=new THREE.MeshPhysicalMaterial({color:0xaeb3bb,metalness:.55,roughness:.52,clearcoat:.15,clearcoatRoughness:.55,emissive:0x090909});
const metalSide=new THREE.MeshStandardMaterial({color:0x686c72,metalness:.5,roughness:.58});
function racePanel(level,name){
 const title=level==='national'?'United States':level==='state'?name:name+' County';
 const note=level==='national'?'Select a state to explore its counties and statewide races.':level==='state'?'The county map is ready. Select a county for county-specific details.':'Candidate results for this county have not been loaded.';
 return `<div class="sub">${level==='national'?'NATIONAL OVERVIEW':level==='state'?'STATEWIDE & FEDERAL RACES':'COUNTY RESULTS'}</div><h2>${title}</h2><p class="muted">${note}</p><div class="race-card"><strong>Major races</strong><p class="muted">U.S. Senate · Governor (where on ballot) · U.S. House · Other applicable statewide contests</p><p class="notice">No candidate returns are loaded in this prototype. Results and map colors will appear only when a verified election-results feed is connected.</p></div>`;
}
function setMapColor(){for(const mesh of meshes){if(!mesh.userData.selected)mesh.material[0].color.set('#35373c')}}
function choose(name,{focus=true}={}){
 if(view==='national'&&name){enterState(name);return;}
 if(selected===name)name=null;
 selected=name;search.value=name||'';suggestions.hidden=true;
 for(const mesh of meshes){
  const on=mesh.userData.name===name,old=mesh.userData.selected;
  mesh.userData.target=on?.76:0;mesh.userData.selected=on;
  if(on){mesh.material=[metalTop,metalSide];mesh.userData.cavity.visible=true;}
  else if(old){mesh.material=[new THREE.MeshStandardMaterial({color:mesh.userData.baseColor,metalness:.25,roughness:.65,emissive:'#090909'}),new THREE.MeshStandardMaterial({color:'#232429',metalness:.2,roughness:.7})];}
  mesh.userData.edges.material.color.set(on?'#d0d2d6':'#777a80');mesh.userData.edges.material.opacity=on?.9:.48;
  mesh.userData.sheen.visible=on;
 }
 if(name&&focus){const active=meshes.find(m=>m.userData.name===name);if(active)frameRegion(active)}
 if(!name){detail.innerHTML=racePanel(view==='national'?'national':'state',activeState);return}
 const row=activeState==='Texas'&&mode.value==='county'?rows.get(clean(name)):null;
 detail.innerHTML=row?`<button id="state-overview">← ${activeState} overview</button><div class="sub">TEXAS · OCT 23, 2026 · OFFICIAL SOS</div><h2>${name} County</h2><div class="metric">${number(row.cumulative_total)}</div><p class="muted">Cumulative early ballots · ${Number(row.cumulative_early_voting_pct).toFixed(2)}% of registered voters</p><div class="grid"><div class="cell"><small>Registered voters</small><strong>${number(row.registered_voters)}</strong></div><div class="cell"><small>In-person</small><strong>${number(row.cumulative_in_person)}</strong></div><div class="cell"><small>By mail</small><strong>${number(row.cumulative_mail)}</strong></div><div class="cell"><small>In-person Oct. 23</small><strong>${number(row.daily_in_person)}</strong></div></div><div class="race-card"><strong>Major election races</strong><p class="notice">Candidate returns are not yet connected. Early-voting figures are aggregate ballots, not votes for candidates.</p></div>`:`<button id="state-overview">← ${activeState} overview</button>${racePanel('county',name)}`;
 const back=$('state-overview');if(back)back.onclick=()=>choose(null,{focus:false});
}
function cameraView(overhead=false){focusTween=null;controls.enabled=true;camera.up.set(0,0,1);controls.target.set(0,view==='national'?-1:1.6,0);camera.position.set(0,view==='national'?(overhead?-.001:-12):(overhead?-.001:-10),view==='national'?(overhead?46:43):(overhead?22:19));controls.update();controls.saveState()}
function animateCamera(toTarget,toCamera,duration=700){focusTween={start:performance.now(),duration,fromCamera:camera.position.clone(),fromTarget:controls.target.clone(),toTarget,toCamera};}
function frameRegion(mesh){
 const bounds=new THREE.Box3().setFromObject(mesh);
 const center=bounds.getCenter(new THREE.Vector3());
 const size=bounds.getSize(new THREE.Vector3());
 const span=Math.max(size.x,size.y,.25);
 // A deliberately contextual view: no extreme close-ups on small counties.
 // County widths vary dramatically, so cap both ends of the framing distance.
 const distance=THREE.MathUtils.clamp(7.2+span*1.5,8,24);
 const target=new THREE.Vector3(center.x,center.y,0);
 const direction=new THREE.Vector3(0,-.72,1.18).normalize();
 animateCamera(target,target.clone().addScaledVector(direction,distance),850);
}
$('reset').onclick=()=>cameraView(false);$('top').onclick=()=>cameraView(true);$('angle').onclick=()=>cameraView(false);$('home').onclick=()=>{choose(null,{focus:false});cameraView(false)};$('national').onclick=()=>showNational();
let matches=[];
function updateSuggestions(){const q=search.value.trim().toLowerCase();matches=q?regionNames.filter(n=>n&&n.toLowerCase().includes(q)).slice(0,12):[];suggestions.replaceChildren();for(const name of matches){const b=document.createElement('button');b.type='button';b.textContent=name;b.onclick=()=>{choose(name);suggestions.hidden=true};suggestions.append(b)}suggestions.hidden=!matches.length;}
search.addEventListener('input',updateSuggestions);
search.addEventListener('keydown',e=>{if(e.key==='Enter'&&matches.length){e.preventDefault();choose(matches[0]);suggestions.hidden=true}if(e.key==='Escape'){choose(null,{focus:false});suggestions.hidden=true}});document.addEventListener('keydown',e=>{if(e.key==='Escape'&&document.activeElement!==search)choose(null,{focus:false});if(e.key==='/'&&document.activeElement!==search){e.preventDefault();search.focus()}});
search.addEventListener('blur',()=>setTimeout(()=>suggestions.hidden=true,180));
function setZoom(value){const distance=THREE.MathUtils.lerp(38,1.5,Number(value)/100);const dir=camera.position.clone().sub(controls.target).normalize();animateCamera(controls.target.clone(),controls.target.clone().addScaledVector(dir,distance),280)}
zoom.addEventListener('input',()=>setZoom(zoom.value));
$('zoom-in').onclick=()=>setZoom(Math.min(100,Number(zoom.value)+8));
$('zoom-out').onclick=()=>setZoom(Math.max(0,Number(zoom.value)-8));
const countyURL='https://cdn.jsdelivr.net/gh/plotly/datasets@master/geojson-counties-fips.json';
const statesURL='https://cdn.jsdelivr.net/gh/PublicaMundi/MappingAPI@master/data/geojson/us-states.json';
const census='https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer';
const statesList=['Alabama','Alaska','Arizona','Arkansas','California','Colorado','Connecticut','Delaware','Florida','Georgia','Hawaii','Idaho','Illinois','Indiana','Iowa','Kansas','Kentucky','Louisiana','Maine','Maryland','Massachusetts','Michigan','Minnesota','Mississippi','Missouri','Montana','Nebraska','Nevada','New Hampshire','New Jersey','New Mexico','New York','North Carolina','North Dakota','Ohio','Oklahoma','Oregon','Pennsylvania','Rhode Island','South Carolina','South Dakota','Tennessee','Texas','Utah','Vermont','Virginia','Washington','West Virginia','Wisconsin','Wyoming'];
const fipsList=['01','02','04','05','06','08','09','10','12','13','15','16','17','18','19','20','21','22','23','24','25','26','27','28','29','30','31','32','33','34','35','36','37','38','39','40','41','42','44','45','46','47','48','49','50','51','53','54','55','56'];
const stateFips=new Map(statesList.map((n,i)=>[n,fipsList[i]]));
async function json(url){const r=await fetch(url);if(!r.ok)throw Error(`HTTP ${r.status}`);return r.json()}
async function districtFeatures(){const meta=await json(census+'?f=pjson');const lyr=(meta.layers||[]).find(l=>/119th Congress|119th Congressional|Congressional Districts.*119/i.test(l.name));if(!lyr)throw Error('119th congressional layer not found');const info=await json(`${census}/${lyr.id}?f=pjson`);const sf=info.fields.find(f=>/^(STATE|STATEFP|STATEFP20|STATEFP25)$/i.test(f.name));const df=info.fields.find(f=>/^(CD119|CDFP|CD|DISTRICT)$/i.test(f.name));if(!sf||!df)throw Error('Missing geographic identifiers');const params=new URLSearchParams({where:`${sf.name}='48'`,outFields:'*',outSR:'4326',returnGeometry:'true',f:'geojson'});const data=await json(`${census}/${lyr.id}/query?${params}`);return data.features.map(f=>({feature:f,name:`TX-${String(f.properties[df.name]).padStart(2,'0')}`}))}
function stateProjection(name){const feat=stateMap.get(name);if(!feat)return;const pts=[];eachPoly(feat,rings=>rings[0].forEach(p=>pts.push(p)));if(!pts.length)return;const xs=pts.map(p=>p[0]),ys=pts.map(p=>p[1]);const lon=(Math.min(...xs)+Math.max(...xs))/2,lat=(Math.min(...ys)+Math.max(...ys))/2;const spanX=Math.max(...xs)-Math.min(...xs),spanY=Math.max(...ys)-Math.min(...ys);const scale=Math.min(28/Math.max(spanX,1),20/Math.max(spanY,1),name==='Texas'?1.05:5);projection={lon,lat,sx:scale*Math.max(.35,Math.cos(lat*Math.PI/180)),sy:scale};if(name==='Texas')projection={lon:-99.5,lat:31,sx:.85,sy:1.05};}
function resetGroup(){scene.remove(group);group.traverse(o=>{if(o.geometry)o.geometry.dispose();if(o.material&&o.material!==metalTop&&o.material!==metalSide){(Array.isArray(o.material)?o.material:[o.material]).forEach(m=>m.dispose())}});group=new THREE.Group();scene.add(group);meshes=[];selected=null;}
function finishBuild(data){resetGroup();data.forEach(({feature,name})=>makeRegion(feature,name));regionNames=data.map(d=>d.name).sort((a,b)=>a.localeCompare(b,undefined,{numeric:true}));search.value='';suggestions.hidden=true;choose(null,{focus:false});cameraView(false);load.style.display='none';$('national').hidden=view==='national';$('state-name').textContent=view==='national'?'United States':activeState;$('mode-control').hidden=view==='national';$('race-select').value='all';}
async function showNational(){view='national';load.style.display='flex';load.textContent='Loading all 50 state outlines…';try{if(!stateFeatures){const raw=await json(statesURL);stateFeatures=raw.features.filter(f=>statesList.includes(f.properties.name));if(stateFeatures.length!==50)throw Error('Expected 50 states, found '+stateFeatures.length);stateMap=new Map(stateFeatures.map(f=>[f.properties.name,f]));}finishBuild(stateFeatures.map(feature=>({feature,name:feature.properties.name})));}catch(e){load.textContent='Unable to load national map: '+e.message;console.error(e)}}
async function enterState(name){activeState=name;activeStateFips=stateFips.get(name);view='state';mode.value='county';await show()}
async function show(){view='state';load.style.display='flex';load.textContent='Building '+activeState+' geography…';try{stateProjection(activeState);if(!countyFeatures){const raw=await json(countyURL);countyFeatures=raw.features;}const data=mode.value==='county'?countyFeatures.filter(f=>String(f.properties.STATE).padStart(2,'0')===activeStateFips).map(f=>({feature:f,name:clean(f.properties.NAME)})):activeState==='Texas'?await districtFeatures():[];if(!data.length)throw Error('No verified geometry available');if(activeState==='Texas'&&mode.value==='county'&&data.length!==254)throw Error('Incomplete Texas coverage: '+data.length);finishBuild(data);}catch(e){load.textContent='Unable to load complete boundaries: '+e.message;console.error(e)}}
mode.onchange=show;
// Double-click on a county zooms in; single click on a state immediately enters its counties.
let focusTween=null;
renderer.domElement.addEventListener('dblclick',e=>{
 if(view==='national')return;
 e.preventDefault();const rect=renderer.domElement.getBoundingClientRect();
 pointer.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);
 raycaster.setFromCamera(pointer,camera);const hits=raycaster.intersectObjects(meshes,false);
 const point=hits.length?hits[0].point.clone():controls.target.clone();
 const offset=camera.position.clone().sub(controls.target);const distance=offset.length();
 const nextDistance=Math.max(controls.minDistance,distance*.72);
 const newTarget=controls.target.clone().lerp(point,.62);
 animateCamera(newTarget,newTarget.clone().add(offset.normalize().multiplyScalar(nextDistance)),480);
});
function hitAt(e){const rect=renderer.domElement.getBoundingClientRect();pointer.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);raycaster.setFromCamera(pointer,camera);return raycaster.intersectObjects(meshes,false)[0]}
let down=null;renderer.domElement.addEventListener('pointerdown',e=>{down={x:e.clientX,y:e.clientY}});
renderer.domElement.addEventListener('pointerup',e=>{if(!down)return;const moved=Math.hypot(e.clientX-down.x,e.clientY-down.y)>5;down=null;if(moved||e.button!==0)return;const hit=hitAt(e);if(hit)choose(hit.object.userData.name)});
const hover=$('hover-info');let hoverName='';
renderer.domElement.addEventListener('pointermove',e=>{if(e.buttons){hover.hidden=true;return}const hit=hitAt(e);const name=hit?.object.userData.name||'';hoverName=name;if(!name){hover.hidden=true;renderer.domElement.style.cursor='grab';return}renderer.domElement.style.cursor='pointer';hover.hidden=false;hover.style.left=Math.min(e.offsetX+16,stage.clientWidth-215)+'px';hover.style.top=Math.max(8,e.offsetY-12)+'px';const row=view==='state'&&activeState==='Texas'&&mode.value==='county'?rows.get(clean(name)):null;hover.innerHTML=`<strong>${name}${view==='state'&&mode.value==='county'?' County':''}</strong><span>${row?'Early ballots: '+number(row.cumulative_total)+'<br>Early turnout: '+Number(row.cumulative_early_voting_pct).toFixed(2)+'%':'Election results not yet loaded'}</span>`;});
renderer.domElement.addEventListener('pointerleave',()=>hover.hidden=true);
$('race-select').addEventListener('change',()=>{const race=$('race-select').value;$('race-note').textContent=race==='all'?'All major applicable races in the panel · Map: awaiting verified results':`Map race: ${$('race-select').selectedOptions[0].text} · Awaiting verified results`;setMapColor()});
function resize(){const w=stage.clientWidth,h=stage.clientHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix()}new ResizeObserver(resize).observe(stage);resize();function tick(){requestAnimationFrame(tick);if(focusTween){controls.enabled=false;const t=Math.min(1,(performance.now()-focusTween.start)/focusTween.duration);const k=t*t*(3-2*t);camera.position.lerpVectors(focusTween.fromCamera,focusTween.toCamera,k);controls.target.lerpVectors(focusTween.fromTarget,focusTween.toTarget,k);if(t===1){focusTween=null;controls.enabled=true;}}for(const mesh of meshes){const t=mesh.userData.target;mesh.userData.level+=(t-mesh.userData.level)*ease();mesh.position.z=mesh.userData.level;if(!mesh.userData.selected&&mesh.userData.level<.025)mesh.userData.cavity.visible=false;}controls.update();const d=camera.position.distanceTo(controls.target);const z=Math.round(THREE.MathUtils.clamp((38-d)/36.5*100,0,100));if(document.activeElement!==zoom)zoom.value=z;zoomLabel.textContent=z+'%';for(const mesh of meshes){if(mesh.userData.sheen)mesh.userData.sheen.material.uniforms.uTime.value=performance.now()/1000;}renderer.render(scene,camera)}tick();
try{const r=await fetch('./counties-2026-10-23.csv');if(!r.ok)throw Error('County data missing');const lines=(await r.text()).trim().split(/\r?\n/),keys=lines.shift().split(',');for(const line of lines){const cells=line.split(',');const row=Object.fromEntries(keys.map((k,i)=>[k,cells[i]]));rows.set(clean(row.county),row)}if(rows.size!==254||[...rows.values()].reduce((n,r)=>n+Number(r.cumulative_total),0)!==3724290)throw Error('County dataset did not reconcile');await showNational()}catch(e){load.textContent='Unable to validate county data: '+e.message}
