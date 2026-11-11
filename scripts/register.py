"""Add every site/models/*.glb that index.json does not know about yet.

Runs in the workflow after conversion. A new scan gets a plain entry named after its
file; edit index.json afterwards to give it proper zh/en titles and a caption.
"""
import json, os, sys

folder = sys.argv[1] if len(sys.argv) > 1 else "site/models"
path = os.path.join(folder, "index.json")
data = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {"models": []}
known = {m["id"] for m in data["models"]}
added = 0
for name in sorted(os.listdir(folder)):
    if not name.lower().endswith(".glb"):
        continue
    mid = name[:-4]
    if mid in known:
        continue
    pretty = mid.replace("-", " ").replace("_", " ").strip().title()
    data["models"].append({
        "id": mid,
        "glb": f"models/{name}",
        "placement": "floor",
        "scale": "fixed",
        "title": {"zh": pretty, "en": pretty},
        "caption": {"zh": "掃描自真實景點。", "en": "Scanned from the real landmark."},
        "credit": "iPhone Object Capture scan"
    })
    known.add(mid); added += 1
    print("registered", mid)
missing = [m["id"] for m in data["models"] if not os.path.exists(os.path.join(folder, os.path.basename(m["glb"])))]
if missing:
    print("WARNING: listed in index.json but no file:", ", ".join(missing))
with open(path, "w", encoding="utf-8", newline="\n") as f:
    json.dump(data, f, ensure_ascii=False, indent=2); f.write("\n")
print(f"{added} added, {len(data['models'])} models total")
