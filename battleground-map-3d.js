import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
const host=document.getElementById('battleground-map');
const watch=new Set('AK AZ FL GA IA KS ME MI MN MS NE NV NH NC OH SC TX VA WI'.split(' '));
const names={Alaska:'AK',Arizona:'AZ',Florida:'FL',Georgia:'GA',Iowa:'IA',Kansas:'KS',Maine:'ME',Michigan:'MI',Minnesota:'MN',Mississippi:'MS',Nebraska:'NE',Nevada:'NV','New Hampshire':'NH','North Carolina':'NC',Ohio:'OH','South Carolina':'SC',Texas:'TX',Virginia:'VA',Wisconsin:'WI'};
let selected='TX',meshes=[],focusTween=null,far=60,near=5;
let renderer;
try{renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});}catch(e){fallback(e);throw e}
renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.setClearColor(0x101010,1);
host.replaceChildren(renderer.domElement);
renderer.domElement.style.cssText='width:100%;height:100%;display:block;touch-action:none';
host.style.height='430px';host.style.minHeight='320px';
const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(38,1,.1,500);
camera.up.set(0,0,1);camera.position.set(0,-28,55);
const controls=new OrbitControls(camera,renderer.domElement);
controls.enableDamping=true;controls.dampingFactor=.055;
controls.mouseButtons={LEFT:THREE.MOUSE.PAN,MIDDLE:THREE.MOUSE.DOLLY,RIGHT:THREE.MOUSE.ROTATE};
controls.rotateSpeed=.19;controls.zoomSpeed=.72;controls.panSpeed=.6;
controls.minPolarAngle=.16;controls.maxPolarAngle=.94;controls.minDistance=.65;controls.maxDistance=120;
scene.add(new THREE.HemisphereLight(0xffffff,0x333333,2));
const light=new THREE.DirectionalLight(0xffffff,2.2);light.position.set(-16,20,36);scene.add(light);
const group=new THREE.Group();scene.add(group);
const raycaster=new THREE.Raycaster(),pointer=new THREE.Vector2();
function animate(toTarget,toPosition,duration=650){focusTween={start:performance.now(),duration,fromTarget:controls.target.clone(),fromPosition:camera.position.clone(),toTarget,toPosition};}
function frame(overhead=false){const bounds=new THREE.Box3().setFromObject(group),center=bounds.getCenter(new THREE.Vector3()),size=bounds.getSize(new THREE.Vector3());if(bounds.isEmpty())return;const aspect=Math.max(.6,host.clientWidth/Math.max(host.clientHeight,1)),vfov=THREE.MathUtils.degToRad(camera.fov),hfov=2*Math.atan(Math.tan(vfov/2)*aspect);const direction=new THREE.Vector3(0,overhead?-.0001:-.28,1).normalize();const dist=Math.max(size.y/(2*Math.tan(vfov/2)),size.x/(2*Math.tan(hfov/2)))*1.16;far=dist;near=Math.max(2,dist*.075);controls.maxDistance=Math.max(120,far*1.8);animate(center,new THREE.Vector3().copy(center).addScaledVector(direction,far),650);}
function setTilt(){const delta=camera.position.clone().sub(controls.target),dist=delta.length(),direction=new THREE.Vector3(0,-.28,1).normalize();animate(controls.target.clone(),controls.target.clone().addScaledVector(direction,dist),500);}
function zoom(step){const delta=camera.position.clone().sub(controls.target),dist=THREE.MathUtils.clamp(delta.length()*(step>0?.9:1.1),near,far*1.8);animate(controls.target.clone(),controls.target.clone().addScaledVector(delta.normalize(),dist),260);}
document.getElementById('map-tilt')?.addEventListener('click',()=>{const b=document.getElementById('map-tilt');const flat=b.getAttribute('aria-pressed')==='true';b.setAttribute('aria-pressed',String(!flat));if(flat)frame(true);else setTilt();});
document.getElementById('map-zoom-in')?.addEventListener('click',()=>zoom(1));
document.getElementById('map-zoom-out')?.addEventListener('click',()=>zoom(-1));
document.getElementById('map-reset')?.addEventListener('click',()=>{document.getElementById('map-tilt')?.setAttribute('aria-pressed','false');frame(false)});
function polygons(feature){const g=feature.geometry;if(!g)return[];return g.type==='Polygon'?[g.coordinates]:g.type==='MultiPolygon'?g.coordinates:[]}
function shape(rings){if(!rings.length)return null;const outer=rings[0],s=new THREE.Shape();if(!outer.length)return null;outer.forEach(([x,y],i)=>i?s.lineTo(x,y):s.moveTo(x,y));for(const hole of rings.slice(1)){if(!hole.length)continue;const p=new THREE.Path();hole.forEach(([x,y],i)=>i?p.lineTo(x,y):p.moveTo(x,y));s.holes.push(p)}return s;}
function renderSelection(){for(const m of meshes){const active=m.userData.code===selected;const watched=watch.has(m.userData.code);m.material[0].color.set(active?'#268cff':watched?'#5b7185':'#393939');m.material[1].color.set(active?'#195b9e':'#292929');m.userData.edges.material.color.set(active?'#e8e8e8':'#737373');}}
function hit(e){const rect=renderer.domElement.getBoundingClientRect();pointer.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);raycaster.setFromCamera(pointer,camera);return raycaster.intersectObjects(meshes,false)[0]?.object}
let down=null;renderer.domElement.addEventListener('pointerdown',e=>{down={x:e.clientX,y:e.clientY}});
renderer.domElement.addEventListener('pointerup',e=>{if(!down)return;const moved=Math.hypot(e.clientX-down.x,e.clientY-down.y)>5;down=null;if(moved||e.button!==0)return;const mesh=hit(e),code=mesh?.userData.code;if(watch.has(code))window.dispatchEvent(new CustomEvent('electionhq:battleground-map-click',{detail:{code}}));});
window.addEventListener('electionhq:battleground-select',e=>{selected=e.detail.code;renderSelection()});
window.addEventListener('electionhq:battleground-data',()=>renderSelection());
function fallback(e){host.dataset.renderReady='error';console.warn('3D map unavailable',e);host.textContent='3D map unavailable; use the state selector or table.';}
async function build(){try{const res=await fetch('./states-projected.geojson');if(!res.ok)throw Error('State geography unavailable');const geo=await res.json();for(const feature of geo.features){const name=feature.properties?.name,code=names[name]||'';for(const rings of polygons(feature)){const s=shape(rings);if(!s)continue;const geom=new THREE.ExtrudeGeometry(s,{depth:.28,bevelEnabled:true,bevelThickness:.025,bevelSize:.025,bevelSegments:1,steps:1});const mesh=new THREE.Mesh(geom,[new THREE.MeshStandardMaterial({color:'#393939',metalness:.06,roughness:.88}),new THREE.MeshStandardMaterial({color:'#292929',roughness:.9})]);mesh.userData={code,name};group.add(mesh);meshes.push(mesh);const edges=new THREE.LineSegments(new THREE.EdgesGeometry(geom,28),new THREE.LineBasicMaterial({color:0x737373,transparent:true,opacity:.7}));mesh.add(edges);mesh.userData.edges=edges;}}if(!meshes.length)throw Error('No state meshes');renderSelection();host.dataset.renderReady='true';host.dataset.stateMeshes=String(new Set(meshes.map(m=>m.userData.name)).size);frame(false);}catch(e){fallback(e)}}
const observer=new ResizeObserver(()=>{const w=host.clientWidth,h=host.clientHeight;if(!w||!h)return;camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h,false)});observer.observe(host);
function tick(t){requestAnimationFrame(tick);if(focusTween){const x=Math.min(1,(t-focusTween.start)/focusTween.duration),ease=x*x*(3-2*x);camera.position.lerpVectors(focusTween.fromPosition,focusTween.toPosition,ease);controls.target.lerpVectors(focusTween.fromTarget,focusTween.toTarget,ease);if(x>=1)focusTween=null;}controls.update();renderer.render(scene,camera)}
requestAnimationFrame(tick);build();
