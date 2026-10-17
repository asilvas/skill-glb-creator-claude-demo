import bpy, sys, math, os
from mathutils import Vector
OUT = r"C:\Users\aaron\skill-glb-creator-claude-demo\runs\baseline-3"
tag = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "v1"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(OUT, "monster.glb"))
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = sc.render.resolution_y = 900
w = bpy.data.worlds.new("w"); w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.8, 0.76, 0.68, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
sc.world = w
for loc, e, rot in (((4, -6, 8), 4, (0.9, 0.2, 0.5)), ((-6, -3, 4), 2, (1.2, 0, -1.2))):
    ld = bpy.data.lights.new("s", 'SUN'); ld.energy = e
    lo = bpy.data.objects.new("s", ld); sc.collection.objects.link(lo); lo.rotation_euler = rot
# ground
bpy.ops.mesh.primitive_plane_add(size=30)
bpy.context.object.data.materials.append(bpy.data.materials.new("g"))
cam = bpy.data.cameras.new("c"); cam.lens = 50
co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co
def shot(name, pos, target=(0, 0, 2.3)):
    co.location = pos
    d = Vector(target) - Vector(pos)
    co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(OUT, f"{tag}_{name}.png")
    bpy.ops.render.render(write_still=True)
# glTF import is Y-up -> Blender Z-up conversion; creature faces -Y in Blender
shot("front", (0, -13, 3.0))
shot("side", (13, 0, 3.0))
shot("back34", (-9, 9, 4.0))
sc.frame_set(1)
for fr in (10, 16, 24):
    sc.frame_set(fr)
    shot(f"f{fr}", (-9, -10, 3.0))
