// Shared OrbitControls configuration, matching the established Election Night / Early Vote 3D map.
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
export function createElectionHQControls(camera,canvas){
 const controls=new OrbitControls(camera,canvas);
 controls.enableDamping=true;
 controls.dampingFactor=.055;
 controls.mouseButtons={LEFT:THREE.MOUSE.PAN,MIDDLE:THREE.MOUSE.DOLLY,RIGHT:THREE.MOUSE.ROTATE};
 controls.rotateSpeed=.19;
 controls.zoomSpeed=.72;
 controls.panSpeed=.6;
 controls.minPolarAngle=.16;
 controls.maxPolarAngle=.94;
 controls.minDistance=.65;
 controls.maxDistance=120;
 return controls;
}
