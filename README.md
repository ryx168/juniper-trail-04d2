# AR landmarks

Scan a real statue with a phone (iPhone or Android), and anyone who scans a QR code can
place the life-size 3D copy in front of them in augmented reality, with no app to install.
Same idea as the AR Code demo at https://x.com/FinanceYF5/status/1700670444817555580.

Everything heavy runs on GitHub Actions. The PC only pushes files.

## How it works

- `site/index.html` — the viewer. On a phone it offers **View in your space**. On Android
  Chrome that opens the camera with tap-to-place (`site/ar-place.js`, WebXR hit-test: an
  orange ring follows the floor, the model is put down where you tap, tap again to move,
  a Scale button cycles 1:1 / 1:2 / 1:4). On iPhone it opens AR Quick Look, where Apple
  places the model and a tap moves it. On a desktop it shows a QR
  code of its own URL so the visitor opens it on a phone. `?m=<id>` picks a model.
- `scans/` — drop phone scans here: `.usdz` from Reality Composer / Object Capture on an
  iPhone, or the `.zip` / `.glb` / `.obj` an Android app exports (see *Scanning*). A scan can
  be a loose file, a folder, or a zip; `scripts/convert_scans.sh` sorts it out. Commit and push.
- `scripts/make_*.py` — procedural stand-ins built by Blender on every run; the file
  name after `make_` is the model id (`make_totem-stanley-park.py` → `models/totem-stanley-park.glb`).
- `.github/workflows/pages.yml` — on every push, Blender 4.5 on the runner runs every
  `make_*.py`, converts every scan into a floor-centred, Y-up, JPEG-textured GLB in
  `site/models/`, registers new ones in `site/models/index.json`, and publishes
  `site/` to GitHub Pages.
- `site/models/index.json` — titles, captions, placement (`floor` or `wall`) and
  scale (`fixed` = life-size) per model. Edit after the first run to name a new scan.

## If the camera shows nothing

Open `https://ar.xotours.ai/?debug=1`. A black box under the title lists the device, whether
WebXR AR / Quick Look are available and which path the button will take. In the camera view a
green line shows session features, frames, floor hits, taps, model state and placement. Any
error is printed there instead of failing silently. A tap always puts down an orange wireframe
box at the spot, replaced by the model once it has loaded, so "box but no model" means the GLB
did not load and "no box" means the tap never reached the session.

iPhone uses model-viewer's in-browser USDZ conversion by default; add `&native=1` to use the
Blender-exported `.usdz` instead.

## Scanning

**iPhone.** Apple *Reality Composer* (free) → Object Capture → walk slowly around the object,
keep it inside the box, let it process on the phone, export `.usdz`. iPhone 12 Pro or newer
works; LiDAR helps with scale.

**Android (Samsung Galaxy etc.).** Samsung has no built-in equivalent of Object Capture and
no LiDAR, so the scan is photos only, reconstructed in the cloud by a free app. Any of these
gives the same kind of result:

| App | Export that works here | Notes |
|---|---|---|
| KIRI Engine (free tier) | *Export → OBJ* gives a `.zip` (obj + mtl + jpg); or GLB | Best on plain or shiny objects, has object masking |
| RealityScan (Epic, free) | `.glb` (via Sketchfab download) | Simplest capture flow |
| Polycam | `.glb` or `.obj` zip (export may need the paid tier) | Object mode only on Android |
| Scaniverse (free) | `.glb` | Processes on the phone |

Take 60–150 photos in a slow walk around the object, two heights, even light, no motion blur,
and keep the whole object in frame. Drop the export straight into `scans/` — the zip does not
need unpacking — and push. The run prints the model height in metres; if it is wrong the app
exported without real-world scale, so set `height_m` in `index.json` by hand.

Keep scans under ~10 MB for phones — re-run the workflow with a *decimate* ratio (0.3–0.5)
from the Actions tab if a scan is too heavy.

## Libraries

- `site/vendor/model-viewer/` — Google `<model-viewer>` 4.1.0, Apache-2.0
- `site/vendor/qrcode/` — `qrcode-generator` 1.4.4, MIT
