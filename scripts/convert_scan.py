"""Convert a phone scan (.usdz from iPhone Object Capture; .obj/.glb/.fbx/.ply/.stl from the
Android apps - KIRI Engine, Polycam, RealityScan, Scaniverse) to a web-ready .glb.

Run headless with Blender 4.5:
  blender -b --python scripts/convert_scan.py -- <input> <output.glb> [--decimate 0.5]
(the workflow calls it through scripts/convert_scans.sh, which also unpacks .zip exports)

What it does: imports the file, joins everything into one mesh, puts the origin on the
floor at the centre of the footprint, optionally decimates, exports a Y-up GLB with
JPEG textures, and prints the model's height in metres so you can sanity-check scale.
"""
import bpy, os, sys

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(argv) < 2:
    print(__doc__); sys.exit(2)
src, dst = os.path.abspath(argv[0]), os.path.abspath(argv[1])
ratio = float(argv[argv.index("--decimate") + 1]) if "--decimate" in argv else None

bpy.ops.wm.read_factory_settings(use_empty=True)
ext = os.path.splitext(src)[1].lower()
if ext in (".usdz", ".usd", ".usda", ".usdc"):
    bpy.ops.wm.usd_import(filepath=src)
elif ext in (".glb", ".gltf"):
    bpy.ops.import_scene.gltf(filepath=src)
elif ext == ".obj":
    bpy.ops.wm.obj_import(filepath=src)      # picks up the .mtl + textures next to it
elif ext == ".fbx":
    bpy.ops.import_scene.fbx(filepath=src)
elif ext == ".ply":
    bpy.ops.wm.ply_import(filepath=src)
elif ext == ".stl":
    bpy.ops.wm.stl_import(filepath=src)
else:
    raise SystemExit(f"unsupported input {ext}")

meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
if not meshes:
    raise SystemExit("no mesh found in input")
bpy.ops.object.select_all(action="DESELECT")
for o in meshes: o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
if len(meshes) > 1:
    bpy.ops.object.join()
obj = bpy.context.view_layer.objects.active

# origin -> centre of footprint, on the floor
xs = [v.co.x for v in obj.data.vertices]; ys = [v.co.y for v in obj.data.vertices]; zs = [v.co.z for v in obj.data.vertices]
cx, cy, z0 = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2, min(zs)
for v in obj.data.vertices:
    v.co.x -= cx; v.co.y -= cy; v.co.z -= z0
height = max(zs) - z0
print(f"model height: {height:.2f} m, footprint {max(xs)-min(xs):.2f} x {max(ys)-min(ys):.2f} m, "
      f"{len(obj.data.polygons)} faces")

if ratio:
    m = obj.modifiers.new("decimate", "DECIMATE"); m.ratio = ratio
    bpy.ops.object.modifier_apply(modifier=m.name)
    print(f"decimated to {len(obj.data.polygons)} faces")

bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB", export_apply=True,
                          export_image_format="JPEG", export_jpeg_quality=85, export_yup=True)
print("WROTE", dst, f"{os.path.getsize(dst)/1e6:.1f} MB")
