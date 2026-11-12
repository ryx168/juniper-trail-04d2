// Tap-to-place AR (WebXR, Android Chrome). The camera opens, a ring follows the floor,
// and the model is put down only where the visitor taps. Tap again to move it.
// iOS has no WebXR; index.html falls back to AR Quick Look there.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

export async function supported() {
  if (!navigator.xr || !navigator.xr.isSessionSupported) return false;
  try { return await navigator.xr.isSessionSupported('immersive-ar'); } catch (e) { return false; }
}

// Loads a GLB without XR; used by the desktop self-test (?selftest=1) to prove the loader path.
export function loadModel(url) {
  return new Promise((resolve, reject) => new GLTFLoader().load(url, g => resolve(g.scene), undefined, reject));
}

function contactShadow(radius) {
  const c = document.createElement('canvas'); c.width = c.height = 256;
  const ctx = c.getContext('2d');
  const g = ctx.createRadialGradient(128, 128, 20, 128, 128, 128);
  g.addColorStop(0, 'rgba(0,0,0,0.45)'); g.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, 256, 256);
  const tex = new THREE.CanvasTexture(c);
  const m = new THREE.Mesh(new THREE.PlaneGeometry(radius * 2.4, radius * 2.4),
    new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false }));
  m.rotation.x = -Math.PI / 2; m.position.y = 0.005; m.renderOrder = -1;
  return m;
}

/**
 * start({ glb, overlay, hint, scaleBtn, exitBtn, text, onEnd })
 *   overlay  - DOM element shown over the camera (dom-overlay), holds hint + buttons
 *   text     - { find, place, move, scale } strings in the current language
 */
export async function start(opts) {
  const { glb, overlay, hint, scaleBtn, exitBtn, text, onEnd } = opts;
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.xr.enabled = true;
  renderer.domElement.style.cssText = 'position:fixed;inset:0;width:100%;height:100%;z-index:2000';
  document.body.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(70, window.innerWidth / window.innerHeight, 0.01, 60);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x8a7a66, 1.6));
  const sun = new THREE.DirectionalLight(0xffffff, 1.4); sun.position.set(2, 6, 3); scene.add(sun);

  const reticle = new THREE.Mesh(
    new THREE.RingGeometry(0.12, 0.16, 48).rotateX(-Math.PI / 2),
    new THREE.MeshBasicMaterial({ color: 0xff8a3d, transparent: true, opacity: 0.9 }));
  reticle.matrixAutoUpdate = false; reticle.visible = false; scene.add(reticle);

  const model = await loadModel(glb);
  const box = new THREE.Box3().setFromObject(model);
  const size = box.getSize(new THREE.Vector3());
  model.add(contactShadow(Math.max(size.x, size.z) / 2));
  model.visible = false; scene.add(model);

  const scales = [1, 0.5, 0.25]; let si = 0;
  const applyScale = () => { model.scale.setScalar(scales[si]); scaleBtn.textContent = text.scale + ' 1:' + (1 / scales[si]); };
  applyScale();
  scaleBtn.onclick = () => { si = (si + 1) % scales.length; applyScale(); };

  let session;
  try {
    session = await navigator.xr.requestSession('immersive-ar', {
      requiredFeatures: ['hit-test'],
      optionalFeatures: ['dom-overlay', 'light-estimation'],
      domOverlay: { root: overlay }
    });
  } catch (e) {
    renderer.dispose(); renderer.domElement.remove();
    throw e;
  }
  overlay.hidden = false; hint.textContent = text.find;
  // taps on the overlay's buttons must not count as "place here"
  overlay.addEventListener('beforexrselect', e => { if (e.target.closest('button')) e.preventDefault(); });

  renderer.xr.setReferenceSpaceType('local');
  await renderer.xr.setSession(session);
  const viewerSpace = await session.requestReferenceSpace('viewer');
  const hitSource = await session.requestHitTestSource({ space: viewerSpace });

  let placed = false;
  const controller = renderer.xr.getController(0);
  controller.addEventListener('select', () => {
    if (!reticle.visible) return;
    model.position.setFromMatrixPosition(reticle.matrix);
    const cam = renderer.xr.getCamera().position;
    model.rotation.y = Math.atan2(cam.x - model.position.x, cam.z - model.position.z); // face the visitor
    model.visible = true; placed = true; hint.textContent = text.move;
  });
  scene.add(controller);

  exitBtn.onclick = () => session.end();
  session.addEventListener('end', () => {
    renderer.setAnimationLoop(null);
    renderer.dispose(); renderer.domElement.remove();
    overlay.hidden = true;
    if (onEnd) onEnd();
  });

  renderer.setAnimationLoop((t, frame) => {
    if (frame) {
      const ref = renderer.xr.getReferenceSpace();
      const hits = frame.getHitTestResults(hitSource);
      if (hits.length) {
        const pose = hits[0].getPose(ref);
        reticle.visible = true;
        reticle.matrix.fromArray(pose.transform.matrix);
        if (!placed) hint.textContent = text.place;
      } else {
        reticle.visible = false;
        if (!placed) hint.textContent = text.find;
      }
    }
    renderer.render(scene, camera);
  });
  return session;
}
