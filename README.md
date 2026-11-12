# AR landmarks

Scan a real statue on an iPhone, and anyone who scans a QR code can place the
life-size 3D copy in front of them in augmented reality, with no app to install.
Same idea as the AR Code demo at https://x.com/FinanceYF5/status/1700670444817555580.

Everything heavy runs on GitHub Actions. The PC only pushes files.

## How it works

- `site/index.html` — the viewer. On a phone it offers **View in your space**
  (iOS: AR Quick Look, Android: Scene Viewer / WebXR). On a desktop it shows a QR
  code of its own URL so the visitor opens it on a phone. `?m=<id>` picks a model.
- `scans/` — drop iPhone scans here (`.usdz` from Reality Composer / Object Capture,
  or `.glb` / `.obj` from Polycam, Scaniverse, KIRI Engine). Commit and push.
- `scripts/make_*.py` — procedural stand-ins built by Blender on every run; the file
  name after `make_` is the model id (`make_totem-stanley-park.py` → `models/totem-stanley-park.glb`).
- `.github/workflows/pages.yml` — on every push, Blender 4.5 on the runner runs every
  `make_*.py`, converts every scan into a floor-centred, Y-up, JPEG-textured GLB in
  `site/models/`, registers new ones in `site/models/index.json`, and publishes
  `site/` to GitHub Pages.
- `site/models/index.json` — titles, captions, placement (`floor` or `wall`) and
  scale (`fixed` = life-size) per model. Edit after the first run to name a new scan.

## Scanning

Apple *Reality Composer* (free) → Object Capture → walk slowly around the object, keep
it inside the box, let it process on the phone, export `.usdz`. iPhone 12 Pro or newer
works; LiDAR helps with scale. Keep scans under ~10 MB for phones — re-run the workflow
with a *decimate* ratio (0.3–0.5) from the Actions tab if a scan is too heavy.

## Libraries

- `site/vendor/model-viewer/` — Google `<model-viewer>` 4.1.0, Apache-2.0
- `site/vendor/qrcode/` — `qrcode-generator` 1.4.4, MIT
