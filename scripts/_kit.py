"""Shared helpers for the procedural landmark scripts (scripts/make_*.py).

Each make_ script does `from _kit import *`, calls reset(), builds parts with box/cyl/cone/
sphere and the material helpers, then finish(). finish() UV-unwraps, bakes any textured
material to a JPEG, joins everything, exports a Y-up GLB to $OUT_GLB and, if $PREVIEW_PNG is
set, renders a quick EEVEE preview from the front.

Conventions: metres, Z-up in Blender, origin at the centre of the footprint on the floor.
The FRONT faces Blender -Y, which becomes glTF +Z (what model-viewer and AR show first).
This file is not matched by the workflow's make_*.py loop.
"""
import bpy, math, os

OBJS = []


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    OBJS.clear()
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 8
    sc.cycles.device = 'CPU'


def flat(name, rgb, rough=0.7, metal=0.0, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*rgb, 1)
        b.inputs["Emission Strength"].default_value = emit
    return m


def textured(name, rgb, scale=6.0, contrast=0.55, rough=0.75, kind='noise', bands='Z'):
    """Procedural stone/wood colour that finish() bakes into an image texture."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = rough
    if kind == 'wave':
        tex = nt.nodes.new("ShaderNodeTexWave"); tex.bands_direction = bands
        tex.inputs["Scale"].default_value = scale; tex.inputs["Distortion"].default_value = 4.0
    else:
        tex = nt.nodes.new("ShaderNodeTexNoise"); tex.inputs["Scale"].default_value = scale
        tex.inputs["Detail"].default_value = 8.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (rgb[0] * contrast, rgb[1] * contrast, rgb[2] * contrast, 1)
    ramp.color_ramp.elements[1].color = (*rgb, 1)
    nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    m["bake"] = True
    return m


def _fin(o, m, smooth=False, bevel=0.0):
    o.data.materials.append(m)
    if bevel:
        mod = o.modifiers.new("bevel", 'BEVEL'); mod.width = bevel; mod.segments = 2
    if smooth:
        bpy.ops.object.shade_smooth()
    OBJS.append(o)
    return o


def box(size, loc, m, rot=(0, 0, 0), bevel=0.0):
    """size = full (x, y, z) extents; loc = centre."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    return _fin(o, m, bevel=bevel)


def cyl(r, h, z0, m, x=0.0, y=0.0, verts=40, rot=(0, 0, 0), smooth=True):
    """Cylinder standing on z0 (bottom), height h."""
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, vertices=verts, location=(x, y, z0 + h / 2), rotation=rot)
    return _fin(bpy.context.object, m, smooth=smooth)


def cone(r1, r2, h, z0, m, x=0.0, y=0.0, verts=40, rot=(0, 0, 0), smooth=True):
    bpy.ops.mesh.primitive_cone_add(radius1=r1, radius2=r2, depth=h, vertices=verts, location=(x, y, z0 + h / 2), rotation=rot)
    return _fin(bpy.context.object, m, smooth=smooth)


def sphere(r, loc, m, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=24, ring_count=12, location=loc)
    o = bpy.context.object; o.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    return _fin(o, m, smooth=True)


def ring_of(n, radius, make, z=0.0, phase=0.0):
    """Call make(x, y, angle) n times around a circle."""
    for i in range(n):
        a = phase + 2 * math.pi * i / n
        make(radius * math.cos(a), radius * math.sin(a), a)


def tilt_all(deg, axis='Y', pivot=(0, 0, 0)):
    """Rotate every part rigidly about a floor pivot (the leaning tower)."""
    import mathutils
    T = mathutils.Matrix.Translation(pivot)
    M = T @ mathutils.Matrix.Rotation(math.radians(deg), 4, axis) @ T.inverted()
    for o in OBJS:
        o.matrix_world = M @ o.matrix_world
    bpy.context.view_layer.update()


def _bake(mat, objs, size=1024):
    sc = bpy.context.scene
    img = bpy.data.images.new(mat.name + "_bake", size, size)
    nt = mat.node_tree
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img; nt.nodes.active = tex
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    sc.render.bake.use_pass_direct = False; sc.render.bake.use_pass_indirect = False
    bpy.ops.object.bake(type='DIFFUSE', margin=6)
    b = nt.nodes["Principled BSDF"]
    for l in list(nt.links):
        if l.to_node == b and l.to_socket.name == "Base Color":
            nt.links.remove(l)
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    img.pack()


def finish(name, tex_size=1024):
    out = os.environ.get("OUT_GLB", name + ".glb")
    # apply modifiers + unwrap every part
    for o in OBJS:
        bpy.ops.object.select_all(action='DESELECT')
        o.select_set(True); bpy.context.view_layer.objects.active = o
        for mod in list(o.modifiers):
            bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)
        bpy.ops.object.mode_set(mode='OBJECT')
    # bake textured materials, one image per material
    by_mat = {}
    for o in OBJS:
        m = o.data.materials[0]
        if m.get("bake"):
            by_mat.setdefault(m.name, (m, []))[1].append(o)
    for m, objs in by_mat.values():
        _bake(m, objs, tex_size)
    # join and export
    bpy.ops.object.select_all(action='DESELECT')
    for o in OBJS: o.select_set(True)
    bpy.context.view_layer.objects.active = OBJS[0]
    bpy.ops.object.join(); obj = bpy.context.object; obj.name = name
    # always stand on the floor: lowest vertex at z = 0
    z0 = min((obj.matrix_world @ v.co).z for v in obj.data.vertices)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for v in obj.data.vertices:
        v.co.z -= z0
    xs = [v.co.x for v in obj.data.vertices]; ys = [v.co.y for v in obj.data.vertices]; zs = [v.co.z for v in obj.data.vertices]
    print(f"SIZE {name}: {max(xs)-min(xs):.2f} x {max(ys)-min(ys):.2f} x {max(zs)-min(zs):.2f} m (w x d x h), "
          f"{len(obj.data.polygons)} faces, floor at z={min(zs):.3f}")
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_apply=True,
                              export_image_format='JPEG', export_jpeg_quality=85, export_yup=True)
    print("WROTE", out, os.path.getsize(out))
    pv = os.environ.get("PREVIEW_PNG")
    if pv:
        _preview(pv, obj)


def _preview(path, obj):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
    sc.render.resolution_x, sc.render.resolution_y = 480, 600
    sc.render.filepath = path
    xs = [v.co.x for v in obj.data.vertices]; zs = [v.co.z for v in obj.data.vertices]
    h = max(zs) - min(zs); w = max(xs) - min(xs); d = max(h, w) * 1.9 + 0.5
    target = bpy.data.objects.new("target", None); target.location = (0, 0, h * 0.45)
    sc.collection.objects.link(target)
    bpy.ops.object.camera_add(location=(d * 0.45, -d, h * 0.55 + d * 0.15))
    cam = bpy.context.object; sc.camera = cam; cam.data.lens = 40
    c = cam.constraints.new('TRACK_TO'); c.target = target; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
    bpy.ops.object.light_add(type='SUN', location=(3, -4, 8)); bpy.context.object.data.energy = 3.5
    bpy.context.object.rotation_euler = (math.radians(40), math.radians(10), math.radians(30))
    w_ = bpy.data.worlds.new("w"); sc.world = w_; w_.use_nodes = True
    w_.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.62, 0.72, 1)
    w_.node_tree.nodes["Background"].inputs[1].default_value = 0.9
    bpy.ops.render.render(write_still=True)
    print("PREVIEW", path)
