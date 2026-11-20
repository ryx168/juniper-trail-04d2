"""Stylised King Kamehameha I statue, Honolulu (Thomas R. Gould's 1880 design, public domain),
in front of Ali'iolani Hale. Procedural stand-in until the real statue is scanned.

Design cues (Gould's cast): dark figure, gilded feather cloak ('ahu 'ula), feather helmet
(mahiole) and sash (ka'ei), spear in the LEFT hand, RIGHT arm raised with the palm open,
sandals; the plinth carries four partly gilt bas-relief panels. Proportions are approximate.

OUT_GLB env = output path; PREVIEW_PNG env = optional preview render.
The figure faces Blender -Y, which is glTF's +Z front.
"""
import bpy, bmesh, math, os
from mathutils import Vector, noise

out = os.environ.get("OUT_GLB", "kamehameha-honolulu.glb")
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene


# ---------- materials ----------
def flat(name, rgb, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m

def stone(name, base, size=512, seed=0.0):
    """Granite speckle written straight into an image (survives GLB export, no bake)."""
    img = bpy.data.images.new(name + "_tex", size, size)
    px = [0.0] * (size * size * 4)
    for y in range(size):
        for x in range(size):
            n = noise.noise(Vector((x / 41.0, y / 41.0, seed)))
            s = noise.noise(Vector((x / 3.1, y / 3.1, seed + 5)))
            k = 1.0 + 0.10 * n + 0.09 * s
            i = (y * size + x) * 4
            px[i], px[i + 1], px[i + 2], px[i + 3] = base[0] * k, base[1] * k, base[2] * k, 1.0
    img.pixels = px; img.pack()
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = img
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.85
    return m

BRONZE = flat("bronze_dark", (0.075, 0.055, 0.04), rough=0.42, metal=0.85)
GOLD   = flat("gilt", (0.93, 0.68, 0.24), rough=0.28, metal=1.0)
RED    = flat("sash_red", (0.55, 0.06, 0.05), rough=0.55, metal=0.2)
GRANITE = stone("granite", (0.46, 0.45, 0.43), seed=1.0)
BASALT  = stone("basalt", (0.20, 0.20, 0.21), seed=7.0)

objs = []
def add(o, m):
    o.data.materials.append(m); objs.append(o); return o

def box(size, loc, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object; o.scale = size; return add(o, m)

def sphere(r, loc, m, sx=1, sy=1, sz=1, seg=24):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=seg, ring_count=seg // 2, location=loc)
    o = bpy.context.object; o.scale = (sx, sy, sz); bpy.ops.object.shade_smooth(); return add(o, m)

def limb(p0, p1, r0, r1, m, verts=20):
    """Tapered cylinder from point p0 (radius r0) to p1 (radius r1)."""
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    bpy.ops.mesh.primitive_cone_add(radius1=r0, radius2=r1, depth=d.length, vertices=verts,
                                    location=(p0 + p1) / 2)
    o = bpy.context.object
    o.rotation_mode = "QUATERNION"; o.rotation_quaternion = d.to_track_quat("Z", "Y")
    bpy.ops.object.shade_smooth(); return add(o, m)

def cut_mesh(o, keep):
    """Delete vertices for which keep(co) is False (local coords after transform_apply)."""
    bpy.ops.object.select_all(action="DESELECT"); o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not keep(v.co)], context="VERTS")
    bm.to_mesh(o.data); bm.free()


# ---------- plinth (stepped, stacked parts a few mm proud so nothing is coplanar) ----------
box((2.70, 2.70, 0.40), (0, 0, 0.20), GRANITE)              # lower step  0.00-0.40
box((2.25, 2.25, 0.32), (0, 0, 0.555), GRANITE)             # upper step  0.395-0.715
box((1.70, 1.70, 1.62), (0, 0, 1.515), BASALT)              # die         0.705-2.325
box((1.98, 1.98, 0.22), (0, 0, 2.425), GRANITE)             # cornice     2.315-2.535
box((1.52, 1.52, 0.14), (0, 0, 2.60), GRANITE)              # top block   2.53-2.67
TOP = 2.67

# four partly gilt bas-relief panels on the die: frame + a few raised gilt shapes
def panel(axis, sign):
    out_c = 0.85 + 0.022                       # die half-width + half panel depth, proud
    def at(u, z, du, dz, depth, m):
        if axis == "y":
            box((du, depth, dz), (u, sign * (out_c + depth / 2 - 0.02), z), m)
        else:
            box((depth, du, dz), (sign * (out_c + depth / 2 - 0.02), u, z), m)
    at(0, 1.52, 1.20, 0.96, 0.04, GOLD)                    # gilt ground
    at(0, 1.52, 1.06, 0.82, 0.05, BASALT)                  # dark recessed field
    at(0, 1.17, 0.96, 0.05, 0.07, GOLD)                    # ground line
    # standing figures in low relief: tapered body + round head (no letter-like shapes)
    for u, hgt, lean in ((-0.33, 0.40, 8), (-0.10, 0.46, -4), (0.14, 0.36, 5), (0.34, 0.30, -10)):
        zb = 1.195 + hgt * 0.40
        if axis == "y":
            box((0.10, 0.07, hgt * 0.80), (u, sign * (out_c + 0.015), zb), GOLD, rot=(0, math.radians(lean), 0))
            sphere(0.055, (u + math.sin(math.radians(lean)) * hgt * 0.4, sign * (out_c + 0.012),
                           1.195 + hgt * 0.80 + 0.05), GOLD, sy=0.55)
        else:
            box((0.07, 0.10, hgt * 0.80), (sign * (out_c + 0.015), u, zb), GOLD, rot=(math.radians(-lean), 0, 0))
            sphere(0.055, (sign * (out_c + 0.012), u + math.sin(math.radians(lean)) * hgt * 0.4,
                           1.195 + hgt * 0.80 + 0.05), GOLD, sx=0.55)
for axis, sign in (("y", -1), ("y", 1), ("x", -1), ("x", 1)):
    panel(axis, sign)


# ---------- figure (about 2.6 m to the helmet crest) ----------
z0 = TOP
# sandals: left foot a little forward (contrapposto)
box((0.13, 0.30, 0.07), (-0.14, -0.05, z0 + 0.035), BRONZE)
box((0.13, 0.30, 0.07), (0.15, 0.04, z0 + 0.035), BRONZE)
# legs
limb((-0.14, -0.02, z0 + 0.06), (-0.12, 0.0, z0 + 1.28), 0.065, 0.105, BRONZE)
limb((0.15, 0.06, z0 + 0.06), (0.12, 0.0, z0 + 1.28), 0.065, 0.105, BRONZE)
# torso (wider at the shoulders, flattened front-to-back)
t = limb((0, 0, z0 + 1.20), (0, 0, z0 + 2.06), 0.19, 0.25, BRONZE, verts=28)
t.scale = (1, 0.62, 1)
# malo (loincloth) and its front flap, gilt
m1 = limb((0, 0, z0 + 1.16), (0, 0, z0 + 1.36), 0.215, 0.205, GOLD, verts=28); m1.scale = (1, 0.66, 1)
box((0.20, 0.05, 0.34), (0, -0.15, z0 + 1.08), GOLD)
# feather sash (ka'ei): red band between two gilt bands, ends hanging at the front
s1 = limb((0, 0, z0 + 1.36), (0, 0, z0 + 1.48), 0.218, 0.215, RED, verts=28); s1.scale = (1, 0.68, 1)
for zz in (z0 + 1.355, z0 + 1.485):
    g = limb((0, 0, zz - 0.012), (0, 0, zz + 0.012), 0.222, 0.222, GOLD, verts=28); g.scale = (1, 0.70, 1)
box((0.09, 0.04, 0.42), (0.07, -0.155, z0 + 1.20), RED, rot=(0, math.radians(6), 0))
box((0.09, 0.04, 0.36), (-0.05, -0.155, z0 + 1.22), GOLD, rot=(0, math.radians(-5), 0))
# neck, head
limb((0, 0, z0 + 2.04), (0, 0, z0 + 2.16), 0.075, 0.07, BRONZE)
sphere(0.13, (0, -0.01, z0 + 2.28), BRONZE, sy=1.05, sz=1.12)
# feather helmet: gilt cap + front-to-back crest
cap = sphere(0.142, (0, -0.005, z0 + 2.31), GOLD, sy=1.08, sz=1.0)
cut_mesh(cap, lambda co: co.z > z0 + 2.29)
box((0.05, 0.30, 0.13), (0, 0.0, z0 + 2.45), GOLD)
sphere(0.075, (0, 0.0, z0 + 2.50), GOLD, sx=0.35, sy=2.0, sz=0.9)

# feather cloak: back half of a flared cone, shoulders to knees, open at the front
bpy.ops.mesh.primitive_cone_add(radius1=0.58, radius2=0.27, depth=1.30, vertices=48,
                                end_fill_type="NOTHING", location=(0, 0.02, z0 + 1.43))
cloak = bpy.context.object; cloak.scale = (1, 0.72, 1); add(cloak, GOLD)
cut_mesh(cloak, lambda co: co.y > -0.06)
sol = cloak.modifiers.new("thick", "SOLIDIFY"); sol.thickness = 0.035; sol.offset = 1
bpy.ops.object.modifier_apply(modifier=sol.name); bpy.ops.object.shade_smooth()
# cloak over the shoulders (two gilt caps)
for sx in (-1, 1):
    sphere(0.13, (sx * 0.23, 0.0, z0 + 2.02), GOLD, sx=1.1, sy=0.9, sz=0.7)

# RIGHT arm (figure's right = -X when the figure faces -Y) raised, palm open
sh_r = Vector((-0.27, 0.0, z0 + 1.98))
el_r = sh_r + Vector((-0.20, -0.22, 0.10))
wr_r = el_r + Vector((-0.10, -0.30, 0.16))
limb(sh_r, el_r, 0.075, 0.065, BRONZE); limb(el_r, wr_r, 0.062, 0.05, BRONZE)
sphere(0.07, el_r, BRONZE)
box((0.11, 0.035, 0.17), wr_r + Vector((-0.02, -0.06, 0.07)), BRONZE, rot=(math.radians(-25), 0, math.radians(15)))
# LEFT arm down, hand forward round the spear shaft
sh_l = Vector((0.27, 0.0, z0 + 1.98))
el_l = sh_l + Vector((0.08, -0.02, -0.42))
hd_l = Vector((0.40, -0.26, z0 + 1.42))
limb(sh_l, el_l, 0.075, 0.065, BRONZE); limb(el_l, hd_l, 0.062, 0.052, BRONZE)
sphere(0.07, el_l, BRONZE); sphere(0.065, hd_l, BRONZE, sx=1.1, sy=1.0, sz=1.3)
# spear: grounded beside the left foot, taller than the king
limb((0.40, -0.26, z0 + 0.02), (0.40, -0.26, z0 + 2.95), 0.024, 0.02, BRONZE, verts=12)
limb((0.40, -0.26, z0 + 2.95), (0.40, -0.26, z0 + 3.20), 0.034, 0.003, GOLD, verts=12)


# ---------- join, UV, export ----------
bpy.ops.object.select_all(action="DESELECT")
for o in objs: o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.object.join(); statue = bpy.context.object; statue.name = "kamehameha_honolulu"
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.01)
bpy.ops.object.mode_set(mode="OBJECT")

zs = [v.co.z for v in statue.data.vertices]
print(f"height {max(zs) - min(zs):.2f} m, {len(statue.data.polygons)} faces")
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", export_apply=True,
                          export_image_format="JPEG", export_jpeg_quality=85, export_yup=True)
print("WROTE", out, os.path.getsize(out))

pv = os.environ.get("PREVIEW_PNG")
if pv:
    sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 24
    sc.render.resolution_x, sc.render.resolution_y = 520, 860; sc.render.filepath = pv
    bpy.ops.object.light_add(type="SUN", location=(4, -6, 10), rotation=(math.radians(40), 0, math.radians(30)))
    bpy.context.object.data.energy = 4
    cam_az = float(os.environ.get("PREVIEW_AZ", "28"))
    a = math.radians(cam_az); dist = 8.5
    bpy.ops.object.camera_add(location=(dist * math.sin(a), -dist * math.cos(a), 3.4))
    cam = bpy.context.object; sc.camera = cam; cam.data.lens = 40
    tgt = Vector((0, 0, 2.9)); cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = (tgt - cam.location).to_track_quat("-Z", "Y")
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.74, 0.9, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.8
    bpy.ops.render.render(write_still=True); print("PREVIEW", pv)
