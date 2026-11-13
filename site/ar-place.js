// Tap-to-place AR (WebXR, Android Chrome). The camera opens, a ring follows the floor,
// and the model is put down only where the visitor taps. Tap again to move it.
// iOS has no WebXR; index.html falls back to AR Quick Look there.
//
// Order matters: navigator.xr.requestSession() must be the FIRST await after the tap,
// because Chrome only honours it inside the user-activation window (~5 s). Loading the
// model first over a slow connection silently lost the session and the object never showed.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

export async function supported() {
  if (!navigator.xr || !navigator.xr.isSessionSupported) return false;
  try { return await navigator.xr.isSessionSupported('immersive-ar'); } catch (e) { return false; }
}

// Loads a GLB without XR; also used by the desktop self-test (?selftest=1).
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
 * start({ glb, overlay, hint, scaleBtn, exitBtn, text, debug, onEnd })
 *   overlay - DOM element shown over the camera (dom-overlay), holds hint + buttons
 *   text    - { find, place, move, scale, loading, failed } in the current language
 *   debug   - element that receives a one-line status readout (optional)
 * Returns the XRSession. Throws if the session cannot be started (caller falls back).
 */
export function start(opts) {
  const { glb, overlay, hint, scaleBtn, exitBtn, text, debug, onEnd } = opts;
  const dbg = (s) => { if (debug) debug.textContent = s; };

  // --- synchronous setup, then the session request is the first await ---
  overlay.hidden = false; hint.textContent = text.loading;
  const sessionPromise = navigator.xr.requestSession('immersive-ar', {
    requiredFeatures: ['hit-test'],
    optionalFeatures: ['dom-overlay', 'light-estimation'],
    domOverlay: { root: overlay }
  });
  return sessionPromise.then(session => run(session), err => { overlay.hidden = true; throw err; });

  async function run(session) {
    const features = (session.enabledFeatures || []).join(',') || '(enabledFeatures n/a)';
    dbg('session ok · ' + features + ' · setting up…');
    window.__xrSession = session;
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

    const group = new THREE.Group(); group.visible = false; scene.add(group);
    const marker = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.4, 0.4),
      new THREE.MeshBasicMaterial({ color: 0xff8a3d, wireframe: true }));
    marker.position.y = 0.2; group.add(marker);
    let model = null, placed = false, hits = 0, frames = 0;
    const scales = [1, 0.5, 0.25]; let si = 0;
    const applyScale = () => { group.scale.setScalar(scales[si]); scaleBtn.textContent = text.scale + ' 1:' + (1 / scales[si]); };
    applyScale();
    scaleBtn.onclick = () => { si = (si + 1) % scales.length; applyScale(); };

    // taps on the overlay's buttons must not count as "place here"
    overlay.addEventListener('beforexrselect', e => { if (e.target.closest && e.target.closest('button')) e.preventDefault(); });

    renderer.xr.setReferenceSpaceType('local');
    let hitSource = null, setupError = '';
    try {
      await renderer.xr.setSession(session);
      dbg('session ok · renderer bound · hit-test…');
      const viewerSpace = await session.requestReferenceSpace('viewer');
      hitSource = await session.requestHitTestSource({ space: viewerSpace });
    } catch (e) {
      setupError = (e && e.message) ? e.message : String(e);
      hint.textContent = text.failed + ' ' + setupError;
      dbg('setup error: ' + setupError);
    }

    // model loads while the camera is already up
    loadModel(glb).then(m => {
      model = m; group.remove(marker);
      const size = new THREE.Box3().setFromObject(m).getSize(new THREE.Vector3());
      group.add(m); group.add(contactShadow(Math.max(size.x, size.z) / 2));
      dbg('model loaded · ' + size.x.toFixed(2) + 'x' + size.y.toFixed(2) + 'x' + size.z.toFixed(2) + ' m');
      hint.textContent = reticle.visible ? text.place : text.find;
    }).catch(e => { hint.textContent = text.failed + ' ' + (e && e.message ? e.message : e); });

    const placeAt = (pos) => {
      group.position.copy(pos);
      const cam = camera.position;
      group.rotation.y = Math.atan2(cam.x - pos.x, cam.z - pos.z); // face the visitor
      group.visible = true; placed = true; hint.textContent = text.move;
    };
    let taps = 0;
    session.addEventListener('select', () => {
      taps++;
      if (reticle.visible) { placeAt(new THREE.Vector3().setFromMatrixPosition(reticle.matrix)); }
      else {
        // no floor found yet: put it 2 m ahead, on an estimated floor 1.4 m below the phone
        const fwd = new THREE.Vector3(0, 0, -1).applyQuaternion(camera.quaternion); fwd.y = 0;
        if (fwd.lengthSq() < 1e-6) fwd.set(0, 0, -1); fwd.normalize();
        placeAt(new THREE.Vector3(camera.position.x + fwd.x * 2, camera.position.y - 1.4, camera.position.z + fwd.z * 2));
      }
      if (!model) hint.textContent = text.loading + ' (' + text.markerNote + ')';
    });

    exitBtn.onclick = () => session.end();
    session.addEventListener('end', () => {
      renderer.setAnimationLoop(null);
      renderer.dispose(); renderer.domElement.remove();
      overlay.hidden = true;
      if (onEnd) onEnd();
    });

    renderer.setAnimationLoop((t, frame) => {
      if (frame) {
        frames++;
        const ref = renderer.xr.getReferenceSpace();
        const results = hitSource ? frame.getHitTestResults(hitSource) : [];
        if (results.length) {
          hits++;
          const pose = results[0].getPose(ref);
          reticle.visible = true;
          reticle.matrix.fromArray(pose.transform.matrix);
          if (!placed && model) hint.textContent = text.place;
        } else {
          reticle.visible = false;
          if (!placed && model) hint.textContent = text.find;
        }
        if (debug && frames % 15 === 0) dbg('xr ok · ' + features + (setupError ? ' · SETUP ERROR ' + setupError : '') +
          ' · frames ' + frames + ' · hits ' + hits + ' · taps ' + taps + ' · model ' + (model ? 'loaded' : 'loading') +
          ' · placed ' + placed + ' · scale 1:' + (1 / scales[si]) + ' · cam ' + camera.position.x.toFixed(1) + ',' +
          camera.position.y.toFixed(1) + ',' + camera.position.z.toFixed(1));
      }
      renderer.render(scene, camera);
    });
    return session;
  }
}
