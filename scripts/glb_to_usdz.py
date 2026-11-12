"""GLB -> USDZ for iOS AR Quick Look. Blender 4.5 headless:
  blender -b --python scripts/glb_to_usdz.py -- in.glb out.usdz
Native USDZ avoids model-viewer's in-browser conversion, which can hand Quick Look an empty scene."""
import bpy, os, sys
argv = sys.argv[sys.argv.index("--") + 1:]
src, dst = os.path.abspath(argv[0]), os.path.abspath(argv[1])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
bpy.ops.wm.usd_export(filepath=dst, export_materials=True, export_textures=True,
                      generate_preview_surface=True, export_uvmaps=True, export_normals=True,
                      convert_orientation=True, export_global_forward_selection='NEGATIVE_Z',
                      export_global_up_selection='Y', selected_objects_only=False)
print("WROTE", dst, os.path.getsize(dst))
