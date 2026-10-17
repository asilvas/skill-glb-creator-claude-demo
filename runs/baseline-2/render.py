import bpy, sys, math, os
from mathutils import Vector
OUT = r"C:\Users\aaron\skill-glb-creator-claude-demo\runs\baseline-2"
args = sys.argv[sys.argv.index('--') + 1:]
tag = args[0]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(OUT, 'monster.glb'))
sc = bpy.context.scene
sc.render.resolution_x = 700; sc.render.resolution_y = 800
try:
    sc.render.engine = 'BLENDER_EEVEE'
except Exception:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (0.8, 0.77, 0.7, 1)
w.node_tree.nodes['Background'].inputs[1].default_value = 0.9
def light(loc, e, kind='SUN'):
    d = bpy.data.lights.new('l', kind); d.energy = e
    o = bpy.data.objects.new('l', d); bpy.context.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
light((-4, -6, 8), 4.0)
light((6, -3, 3), 1.5)
# floor
bpy.ops.mesh.primitive_plane_add(size=30); bpy.context.object.name = 'floor'
cam_d = bpy.data.cameras.new('c'); cam_d.lens = 45
cam = bpy.data.objects.new('c', cam_d); bpy.context.collection.objects.link(cam); sc.camera = cam
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
print('ACTIONS', [a.name for a in bpy.data.actions], 'frames', bpy.data.actions[0].frame_range)
# bounds
mesh = max([o for o in bpy.data.objects if o.type == 'MESH' and o.name != 'floor'], key=lambda o: len(o.data.vertices))
from mathutils import Matrix
sc.frame_set(0)
dg = bpy.context.evaluated_depsgraph_get()
ev = mesh.evaluated_get(dg)
zs = [(ev.matrix_world @ v.co) for v in ev.data.vertices]
print('BBOX min', min(v.z for v in zs), 'max', max(v.z for v in zs), 'x', min(v.x for v in zs), max(v.x for v in zs), 'y', min(v.y for v in zs), max(v.y for v in zs))
views = {'front': ((0, 0, 0), None), }
def shot(name, frame, camloc, target=(0, 0, 2.3), lens=45):
    sc.frame_set(frame)
    cam.location = camloc
    cam_d.lens = lens
    cam.rotation_euler = (Vector(target) - Vector(camloc)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(OUT, 'renders', '%s_%s.png' % (tag, name))
    bpy.ops.render.render(write_still=True)
# note: after glTF import, +Z forward becomes Blender -Y
shot('ant', 12, (-8, -9, 3.6), lens=45)
shot('front', 0, (-5.5, -11, 3.6), lens=50)
shot('side', 0, (-12, -1, 3.0), lens=50)
shot('back', 0, (6, 11, 3.6), lens=50)
shot('impact', 15, (-8, -9, 3.6), lens=45)
shot('wind', 9, (-8, -9, 3.6), lens=45)
