import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
const $=id=>document.getElementById(id), stage=$('stage'), load=$('loading'), mode=$('mode'), detail=$('details'), search=$('search'), suggestions=$('suggestions'), zoom=$('zoom'), zoomLabel=$('zoom-label');
const renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.outputColorSpace=THREE.SRGBColorSpace;stage.prepend(renderer.domElement);
const scene=new THREE.Scene(), camera=new THREE.PerspectiveCamera(38,1,.1,500);camera.up.set(0,0,1);camera.position.set(0,-38,45);const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=.055;controls.mouseButtons={LEFT:THREE.MOUSE.PAN,MIDDLE:THREE.MOUSE.DOLLY,RIGHT:THREE.MOUSE.ROTATE};controls.rotateSpeed=.19;controls.zoomSpeed=.72;controls.panSpeed=.6;controls.minDistance=.65;controls.maxDistance=120;controls.minPolarAngle=.16;controls.maxPolarAngle=.94;controls.target.set(0,0,0);
scene.add(new THREE.HemisphereLight(0xd6e5ff,0x101e38,1.55));const sun=new THREE.DirectionalLight(0xffffff,2.25);sun.position.set(-16,20,36);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);sun.shadow.camera.left=-38;sun.shadow.camera.right=38;sun.shadow.camera.top=38;sun.shadow.camera.bottom=-38;sun.shadow.bias=-.0006;scene.add(sun);
const rim=new THREE.DirectionalLight(0x70a9ff,1.25);rim.position.set(18,-10,16);scene.add(rim);
// Floating sculpture: no ground plane or grid.
let projectionRegion='';let projectedGeometry=false;let trackerMode=document.body.classList.contains('early')?'early':'night';window.setTrackerMode=(v)=>{trackerMode=v;setMapColor();refreshPanel();updateFloatingPanel();};let demoMode=true;let backdropNames=new Set();let clickTimer=null;let transitionLock=false;let senateCalls={D:0,R:0};let houseCalls={D:0,R:0};let group=new THREE.Group();scene.add(group);let meshes=[], selected=null, rows=new Map(), activeState='Texas', activeStateFips='48', view='state', projection={lon:-99.5,lat:31,sx:.85,sy:1.05}, stateFeatures=null, projectedStates=null, countyFeatures=null, stateMap=new Map(), regionNames=[];const raycaster=new THREE.Raycaster(), pointer=new THREE.Vector2();const ease=()=>matchMedia('(prefers-reduced-motion: reduce)').matches?1:.14;
function clean(x){return String(x||'').trim().toUpperCase()}function number(x){return Number(x).toLocaleString('en-US')}
function polygonToShape(rings){const outer=rings[0];if(!outer||outer.length<4)return null;const shape=new THREE.Shape();outer.forEach((p,i)=>i?shape.lineTo(...project(p)):shape.moveTo(...project(p)));for(const hole of rings.slice(1)){if(hole.length<4)continue;const path=new THREE.Path();hole.forEach((p,i)=>i?path.lineTo(...project(p)):path.moveTo(...project(p)));shape.holes.push(path)}return shape}
function project(p){
 if(projectedGeometry)return [p[0],p[1]];
 if(view==='national'){
  // Transform whole state consistently, including Aleutian islands crossing the date line.
  if(projectionRegion==='Alaska'){
   const lon=p[0]>0?p[0]-360:p[0];
   // Mockup-style compact, upright Alaska inset. Longitude wraps across the date line.
   // The x and y scales are deliberately independent: the prior uniform scale
   // flattened Alaska into a long horizontal ribbon.
   return [(lon+153)*.132-12.8,(p[1]-64)*.235-12.15];
  }
  if(projectionRegion==='Hawaii')return [(p[0]+157)*.60-6.1,(p[1]-20.5)*.60-12.65];
  return [(p[0]+98)*.62,(p[1]-38)*.76];
 }
 return [(p[0]-projection.lon)*projection.sx,(p[1]-projection.lat)*projection.sy];
}
function eachPoly(feature,fn){const g=feature.geometry;if(!g)return;if(g.type==='Polygon')fn(g.coordinates);else if(g.type==='MultiPolygon')g.coordinates.forEach(fn)}
function makeRegion(feature,name){projectionRegion=name;projectedGeometry=!!feature.properties.projected;const shapes=[];eachPoly(feature,rings=>{const s=polygonToShape(rings);if(s)shapes.push(s)});if(!shapes.length)return;const isCounty=view==='state'&&!backdropNames.has(name);
const baseDepth=isCounty?.042:.30;
const geom=new THREE.ExtrudeGeometry(shapes,{depth:baseDepth,bevelEnabled:true,bevelSegments:2,steps:1,bevelSize:isCounty?.004:.028,bevelThickness:isCounty?.005:.038,curveSegments:1});const color='#35373c';const mesh=new THREE.Mesh(geom,[new THREE.MeshStandardMaterial({color,metalness:.28,roughness:.66,emissive:'#070b12'}),new THREE.MeshStandardMaterial({color:'#152a46',metalness:.56,roughness:.42})]);mesh.castShadow=true;mesh.receiveShadow=true;mesh.userData={name,baseColor:color,level:0,target:0,selected:false,isBackdrop:backdropNames.has(name),baseDepth};group.add(mesh);meshes.push(mesh);const edges=new THREE.LineSegments(new THREE.EdgesGeometry(geom,24),new THREE.LineBasicMaterial({color:0x777a80,transparent:true,opacity:.48}));mesh.add(edges);mesh.userData.edges=edges;edges.renderOrder=4;
// Keep a subtly illuminated footprint beneath the raised geographic piece.
const cavity=new THREE.Group();
const glow=new THREE.Mesh(new THREE.ShapeGeometry(shapes),new THREE.MeshBasicMaterial({color:0x7e848c,transparent:true,opacity:.22,depthWrite:false,side:THREE.DoubleSide}));glow.position.z=baseDepth*.47;cavity.add(glow);
for(const shape of shapes){const points=shape.getPoints(120);const path=new THREE.BufferGeometry().setFromPoints(points.map(v=>new THREE.Vector3(v.x,v.y,baseDepth*.53)));const line=new THREE.LineLoop(path,new THREE.LineBasicMaterial({color:0xc5c8cc,transparent:true,opacity:.9,depthTest:true,depthWrite:false}));line.renderOrder=0;cavity.add(line);const halo=new THREE.LineLoop(path.clone(),new THREE.LineBasicMaterial({color:0x92969e,transparent:true,opacity:.32,depthTest:true,depthWrite:false}));halo.position.z=.013;halo.renderOrder=0;cavity.add(halo)}
cavity.visible=false;group.add(cavity);mesh.userData.cavity=cavity;
const sheenGeo=new THREE.ShapeGeometry(shapes);
const sheenMat=new THREE.ShaderMaterial({transparent:true,depthWrite:false,side:THREE.DoubleSide,uniforms:{uTime:{value:0},uMin:{value:0},uSpan:{value:1}},vertexShader:`varying vec2 vPos; void main(){vPos=position.xy;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`,fragmentShader:`uniform float uTime;uniform float uMin;uniform float uSpan;varying vec2 vPos;void main(){float progress=mod(uTime,5.5)/5.5;float pos=(vPos.x+vPos.y*.75-uMin)/max(uSpan,.01);float sweep=progress*1.4-.2;float band=exp(-pow((pos-sweep)/.075,2.0));float envelope=smoothstep(.0,.09,progress)*(1.0-smoothstep(.75,.83,progress));gl_FragColor=vec4(.93,.94,.97,band*.16*envelope);}`});
const sheen=new THREE.Mesh(sheenGeo,sheenMat);sheen.position.z=baseDepth+.014;sheen.visible=false;mesh.add(sheen);mesh.userData.sheen=sheen;
const box=new THREE.Box3().setFromObject(sheen),sz=box.getSize(new THREE.Vector3());sheenMat.uniforms.uMin.value=box.min.x+box.min.y*.75;sheenMat.uniforms.uSpan.value=Math.max(.1,sz.x+sz.y*.75);
}
const metalTop=new THREE.MeshPhysicalMaterial({color:0xaeb3bb,metalness:.55,roughness:.52,clearcoat:.15,clearcoatRoughness:.55,emissive:0x090909});
const metalSide=new THREE.MeshStandardMaterial({color:0x686c72,metalness:.5,roughness:.58});
const partyColors={R:'#8A232D',D:'#1E488A',O:'#62447B'};
function hashDemo(str){let h=2166136261;for(const c of str){h^=c.charCodeAt(0);h=Math.imul(h,16777619)}return h>>>0}
// Synthetic visual-only data. No external election feed or actual race calls.
const governors2026=new Set(['Alabama','Alaska','Arizona','Arkansas','California','Colorado','Connecticut','Florida','Georgia','Hawaii','Idaho','Illinois','Iowa','Kansas','Maine','Maryland','Massachusetts','Michigan','Minnesota','Nebraska','Nevada','New Hampshire','New Mexico','New York','Ohio','Oklahoma','Oregon','Pennsylvania','Rhode Island','South Carolina','South Dakota','Tennessee','Texas','Vermont','Wisconsin','Wyoming']);
const senate2026=new Set(['Alabama','Alaska','Arkansas','Colorado','Delaware','Florida','Georgia','Idaho','Illinois','Iowa','Kansas','Kentucky','Louisiana','Maine','Massachusetts','Michigan','Minnesota','Mississippi','Montana','Nebraska','New Hampshire','New Jersey','New Mexico','North Carolina','Ohio','Oklahoma','Oregon','Rhode Island','South Carolina','South Dakota','Tennessee','Texas','Virginia','West Virginia','Wyoming']);
function raceChoice(){return $('race-select').value==='all'?'senate':$('race-select').value}
function currentState(name){return view==='national'?name:activeState}
function raceAvailable(name,race){if(race==='house')return true;const state=currentState(name);return race==='senate'?senate2026.has(state):governors2026.has(state)}
function fakeResult(name,race='senate'){
 const seed=hashDemo('SYNTHETIC-2026|'+race+'|'+(view==='national'?'US':activeState)+'|'+name);
 const pct=35+(seed%3100)/100;const total=12000+((seed>>>3)%490000);
 const R=Math.round(total*pct/100),D=total-R;const tied=seed%109===0;
 const reported=20+seed%81;const called=reported>75&&seed%4===0;
 const previous=seed%2?'R':'D';const party=tied?'T':R>D?'R':'D';
 return {R:tied?Math.floor(total/2):R,D:tied?Math.floor(total/2):D,total,party,previous,called,reported,flip:called&&party!==previous&&party!=='T',awaiting:seed%23===0};
}
function partyColor(p){return p==='T'?'#C4A436':p==='D'?'#1E488A':'#8A232D'}
function resultsMarkup(name,race){
 if(!raceAvailable(name,race))return `<div class="demo-race no-election"><strong>${raceTitle(race)}</strong><p class="muted">Not on ballot in this state in the 2026 demo.</p></div>`;
 const x=fakeResult(name,race);if(x.awaiting)return `<div class="demo-race"><strong>${raceTitle(race)}</strong><p class="muted">Awaiting Results</p></div>`;
 const dp=100*x.D/(x.D+x.R),rp=100-dp,dl=x.party==='D',rl=x.party==='R';
 const tag=party=>x.party!==party?'':x.called?(x.flip?' · '+(party==='D'?'Democratic':'Republican')+' gain':' · Hold'):x.party==='T'?' · Tied':' · Leading';
 return `<div class="demo-race"><div class="race-header"><strong>${raceTitle(race)}</strong><small>SIMULATED</small></div><div class="race-status"><b>${x.called?'CALLED':'NOT CALLED'}</b><span>${x.reported}% precincts reporting</span></div><div class="race-columns"><div class="candidate ${dl?'front':''}" style="--accent:#729BE1"><span>Democratic${tag('D')}</span><b>${dp.toFixed(1)}%</b><small>${number(x.D)} votes</small></div><div class="candidate right ${rl?'front':''}" style="--accent:#E1848C"><span>Republican${tag('R')}</span><b>${rp.toFixed(1)}%</b><small>${number(x.R)} votes</small></div></div><div class="results-bar"><div class="result-seg ${dl?'front':''}" style="width:${dp}%;background:#1E488A"></div><div class="result-seg ${rl?'front':''}" style="width:${rp}%;background:#8A232D"></div></div>${x.party==='T'?'<div class="reporting">Tied</div>':''}</div>`;
}
function raceTitle(r){return r==='senate'?'U.S. Senate':r==='governor'?'Governor':'U.S. House'}
function chamberMarkup(kind){
 const senate=kind==='senate',baseD=senate?34:0,baseR=senate?31:0,cap=senate?100:435,threshold=senate?51:218;
 const calls=senate?senateCalls:houseCalls,d=baseD+calls.D,r=baseR+calls.R,undecided=cap-d-r;
 const dControl=senate?d>=51:d>=threshold,rControl=senate?r>=50:r>=threshold;
 const control=dControl?'DEMOCRATS GAIN CONTROL':rControl?'REPUBLICANS RETAIN CONTROL':'';
 // Demo-only synthetic breakdown; production must use seat-by-seat previous-holder records.
 const dFlips=Math.floor(calls.D/6),rFlips=Math.floor(calls.R/7);
 return `<div class="chamber"><div class="chamber-title"><strong>U.S. ${senate?'Senate':'House'} · Balance of Power</strong><small>FICTIONAL CALL SIMULATOR</small></div><div class="seat-stats"><div class="dem ${dControl?'control':''}"><span>Democratic caucus</span><b>${d}</b><small>+${calls.D} called</small><small>${calls.D-dFlips} held · <b class="flip-count">${dFlips} flipped</b></small></div><div class="undecided"><span>Undecided</span><b>${undecided}</b></div><div class="rep ${rControl?'control':''}"><span>Republican</span><b>${r}</b><small>+${calls.R} called</small><small>${calls.R-rFlips} held · <b class="flip-count">${rFlips} flipped</b></small></div></div><div class="chamber-bar"><div class="chamber-blue ${dControl?'control':''}" style="width:${d/cap*100}%"></div><div class="chamber-gray" style="width:${undecided/cap*100}%"></div><div class="chamber-red ${rControl?'control':''}" style="width:${r/cap*100}%"></div><div class="finish-line" title="Chamber midpoint"></div></div>${control?`<div class="control-announcement ${dControl?'blue':'red'}">${control} OF THE ${senate?'SENATE':'HOUSE'} · SIMULATED</div>`:''}<div class="sim-controls"><button data-chamber="${kind}" data-party="D" data-delta="1" ${undecided===0?'disabled':''}>+1 D call</button><button data-chamber="${kind}" data-party="R" data-delta="1" ${undecided===0?'disabled':''}>+1 R call</button><button data-chamber="${kind}" data-reset="1">Reset</button></div><div class="hold-note">Hold/flip breakdown is fictional demonstration logic, not linked to individual race calls.</div></div>`;
}
function attachChamberButtons(){detail.querySelectorAll('[data-chamber]').forEach(b=>b.onclick=()=>{const calls=b.dataset.chamber==='senate'?senateCalls:houseCalls;if(b.dataset.reset){calls.D=0;calls.R=0}else{const cap=b.dataset.chamber==='senate'?35:435;if(calls.D+calls.R<cap)calls[b.dataset.party]++}refreshPanel()})}
function racePanel(level,name){const races=$('race-select').value==='all'?['senate','governor','house']:[raceChoice()];
 if(level==='national')return `<div class="sub">NATIONAL · SYNTHETIC DEMO</div><h2>United States</h2><p class="muted">Election-night seat counters start with uncontested seats and grow inward as fictional races are called. NOT ACTUAL RESULTS.</p>${chamberMarkup('senate')}${chamberMarkup('house')}<div class="demo-race"><strong>Governorships</strong><p class="muted">States without a governor race retain their existing party control. Individual gubernatorial races appear when selecting states.</p></div>`;
 return `<div class="sub">${level==='state'?'STATEWIDE & FEDERAL':'COUNTY'} · SIMULATED</div><h2>${level==='county'?name+' County':name}</h2><p class="muted">Entirely fictional candidate results. No real returns or projections.</p>${races.map(r=>resultsMarkup(name,r)).join('')}<p class="notice">SYNTHETIC TEST DATA · No live results connected.</p>${level==='state'&&view==='national'?`<button id="explore-state">Explore ${name} counties</button>`:''}`;
}
function makeStripes(mesh,color){
 if(mesh.userData.stripes){mesh.remove(mesh.userData.stripes);mesh.userData.stripes.geometry.dispose();mesh.userData.stripes.material.dispose();mesh.userData.stripes=null}
 // Fine stripes are evaluated in the geography's own local coordinates and clipped to its exact top surface.
 const geo=mesh.geometry.clone();const mat=new THREE.ShaderMaterial({transparent:true,depthWrite:false,polygonOffset:true,polygonOffsetFactor:-3,uniforms:{uColor:{value:new THREE.Color(color)},uFrequency:{value:view==='national'?2.8:6.8}},vertexShader:`varying vec3 p;varying float topFace;void main(){p=position;topFace=normal.z;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`,fragmentShader:`uniform vec3 uColor;uniform float uFrequency;varying vec3 p;varying float topFace;void main(){if(topFace<0.7)discard;float stripe=fract((p.x+p.y)*uFrequency);if(stripe>0.26)discard;gl_FragColor=vec4(uColor,0.72);}`});const m=new THREE.Mesh(geo,mat);m.position.z=.003;mesh.add(m);mesh.userData.stripes=m;
}
// Expanded contrast for low participation percentages, preserving the actual 0–100% metric.
function earlyGreen(pct){const t=Math.pow(Math.max(0,Math.min(1,pct/100)),.43);const low=[226,248,232],high=[4,86,47];return '#'+low.map((v,i)=>Math.round(v+(high[i]-v)*t).toString(16).padStart(2,'0')).join('')}

// Call the Map nationwide aggregate feed. All state data remains attributed and dated;
// missing fields are never inferred. Texas county percentages remain the official snapshot.
const nationalEarly=new Map();let nationalChecked='',nationalStatus='Loading nationwide data…';
const nationalFeed='./data/early-vote/US.json';

function nationalRow(name){return nationalEarly.get(name)||null}
function earlyCount(n){return n===null||n===undefined||!Number.isFinite(Number(n))?'Unavailable':number(n)}
function earlyStateMarkup(name){const r=nationalRow(name);if(!r)return '<p class="muted">No national early-vote count available for this state.</p>';
 const source=String(r.source_name||'Call the Map');const date=String(r.counts_through||'not reported');
 const party=r.dem!=null&&r.rep!=null?`<div class="call-row"><span>Registered Democrats voting</span><b>${earlyCount(r.dem)}</b></div><div class="call-row"><span>Registered Republicans voting</span><b>${earlyCount(r.rep)}</b></div><p class="muted">Party registration, not candidate preference.</p>`:'<p class="muted">Party registration breakdown unavailable.</p>';
 return `<p class="muted">Reported through ${date} · ${r.count_via==='civicapi'||r.count_via==='civicapi_latest'?'civicAPI via Call the Map':'Call the Map / state source'}</p><div class="call-row"><span>Early ballots</span><b>${earlyCount(r.total)}</b></div><div class="call-row"><span>Mail</span><b>${earlyCount(r.mail)}</b></div><div class="call-row"><span>In person</span><b>${earlyCount(r.in_person)}</b></div>${party}<div class="call-row"><span>Vs 2022 · same stage</span><b>${r.vs_2022_change??'Unavailable'}</b></div><div class="call-row"><span>Vs 2024 · same stage</span><b>${r.vs_2024_change??'Unavailable'}</b></div><p class="muted">Source: ${source}. County-level reporting may lag state totals.</p>`;
}
async function loadNationalEarly(){
 try{
  const response=await fetch(nationalFeed,{mode:'cors',cache:'no-cache'});
  if(!response.ok)throw Error('HTTP '+response.status);
  const data=await response.json();
  if(data.schema!=='ctm-early-vote-download-v1'||!Array.isArray(data.states))throw Error('Unexpected data schema');
  const next=new Map();
  for(const r of data.states){if(typeof r.state_name!=='string'||!Number.isFinite(Number(r.total))||Number(r.total)<0)continue;next.set(r.state_name,r);}
  if(next.size<30||next.size>50||!Number.isFinite(Number(data.national?.total))||[...next.values()].reduce((sum,r)=>sum+Number(r.total),0)!==Number(data.national.total))throw Error('Incomplete or inconsistent national feed');
  nationalEarly.clear();for(const [k,v] of next)nationalEarly.set(k,v);
  nationalChecked=data.checked_at||'';
  nationalStatus=`${number(data.national.total)} ballots · ${next.size} states reporting · checked ${nationalChecked.slice(0,10)}`;
  window.dispatchEvent(new CustomEvent('electionhq:national-early-loaded',{detail:{states:next.size,national:data.national,checked_at:nationalChecked}}));
  if(trackerMode==='early'){setMapColor();refreshPanel();updateFloatingPanel();}
 }catch(err){nationalStatus='National feed unavailable · Texas snapshot remains accessible';console.warn('National early-vote feed:',err);window.dispatchEvent(new CustomEvent('electionhq:national-early-error',{detail:{message:String(err)}}));if(trackerMode==='early'){setMapColor();refreshPanel();}}
}

function statewidePct(){let votes=0,registered=0;for(const r of rows.values()){votes+=Number(r.cumulative_total)||0;registered+=Number(r.registered_voters)||0}return registered?100*votes/registered:null}
function setMapColor(){const contextLabel=$('ev-map-context');if(contextLabel)contextLabel.textContent=view==='national'?'NATIONAL: GREEN = RELATIVE REPORTED BALLOTS (LOG SCALE)':activeState==='Texas'?'TEXAS COUNTIES: GREEN = VERIFIED EARLY-VOTE PARTICIPATION (% OF REGISTERED VOTERS)':'COUNTY TURNOUT UNAVAILABLE: NO VERIFIED COUNTY DATA FOR '+activeState.toUpperCase();document.body.classList.toggle('national-early',trackerMode==='early'&&view==='national');document.body.classList.toggle('nontexas-early',trackerMode==='early'&&view==='state'&&activeState!=='Texas');for(const mesh of meshes){const name=mesh.userData.name;if(mesh.userData.isBackdrop){if(trackerMode!=='early'&&mesh.userData.originalTopMaterial)mesh.material[0]=mesh.userData.originalTopMaterial;mesh.material[0].color.set('#222327');mesh.userData.edges.material.opacity=.12;continue;}const race=raceChoice();const available=raceAvailable(name,race);const x=fakeResult(name,race);const earlyRow=view==='state'&&activeState==='Texas'?rows.get(clean(name)):null;const total=earlyRow?Number(earlyRow.cumulative_total):0;const color=trackerMode==='early'?(view==='national'?(nationalRow(name)?earlyGreen(Math.min(100,100*Math.log1p(Number(nationalRow(name).total))/Math.log1p(6000000))):'#343B46'):(earlyRow&&Number.isFinite(Number(earlyRow.cumulative_early_voting_pct))?earlyGreen(Number(earlyRow.cumulative_early_voting_pct)):'#343B46')):(!available?'#1C1D20':x.awaiting?'#3A3D42':partyColor(x.party));// Use an unlit top face for Early Vote so percentages match the legend exactly.
const early=trackerMode==='early';
if(early){if(!mesh.userData.originalTopMaterial){mesh.userData.originalTopMaterial=mesh.material[0];mesh.userData.earlyTopMaterial=new THREE.MeshBasicMaterial({color, toneMapped:false});}mesh.material[0]=mesh.userData.earlyTopMaterial;}else if(mesh.userData.originalTopMaterial){mesh.material[0]=mesh.userData.originalTopMaterial;}
mesh.material[0].color.set(color);mesh.userData.baseColor=color;mesh.userData.edges.material.opacity=mesh.userData.selected?1:(available?.40:.13);if(trackerMode!=='early'&&available&&x.flip)makeStripes(mesh,x.party==='D'?'#9BBEF4':'#F1A1AA');else if(mesh.userData.stripes){mesh.remove(mesh.userData.stripes);mesh.userData.stripes.geometry.dispose();mesh.userData.stripes.material.dispose();mesh.userData.stripes=null}}}
function refreshPanel(){if(selected)updateFloatingPanel();if(trackerMode==='early'&&view==='national'){detail.innerHTML=`<div class="sub">EARLY VOTE · NATIONAL COVERAGE</div><h2>${selected||'United States'}</h2>${selected?earlyStateMarkup(selected):`<p class="muted">${nationalStatus}</p><p class="notice">Map green indicates relative reported ballot volume (log scale), NOT participation percentage. Gray = no data. State reporting dates vary.</p><p class="muted">Call the Map · callthemap.com/early-vote. civicAPI credited where indicated.</p>`}`;return;}if(trackerMode==='early'){const r=view==='state'&&activeState==='Texas'?rows.get(clean(selected||'')):null;detail.innerHTML=`<div class="sub">EARLY VOTE · ${activeState==='Texas'?'TEXAS VERIFIED COUNTY SNAPSHOT':'COUNTY COVERAGE UNAVAILABLE'}</div><h2>${selected||activeState}</h2><p class="muted">${r?'Cumulative early ballots: '+number(r.cumulative_total):'No verified county turnout available for this selection.'}</p><p class="notice">Source: Texas county CSV · October 23, 2026. No partisan election results.</p>`;return;}if(view==='national')detail.innerHTML=racePanel(selected?'state':'national',selected||'United States');else detail.innerHTML=racePanel(selected?'county':'state',selected||activeState);attachChamberButtons();const explore=$('explore-state');if(explore)explore.onclick=()=>enterState(selected);}
function choose(name,{focus=true}={}){
 trackerMode=document.body.classList.contains('early')?'early':'night';
 if(selected===name)name=null;
 panelRace=null;
 selected=name;search.value=name||'';suggestions.hidden=true;
 for(const mesh of meshes){const on=mesh.userData.name===name&&!mesh.userData.isBackdrop;mesh.userData.target=on?(view==='state'?.19:.58):0;mesh.userData.selected=on;mesh.userData.cavity.visible=on||mesh.userData.level>.025;mesh.userData.sheen.visible=on;mesh.userData.edges.material.color.set(on?'#e3e9f6':'#777a80');mesh.userData.edges.material.opacity=on?1:.4;mesh.userData.cavity.children.forEach(c=>{if(c.material)c.material.opacity=on?.9:.22});}
 setMapColor();
 if(name&&focus){const active=meshes.find(m=>m.userData.name===name&&!m.userData.isBackdrop);if(active)frameRegion(active)}
 if(!name&&view==='national'&&focus)cameraView(false);
 refreshPanel();updateFloatingPanel();
 window.dispatchEvent(new CustomEvent('electionhq:geography-change',{detail:{view,activeState,selected:name}}));
 if(trackerMode==='early'&&view==='state'&&activeState==='Texas')window.dispatchEvent(new CustomEvent('electionhq:map-selection',{detail:{county:name||null}}));
}
window.addEventListener('electionhq:select-county',e=>{const name=clean(e.detail?.county);if(trackerMode!=='early')return;if(view==='state'&&activeState==='Texas'){if(meshes.some(m=>m.userData.name===name&&!m.userData.isBackdrop)){if(selected!==name)choose(name,{focus:true});else{const active=meshes.find(m=>m.userData.name===name&&!m.userData.isBackdrop);if(active)frameRegion(active);}}}else{enterState('Texas').then(()=>choose(name,{focus:true}));}});
let panelRace=null;
const floatingPanel=$('map-results-panel'),floatingContent=$('map-panel-content');
function updateFloatingPanel(){
 // The tab is the authoritative UI mode even if the module loaded after the tab switched.
 trackerMode=document.body.classList.contains('early')?'early':'night';
 const open=!!selected;
 floatingPanel.hidden=!open;
 if(!open){panelRace=null;return;}
 if(trackerMode==='early'&&view==='national'){floatingContent.innerHTML=`<h2>${selected}</h2>${earlyStateMarkup(selected)}<button type="button" class="panel-back" id="panel-explore">Explore counties</button>`;const b=floatingContent.querySelector('#panel-explore');if(b)b.onclick=()=>enterState(selected);return;}
 if(trackerMode==='early'){
  const row=view==='state'&&activeState==='Texas'?rows.get(clean(selected)):null;
  const ballots=row?Number(row.cumulative_total):null;
  const registered=row?Number(row.registered_voters):null;
  const pct=row?Number(row.cumulative_early_voting_pct):null;
  const statewide=statewidePct();
  floatingContent.innerHTML=`<h2>${view==='state'?selected+' County':selected}</h2><p class="muted">${activeState==='Texas'?'Texas official county snapshot · October 23, 2026':'County participation not connected for '+activeState}</p>${row?`<div class="call-row"><span>Early ballots</span><b>${number(ballots)}</b></div><div class="call-row"><span>Registered</span><b>${number(registered)}</b></div><div class="call-row"><span>Participation</span><b>${pct.toFixed(2)}%</b></div><div class="call-row"><span>Vs 2024 (same point)</span><b>Unavailable</b></div>`:'<p>County-level details are available for Texas only.</p>'}${view==='national'&&selected==='Texas'?'<button type="button" class="panel-back" id="panel-explore">Explore counties</button>':''}`;
  const explore=floatingContent.querySelector('#panel-explore');if(explore)explore.onclick=()=>enterState('Texas');
  return;
 }
 if(!panelRace)panelRace=raceChoice();
 const options=[['senate','U.S. Senate'],['governor','Governor'],['house','U.S. House']];
 const level=view==='national'?'state':'county';
 const label=level==='county'?selected+' County':selected;
 floatingContent.innerHTML=`<h2>${label}</h2><label for="panel-race-select" class="sub">Race results</label><select id="panel-race-select" class="panel-race-select">${options.map(([key,name])=>`<option value="${key}" ${panelRace===key?'selected':''}>${name}</option>`).join('')}</select><p class="muted">Fictional demonstration · No live returns</p>${resultsMarkup(selected,panelRace)}${level==='state'?`<button type="button" class="panel-back" id="panel-explore">Explore counties</button>`:''}`;
 floatingContent.querySelector('#panel-race-select').onchange=e=>{panelRace=e.target.value;updateFloatingPanel()};
 const explore=floatingContent.querySelector('#panel-explore');if(explore)explore.onclick=()=>enterState(selected);
}
$('map-panel-close').onclick=()=>{choose(null,{focus:false});cameraView(false)};
let zoomNear=1.5,zoomFar=78;
function cameraView(overhead=false){
 focusTween=null;controls.enabled=true;camera.up.set(0,0,1);
 const bounds=new THREE.Box3();
 for(const m of meshes)if(view==='national'||!m.userData.isBackdrop)bounds.expandByObject(m);
 if(bounds.isEmpty())return;
 const center=bounds.getCenter(new THREE.Vector3()),size=bounds.getSize(new THREE.Vector3());
 const aspect=Math.max(.6,stage.clientWidth/Math.max(stage.clientHeight,1));
 const vfov=THREE.MathUtils.degToRad(camera.fov),hfov=2*Math.atan(Math.tan(vfov/2)*aspect);
 // Slight 3D tilt without sacrificing the fitted outline.
 const direction=new THREE.Vector3(0,overhead?-.0001:-.28,1).normalize();
 const projectedHeight=size.y*Math.abs(direction.z)+size.z*Math.abs(direction.y);
 const distance=Math.max(projectedHeight/(2*Math.tan(vfov/2)),size.x/(2*Math.tan(hfov/2)));
 zoomFar=distance*(view==='national'?1.16:.87);
 zoomNear=Math.max(view==='national'?2:.65,zoomFar*.075);
 controls.maxDistance=Math.max(120,zoomFar*1.8);
 controls.target.set(center.x,center.y,0);
 camera.position.copy(controls.target).addScaledVector(direction,zoomFar);
 camera.lookAt(controls.target);camera.updateProjectionMatrix();controls.update();controls.saveState();syncZoom(0);
}
function syncZoom(value){const v=Math.round(THREE.MathUtils.clamp(value,0,100));zoom.value=v;if(document.activeElement!==$('zoom-number'))$('zoom-number').value=v;}
function animateCamera(toTarget,toCamera,duration=700){focusTween={start:performance.now(),duration,fromCamera:camera.position.clone(),fromTarget:controls.target.clone(),toTarget,toCamera};}
function frameRegion(mesh){
 const bounds=new THREE.Box3().setFromObject(mesh);
 const center=bounds.getCenter(new THREE.Vector3());
 const size=bounds.getSize(new THREE.Vector3());
 const span=Math.max(size.x,size.y,.25);
 // A deliberately contextual view: no extreme close-ups on small counties.
 // County widths vary dramatically, so cap both ends of the framing distance.
 const distance=THREE.MathUtils.clamp(4.6+span*1.25,7,31);
 const target=new THREE.Vector3(center.x+distance*.12,center.y,0);
 const direction=new THREE.Vector3(0,-.72,1.18).normalize();
 animateCamera(target,target.clone().addScaledVector(direction,distance),850);
}
$('reset').onclick=()=>cameraView(false);$('top').onclick=()=>cameraView(true);$('angle').onclick=()=>cameraView(false);$('home').onclick=()=>{choose(null,{focus:false});cameraView(false)};$('national').onclick=()=>showNational();
let matches=[];
function updateSuggestions(){const q=search.value.trim().toLowerCase();matches=q?regionNames.filter(n=>n&&n.toLowerCase().includes(q)).slice(0,12):[];suggestions.replaceChildren();for(const name of matches){const b=document.createElement('button');b.type='button';b.textContent=name;b.onclick=()=>{choose(name);suggestions.hidden=true};suggestions.append(b)}suggestions.hidden=!matches.length;}
search.addEventListener('input',updateSuggestions);
search.addEventListener('keydown',e=>{if(e.key==='Enter'){updateSuggestions();if(matches.length){e.preventDefault();choose(matches[0]);suggestions.hidden=true}}if(e.key==='Escape'){choose(null,{focus:false});suggestions.hidden=true}});document.addEventListener('keydown',e=>{if(e.key==='Escape'&&document.activeElement!==search)choose(null,{focus:false});if(e.key==='/'&&document.activeElement!==search){e.preventDefault();search.focus()}});
search.addEventListener('blur',()=>setTimeout(()=>suggestions.hidden=true,180));
function setZoom(value){syncZoom(value);const distance=THREE.MathUtils.lerp(zoomFar,zoomNear,Number(value)/100);const dir=camera.position.clone().sub(controls.target).normalize();animateCamera(controls.target.clone(),controls.target.clone().addScaledVector(dir,distance),280)}
zoom.addEventListener('input',()=>setZoom(zoom.value));
$('zoom-in').onclick=()=>setZoom(Math.min(100,Number(zoom.value)+1));
$('zoom-out').onclick=()=>setZoom(Math.max(0,Number(zoom.value)-1));
const countyURL='https://cdn.jsdelivr.net/gh/plotly/datasets@master/geojson-counties-fips.json';
const statesURL='states-raw.geojson';const projectedStatesURL='states-projected.geojson';
const census='https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer';
const statesList=['Alabama','Alaska','Arizona','Arkansas','California','Colorado','Connecticut','Delaware','Florida','Georgia','Hawaii','Idaho','Illinois','Indiana','Iowa','Kansas','Kentucky','Louisiana','Maine','Maryland','Massachusetts','Michigan','Minnesota','Mississippi','Missouri','Montana','Nebraska','Nevada','New Hampshire','New Jersey','New Mexico','New York','North Carolina','North Dakota','Ohio','Oklahoma','Oregon','Pennsylvania','Rhode Island','South Carolina','South Dakota','Tennessee','Texas','Utah','Vermont','Virginia','Washington','West Virginia','Wisconsin','Wyoming'];
const fipsList=['01','02','04','05','06','08','09','10','12','13','15','16','17','18','19','20','21','22','23','24','25','26','27','28','29','30','31','32','33','34','35','36','37','38','39','40','41','42','44','45','46','47','48','49','50','51','53','54','55','56'];
const stateFips=new Map(statesList.map((n,i)=>[n,fipsList[i]]));
async function json(url){const r=await fetch(url);if(!r.ok)throw Error(`HTTP ${r.status}`);return r.json()}
async function districtFeatures(){const meta=await json(census+'?f=pjson');const lyr=(meta.layers||[]).find(l=>/119th Congress|119th Congressional|Congressional Districts.*119/i.test(l.name));if(!lyr)throw Error('119th congressional layer not found');const info=await json(`${census}/${lyr.id}?f=pjson`);const sf=info.fields.find(f=>/^(STATE|STATEFP|STATEFP20|STATEFP25)$/i.test(f.name));const df=info.fields.find(f=>/^(CD119|CDFP|CD|DISTRICT)$/i.test(f.name));if(!sf||!df)throw Error('Missing geographic identifiers');const params=new URLSearchParams({where:`${sf.name}='48'`,outFields:'*',outSR:'4326',returnGeometry:'true',f:'geojson'});const data=await json(`${census}/${lyr.id}/query?${params}`);return data.features.map(f=>({feature:f,name:`TX-${String(f.properties[df.name]).padStart(2,'0')}`}))}
function stateProjection(name){const feat=stateMap.get(name);if(!feat)return;const pts=[];eachPoly(feat,rings=>rings[0].forEach(p=>pts.push(p)));if(!pts.length)return;const xs=pts.map(p=>p[0]),ys=pts.map(p=>p[1]);const lon=(Math.min(...xs)+Math.max(...xs))/2,lat=(Math.min(...ys)+Math.max(...ys))/2;const spanX=Math.max(...xs)-Math.min(...xs),spanY=Math.max(...ys)-Math.min(...ys);const scale=Math.min(28/Math.max(spanX,1),20/Math.max(spanY,1),name==='Texas'?1.05:5);projection={lon,lat,sx:scale*Math.max(.35,Math.cos(lat*Math.PI/180)),sy:scale};if(name==='Texas')projection={lon:-99.5,lat:31,sx:.85,sy:1.05};}
function resetGroup(){for(const m of meshes){if(m.userData.originalTopMaterial){m.material[0]=m.userData.originalTopMaterial;m.userData.earlyTopMaterial.dispose();delete m.userData.originalTopMaterial;delete m.userData.earlyTopMaterial;}}scene.remove(group);group.traverse(o=>{if(o.geometry)o.geometry.dispose();if(o.material&&o.material!==metalTop&&o.material!==metalSide){(Array.isArray(o.material)?o.material:[o.material]).forEach(m=>m.dispose())}});group=new THREE.Group();scene.add(group);meshes=[];selected=null;}
function finishBuild(data,{preserveCamera=false}={}){resetGroup();data.forEach(({feature,name})=>makeRegion(feature,name));regionNames=data.map(d=>d.name).sort((a,b)=>a.localeCompare(b,undefined,{numeric:true}));search.value='';suggestions.hidden=true;choose(null,{focus:false});if(!preserveCamera)cameraView(false);load.style.display='none';$('national').hidden=view==='national';$('state-name').textContent=view==='national'?'United States':activeState;$('mode-control').hidden=view==='national';$('race-select').value='all';setMapColor();refreshPanel();}
async function showNational(){view='national';void loadPlacesForCurrentView();load.style.display='flex';load.textContent='Loading all 50 state outlines…';try{if(!stateFeatures){const [raw,proj]=await Promise.all([json(statesURL),json(projectedStatesURL)]);stateFeatures=raw.features.filter(f=>statesList.includes(f.properties.name));projectedStates=proj.features.filter(f=>statesList.includes(f.properties.name));if(stateFeatures.length!==50||projectedStates.length!==50)throw Error('Expected 50 states');stateMap=new Map(stateFeatures.map(f=>[f.properties.name,f]));}backdropNames.clear();finishBuild(projectedStates.map(feature=>({feature,name:feature.properties.name})));}catch(e){load.textContent='Unable to load national map: '+e.message;console.error(e)}}
async function enterState(name){focusTween=null;transitionLock=view==='national';activeState=name;activeStateFips=stateFips.get(name);view='state';mode.value='county';void loadPlacesForCurrentView();await show()}
async function show(){view='state';load.style.display='flex';load.textContent='Building '+activeState+' county geography…';try{
 if(!countyFeatures){const raw=await json(countyURL);countyFeatures=raw.features;}
 const data=mode.value==='county'?countyFeatures.filter(f=>String(f.properties.STATE).padStart(2,'0')===activeStateFips).map(f=>({feature:f,name:clean(f.properties.NAME)})):activeState==='Texas'?await districtFeatures():[];
 if(!data.length)throw Error('No county/district geometry available');
 if(activeState==='Texas'&&mode.value==='county'&&data.length!==254)throw Error('Incomplete Texas coverage');
 // Preserve neighboring states in subdued gray while displaying county polygons.
 backdropNames=new Set(stateFeatures.filter(f=>f.properties.name!==activeState).map(f=>f.properties.name));
 const surroundings=[];
 stateProjection(activeState);
 finishBuild(data);
 const stateFeature=stateMap.get(activeState);projectionRegion=activeState;
 const polys=[];eachPoly(stateFeature,rings=>{for(const pt of rings[0])polys.push(new THREE.Vector3(...project(pt),0))});
 const bounds=new THREE.Box3().setFromPoints(polys);const center=bounds.getCenter(new THREE.Vector3()),size=bounds.getSize(new THREE.Vector3());
 // County geometry is framed in its own local projection; do not reuse the national camera.
 cameraView(false);transitionLock=false;
 }catch(e){load.textContent='Unable to load boundaries: '+e.message;console.error(e)}}
mode.onchange=show;
let focusTween=null;
function hitAt(e,includeBackdrop=false){const rect=renderer.domElement.getBoundingClientRect();pointer.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);raycaster.setFromCamera(pointer,camera);return raycaster.intersectObjects(meshes.filter(m=>includeBackdrop||!m.userData.isBackdrop),false)[0]}
let down=null;renderer.domElement.addEventListener('pointerdown',e=>{down={x:e.clientX,y:e.clientY}});
renderer.domElement.addEventListener('pointerup',e=>{if(!down)return;const moved=Math.hypot(e.clientX-down.x,e.clientY-down.y)>5;down=null;if(moved||e.button!==0)return;const hit=hitAt(e,true);if(view==='state'&&(!hit||hit.object.userData.isBackdrop)){showNational();return}if(!hit)return;const name=hit.object.userData.name;if(clickTimer)clearTimeout(clickTimer);clickTimer=setTimeout(()=>{clickTimer=null;choose(name)},240)});
renderer.domElement.addEventListener('dblclick',e=>{e.preventDefault();if(clickTimer){clearTimeout(clickTimer);clickTimer=null}const hit=hitAt(e,true);if(view==='state'&&(!hit||hit.object.userData.isBackdrop)){showNational();return}if(view==='national'&&hit){enterState(hit.object.userData.name);return}if(view==='state'&&hit){choose(hit.object.userData.name)}});
const hover=$('hover-info');let hoverName='';
renderer.domElement.addEventListener('pointermove',e=>{if(e.buttons){hover.hidden=true;return}const hit=hitAt(e);const name=hit?.object.userData.name||'';if(!name){hover.hidden=true;renderer.domElement.style.cursor='grab';return}renderer.domElement.style.cursor='pointer';hover.hidden=false;hover.style.left=Math.min(e.offsetX+16,stage.clientWidth-230)+'px';hover.style.top=Math.max(8,e.offsetY-12)+'px';const race=raceChoice(),x=fakeResult(name,race),available=raceAvailable(name,race);const dp=(100*x.D/(x.D+x.R)).toFixed(1),rp=(100*x.R/(x.D+x.R)).toFixed(1);if(trackerMode==='early'){const row=view==='state'&&activeState==='Texas'?rows.get(clean(name)):null;const national=view==='national'?nationalRow(name):null;hover.innerHTML=`<strong>${name}${view==='state'?' County':''}</strong><span>EARLY VOTE · REPORTED DATA</span><span>${row?'<b>'+Number(row.cumulative_early_voting_pct).toFixed(2)+'% participation</b> · '+number(row.cumulative_total)+' ballots':national?'<b>'+earlyCount(national.total)+' reported ballots</b> · through '+national.counts_through:'No reported data for this geography'}</span>`;return;}hover.innerHTML=`<strong>${name}${view==='state'&&!hit.object.userData.isBackdrop?' County':''}</strong><span>SIMULATED ${raceTitle(race).toUpperCase()}</span>${!available?'<span>Not on ballot</span>':x.awaiting?'<span>Awaiting Results</span>':`<div class="hover-row ${x.party==='D'?'lead':''}" style="color:#80A9EE"><b>D${!x.called&&x.party==='D'?' · Leading':x.called&&x.flip&&x.party==='D'?' · Democratic gain':''}</b><b>${dp}%</b></div><div class="hover-row ${x.party==='R'?'lead':''}" style="color:#E1848C"><b>R${!x.called&&x.party==='R'?' · Leading':x.called&&x.flip&&x.party==='R'?' · Republican gain':''}</b><b>${rp}%</b></div><div class="hover-track" style="height:14px;align-items:center"><i style="width:${dp}%;background:#1E488A;height:${x.party==='D'?'14':'9'}px;${x.party==='D'?'outline:1px solid #b8d6ff;box-shadow:0 0 8px #548be788;':''}"></i><i style="width:${rp}%;background:#8A232D;height:${x.party==='R'?'14':'9'}px;${x.party==='R'?'outline:1px solid #ffb0bb;box-shadow:0 0 8px #df697888;':''}"></i></div><span>${x.called?'Called':'Not called'} · ${x.reported}% reporting</span>`}`;});
renderer.domElement.addEventListener('pointerleave',()=>hover.hidden=true);
$('race-select').addEventListener('change',()=>{setMapColor();refreshPanel();$('race-note').textContent='DEMO DATA · Entirely fictional returns · Map colors represent the selected simulated race';});
// Geographic place labels: locally bundled reference points, no paid map API.
// Coordinates are approximate WGS84 city centers; map display is informational.
// One nationwide city-label engine. Data bundled locally and sorted by population.
const placeLayer=document.createElement('div');placeLayer.className='ehq-place-labels';placeLayer.setAttribute('aria-hidden','true');stage.append(placeLayer);
const placeVector=new THREE.Vector3();let placeLabels=[],placeNodes=[];
// Keep the bundled top-1k fallback; optional expanded state files can be added in one batch.
const statePlaceCache=new Map();let placeLoadToken=0;
async function readPlaceFile(path){const r=await fetch(path);if(!r.ok)throw Error('Place data '+r.status);const d=await r.json();if(d.schema!=='electionhq-place-points-v1'||!Array.isArray(d.places))throw Error('Unexpected place dataset');return d.places.filter(p=>p.length===5&&typeof p[0]==='string'&&typeof p[1]==='string'&&p.slice(2).every(Number.isFinite)&&Math.abs(p[3])<=90&&Math.abs(p[4])<=180)}
let nationalPlacePromise=readPlaceFile('./data/geography/us-cities-top-1000.json').catch(e=>{console.warn('City labels unavailable:',e.message);return []});
function installPlaceLabels(rows){placeLayer.replaceChildren();placeLabels=rows.sort((a,b)=>b[2]-a[2]);placeNodes=placeLabels.map(([name])=>{const el=document.createElement('span');el.className='ehq-place-label';el.textContent=name;el.hidden=true;placeLayer.append(el);return el});lastPlaceCamera='';}
async function loadPlacesForCurrentView(){
 const token=++placeLoadToken,base=await nationalPlacePromise;if(token!==placeLoadToken)return;
 if(view!=='state'||!activeState){installPlaceLabels(base);return}
 const code=stateFips.get(activeState); // Use existing state identifier; missing optional files are normal.
 if(!code){installPlaceLabels(base);return}
 if(!statePlaceCache.has(code))statePlaceCache.set(code,readPlaceFile('./data/geography/places-by-state/'+code+'.json').catch(()=>[]));
 const expanded=await statePlaceCache.get(code);if(token!==placeLoadToken)return;
 const unique=new Map();for(const p of base.filter(p=>p[1]===activeState).concat(expanded)){unique.set(p[1]+'|'+p[0].toLowerCase()+'|'+p[3].toFixed(3)+'|'+p[4].toFixed(3),p)}
 installPlaceLabels([...unique.values()]);
}
let lastPlaceUpdate=0,lastPlaceCamera='',lastPlaceView='';
function updatePlaceLabels(zoomPct){
 // Throttle DOM layout while the camera moves.
 const now=performance.now(),key=view+'|'+activeState+'|'+mode.value+'|'+zoomPct+'|'+camera.position.toArray().map(v=>v.toFixed(2)).join(',')+'|'+controls.target.toArray().map(v=>v.toFixed(2)).join(',');
 if(key===lastPlaceCamera&&lastPlaceView===view)return;
 if(now-lastPlaceUpdate<90)return;
 lastPlaceUpdate=now;lastPlaceCamera=key;lastPlaceView=view;
 if(view!=='state'||mode.value!=='county'||!placeLabels.length){placeLayer.hidden=true;return}
 placeLayer.hidden=false;
 const width=stage.clientWidth,height=stage.clientHeight;
 // Density adjusts with zoom, and a screen-space grid reserves room for labels.
 const minimumPopulation=zoomPct<35?250000:zoomPct<55?100000:zoomPct<75?50000:0; // Unknown-population communities are eligible only at close zoom.
 const cellSize=100,grid=new Set();let shown=0;
 for(let i=0;i<placeLabels.length;i++){
  const [name,state,pop,lat,lon]=placeLabels[i],el=placeNodes[i];
  if(state!==activeState||pop<minimumPopulation){el.hidden=true;continue}
  placeVector.set((lon-projection.lon)*projection.sx,(lat-projection.lat)*projection.sy,.35).project(camera);
  if(placeVector.z< -1||placeVector.z>1){el.hidden=true;continue}
  const x=(placeVector.x+1)*width/2,y=(1-placeVector.y)*height/2;
  const w=Math.max(40,name.length*7+12),h=19;
  if(x<w/2+8||x>width-w/2-8||y<h||y>height-h){el.hidden=true;continue}
  const minX=Math.floor((x-w/2-7)/cellSize),maxX=Math.floor((x+w/2+7)/cellSize),minY=Math.floor((y-h/2-5)/cellSize),maxY=Math.floor((y+h/2+5)/cellSize);
  let blocked=false;for(let gx=minX;gx<=maxX&&!blocked;gx++)for(let gy=minY;gy<=maxY;gy++)if(grid.has(gx+':'+gy)){blocked=true;break}
  if(blocked||shown>=Math.min(100,Math.max(8,Math.floor(width*height/6000)))){el.hidden=true;continue}
  for(let gx=minX;gx<=maxX;gx++)for(let gy=minY;gy<=maxY;gy++)grid.add(gx+':'+gy);
  shown++;el.hidden=false;el.style.left=x+'px';el.style.top=y+'px';
 }
}
function resize(){const w=stage.clientWidth,h=stage.clientHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix()}new ResizeObserver(resize).observe(stage);resize();function tick(){requestAnimationFrame(tick);if(focusTween){controls.enabled=false;const t=Math.min(1,(performance.now()-focusTween.start)/focusTween.duration);const k=t*t*(3-2*t);camera.position.lerpVectors(focusTween.fromCamera,focusTween.toCamera,k);controls.target.lerpVectors(focusTween.fromTarget,focusTween.toTarget,k);if(t===1){focusTween=null;controls.enabled=true;}}for(const mesh of meshes){const t=mesh.userData.target;mesh.userData.level+=(t-mesh.userData.level)*ease();mesh.position.z=mesh.userData.level;if(!mesh.userData.selected&&mesh.userData.level<.012)mesh.userData.cavity.visible=false;}controls.update();const d=camera.position.distanceTo(controls.target);const z=Math.round(THREE.MathUtils.clamp((zoomFar-d)/(zoomFar-zoomNear)*100,0,100));syncZoom(z);updatePlaceLabels(z);zoomLabel.textContent='%';for(const mesh of meshes){if(mesh.userData.sheen)mesh.userData.sheen.material.uniforms.uTime.value=performance.now()/1000;}renderer.render(scene,camera);if(meshes.length && !window.__mapWebGLReady){window.__mapWebGLReady=true;document.getElementById('fallback-map')?.classList.add('webgl-ready');}}tick();
$('zoom-number').addEventListener('change',e=>{const n=Number(e.target.value);if(Number.isFinite(n))setZoom(Math.max(0,Math.min(100,Math.round(n))))});
try{const r=await fetch('./counties-2026-10-23.csv');if(!r.ok)throw Error('County data missing');const lines=(await r.text()).trim().split(/\r?\n/),keys=lines.shift().split(',');for(const line of lines){const cells=line.split(',');const row=Object.fromEntries(keys.map((k,i)=>[k,cells[i]]));rows.set(clean(row.county),row)}if(rows.size!==254||[...rows.values()].reduce((n,r)=>n+Number(r.cumulative_total),0)!==3724290)throw Error('County dataset did not reconcile');await showNational();loadNationalEarly()}catch(e){load.textContent='Unable to validate county data: '+e.message;loadNationalEarly()}
