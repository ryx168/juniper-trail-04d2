"""Stylised Pacific-Northwest totem pole (Stanley Park, Brockton Point style), ~5.5 m.
Procedural stand-in until the real pole is scanned. OUT_GLB env = output path."""
import bpy, math, os, random
out = os.environ.get("OUT_GLB", "totem-stanley-park.glb")
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 16; sc.cycles.device = 'CPU'
random.seed(7)

def mat(name, rgb, rough=0.8, grain=False):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]; b.inputs["Roughness"].default_value = rough
    if grain:
        wave = nt.nodes.new("ShaderNodeTexWave"); wave.inputs["Scale"].default_value = 1.2
        wave.inputs["Distortion"].default_value = 4.0; wave.inputs["Detail"].default_value = 3
        wave.bands_direction = 'Z'
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = (rgb[0]*0.6, rgb[1]*0.6, rgb[2]*0.6, 1)
        ramp.color_ramp.elements[1].color = (*rgb, 1)
        nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"]); nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
        bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.25
        nt.links.new(wave.outputs["Fac"], bump.inputs["Height"]); nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    else:
        b.inputs["Base Color"].default_value = (*rgb, 1)
    return m

CEDAR = mat("cedar", (0.42, 0.26, 0.14), grain=True)
RED   = mat("paint_red", (0.62, 0.10, 0.08))
BLACK = mat("paint_black", (0.05, 0.05, 0.06))
GREEN = mat("paint_green", (0.10, 0.36, 0.28))
WHITE = mat("paint_white", (0.85, 0.82, 0.74))

objs = []
def add(o, m): o.data.materials.append(m); objs.append(o); return o
def cyl(r, h, z, m=CEDAR, verts=40, name="seg"):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, vertices=verts, location=(0, 0, z + h/2))
    o = bpy.context.object; o.name = name; return add(o, m)
def sphere(r, loc, m, name="s", sx=1, sy=1, sz=1):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=24, ring_count=12, location=loc)
    o = bpy.context.object; o.name = name; o.scale = (sx, sy, sz); bpy.ops.object.shade_smooth(); return add(o, m)
def box(size, loc, m, name="b", rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = size; return add(o, m)
def cone(r1, r2, h, loc, m, rot=(0,0,0), name="c"):
    bpy.ops.mesh.primitive_cone_add(radius1=r1, radius2=r2, depth=h, vertices=24, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; return add(o, m)

R = 0.42                       # pole radius (m)
# base ring + main shaft
cyl(R*1.08, 0.25, 0.0, CEDAR, name="base")
cyl(R, 5.0, 0.25, CEDAR, name="shaft")

def face(z, h, m_face, eye=WHITE, pupil=BLACK, brow=BLACK, mouth=RED, beak=None, beak_len=0.0):
    """A carved face band from z to z+h on the +Y side (front)."""
    cz = z + h*0.5
    cyl(R*1.02, h*0.92, z + h*0.04, m_face, name="band")           # painted band
    # brow ridge
    box((R*1.6, 0.16, h*0.14), (0, R*0.78, z + h*0.80), brow, "brow")
    # eyes (ovals) + pupils
    for sx in (-1, 1):
        sphere(h*0.13, (sx*R*0.45, R*0.92, z + h*0.64), eye, "eye", sx=1.4, sy=0.5, sz=1)
        sphere(h*0.06, (sx*R*0.45, R*1.02, z + h*0.64), pupil, "pupil", sx=1.2, sy=0.5, sz=1)
    if beak is not None:
        # beak: cone pointing +Y, drooping slightly
        cone(R*0.28, 0.02, beak_len, (0, R*0.9 + beak_len*0.45, z + h*0.42), beak, rot=(math.radians(-100), 0, 0), name="beak")
    else:
        # nose + mouth
        box((R*0.36, 0.22, h*0.22), (0, R*0.95, z + h*0.44), BLACK, "nose")
        box((R*1.1, 0.14, h*0.12), (0, R*0.98, z + h*0.22), mouth, "mouth")
    return cz

# bottom figure: bear (black band, red mouth)
face(0.35, 1.25, CEDAR, mouth=RED)
box((R*2.1, 0.30, 0.22), (0, R*0.75, 0.55), BLACK, "bear_paws")
# middle: beaver / human (green band)
face(1.75, 1.15, GREEN, mouth=RED)
# upper: raven with long beak (red band)
face(3.05, 1.15, RED, beak=BLACK, beak_len=0.9)
# top: thunderbird head + wings
face(4.25, 1.0, BLACK, eye=WHITE, pupil=RED, brow=RED, beak=RED, beak_len=0.55)
# wings (angled boards) with painted tips
for sx in (-1, 1):
    box((1.55, 0.16, 0.42), (sx*(R + 0.72), 0, 4.95), BLACK, "wing", rot=(0, math.radians(-18*sx), 0))
    box((0.55, 0.17, 0.30), (sx*(R + 1.35), 0, 5.12), RED, "wingtip", rot=(0, math.radians(-18*sx), 0))
    box((0.9, 0.18, 0.08), (sx*(R + 0.72), 0, 4.95), WHITE, "wingstripe", rot=(0, math.radians(-18*sx), 0))
# head crest
cone(R*0.9, 0.05, 0.45, (0, 0, 5.25 + 0.22), BLACK, name="crest")
for sx in (-1, 1):
    box((0.10, 0.10, 0.45), (sx*0.28, 0, 5.45), RED, "ear")

# --- join, UV, bake cedar grain so the GLB carries it; flat paints export as-is ---
bpy.ops.object.select_all(action='DESELECT')
for o in objs: o.select_set(True)
bpy.context.view_layer.objects.active = objs[1]
bpy.ops.object.join(); pole = bpy.context.object; pole.name = "totem_stanley_park"
# faces were modelled on +Y; glTF's front is +Z, which is Blender -Y, so turn the pole round
import math as _m; pole.rotation_euler[2] = _m.radians(180); bpy.ops.object.transform_apply(rotation=True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.01)
bpy.ops.object.mode_set(mode='OBJECT')

img = bpy.data.images.new("cedar_bake", 1024, 1024)
nt = CEDAR.node_tree; tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img; nt.nodes.active = tex
# bake only the cedar material: select its faces via material slot
sc.render.bake.use_pass_direct = False; sc.render.bake.use_pass_indirect = False
pole.active_material_index = [s.material for s in pole.material_slots].index(CEDAR)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.material_slot_select(); bpy.ops.object.mode_set(mode='OBJECT')
sc.render.bake.use_selected_to_active = False
bpy.ops.object.bake(type='DIFFUSE', margin=4, use_clear=True)
b = nt.nodes["Principled BSDF"]
for l in list(nt.links):
    if l.to_node == b and l.to_socket.name in ("Base Color", "Normal"): nt.links.remove(l)
nt.links.new(tex.outputs["Color"], b.inputs["Base Color"]); img.pack()

bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_apply=True,
                          export_image_format='JPEG', export_jpeg_quality=85, export_yup=True)
print("WROTE", out, os.path.getsize(out))

# optional preview render for eyeballing (PREVIEW_PNG env)
pv = os.environ.get("PREVIEW_PNG")
if pv:
    sc.render.engine = 'BLENDER_EEVEE_NEXT' if hasattr(bpy.types, "SceneEEVEE") else 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = 480, 800; sc.render.filepath = pv
    bpy.ops.object.light_add(type="SUN", location=(4, -6, 10)); bpy.context.object.data.energy = 3
    bpy.ops.object.camera_add(location=(4.5, -7.5, 3.2), rotation=(math.radians(82), 0, math.radians(31)))
    sc.camera = bpy.context.object; sc.camera.data.lens = 35
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.6, 0.7, 0.85, 1)
    bpy.ops.render.render(write_still=True); print("PREVIEW", pv)
