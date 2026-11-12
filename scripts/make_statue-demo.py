import bpy, math, os
out = os.environ.get("OUT_GLB", "statue_demo.glb")
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 16
scene.cycles.device = 'CPU'

def stone_mat(name, base, noise_scale, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nodes = nt.nodes; links = nt.links
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.75
    noise = nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = noise_scale
    noise.inputs["Detail"].default_value = 8.0; noise.inputs["Roughness"].default_value = 0.7
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (base[0]*0.55, base[1]*0.55, base[2]*0.55, 1)
    ramp.color_ramp.elements[1].color = (*base, 1)
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bump = nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = strength
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m

# ---- pedestal: plinth + shaft + cap, slightly weathered ----
parts = []
def box(name, size, loc):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    bev = o.modifiers.new("bevel", 'BEVEL'); bev.width = 0.02; bev.segments = 3
    parts.append(o); return o
box("plinth", (0.95, 0.95, 0.12), (0, 0, 0.06))
box("shaft",  (0.70, 0.70, 1.25), (0, 0, 0.12 + 0.625))
box("cap",    (0.85, 0.85, 0.10), (0, 0, 1.37 + 0.05))
ped_mat = stone_mat("limestone", (0.62, 0.58, 0.50), 6.0, 0.35)
for o in parts: o.data.materials.append(ped_mat)

# ---- bust: Suzanne on a rounded base, smooth + subdivided ----
bpy.ops.mesh.primitive_cylinder_add(radius=0.30, depth=0.10, vertices=48, location=(0, 0, 1.42 + 0.05))
base = bpy.context.object; base.name = "bust_base"
bpy.ops.mesh.primitive_monkey_add(size=0.75, location=(0, 0, 1.47 + 0.42), rotation=(math.radians(8), 0, 0))
head = bpy.context.object; head.name = "bust"
sub = head.modifiers.new("subsurf", 'SUBSURF'); sub.levels = 3; sub.render_levels = 3
bpy.ops.object.shade_smooth()
marble = stone_mat("marble", (0.90, 0.88, 0.84), 3.0, 0.08)
marble.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.35
for o in (base, head): o.data.materials.append(marble)

# ---- bake procedural materials to image textures so glTF carries them ----
bpy.ops.object.select_all(action='DESELECT')
for o in parts + [base, head]:
    o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier=o.modifiers[0].name) if o.modifiers else None
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT'); o.select_set(False)

def bake(mat, objs, size, name):
    img = bpy.data.images.new(name, size, size)
    nt = mat.node_tree
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img
    nt.nodes.active = tex
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    scene.render.bake.use_pass_direct = False; scene.render.bake.use_pass_indirect = False
    bpy.ops.object.bake(type='DIFFUSE', margin=8)
    # rewire: baked image -> base color, drop procedural bump (keep it simple & light)
    bsdf = nt.nodes["Principled BSDF"]
    for l in list(nt.links):
        if l.to_node == bsdf and l.to_socket.name in ("Base Color", "Normal"): nt.links.remove(l)
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    img.pack()

bake(ped_mat, parts, 1024, "limestone_bake")
bake(marble, [base, head], 1024, "marble_bake")

# join into one object, origin at the floor centre, export
bpy.ops.object.select_all(action='DESELECT')
for o in parts + [base, head]: o.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join(); statue = bpy.context.object; statue.name = "xo_statue_demo"
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_apply=True,
                          export_image_format='JPEG', export_jpeg_quality=85, export_yup=True)
print("WROTE", out, os.path.getsize(out))
