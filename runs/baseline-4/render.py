import bpy, sys, math
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
prefix = "C:/Users/aaron/skill-glb-creator-claude-demo/runs/baseline-4/" + argv[0]
GLB = r"C:\Users\aaron\skill-glb-creator-claude-demo\runs\baseline-4\monster.glb"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
sc = bpy.context.scene
arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
print('ACTIONS', [(a.name, a.frame_range[:], (a.frame_range[1]-a.frame_range[0])/sc.render.fps) for a in bpy.data.actions], 'fps', sc.render.fps)
# bounds
mn = Vector((1e9,)*3); mx = Vector((-1e9,)*3)
for o in bpy.data.objects:
    if o.type == 'MESH':
        ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
        for vv in me.vertices:
            w = o.matrix_world @ vv.co
            mn = Vector(map(min, mn, w)); mx = Vector(map(max, mx, w))
sc.frame_set(0)
print('BOUNDS (blender zup)', mn, mx)
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = 900, 900
w = bpy.data.worlds.new('w'); w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (0.8, 0.77, 0.7, 1)
w.node_tree.nodes['Background'].inputs[1].default_value = 1.0
sc.world = w
def light(loc, e, kind='SUN'):
    l = bpy.data.lights.new('l', kind); l.energy = e
    o = bpy.data.objects.new('l', l); sc.collection.objects.link(o)
    o.rotation_euler = loc
light((math.radians(50), math.radians(10), math.radians(30)), 4)
light((math.radians(60), 0, math.radians(-140)), 2)
# ground
bpy.ops.mesh.primitive_plane_add(size=30)
bpy.context.object.data.materials.append(bpy.data.materials.new('g'))
cam = bpy.data.cameras.new('c'); cam.lens = 55
co = bpy.data.objects.new('c', cam); sc.collection.objects.link(co); sc.camera = co
def shoot(name, frame, az, dist=11, h=2.4, el=0):
    sc.frame_set(frame)
    co.location = Vector((math.sin(az)*dist, -math.cos(az)*dist, h))
    d = Vector((0, 0, 2.5)) - co.location
    co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{prefix}_{name}.png'
    bpy.ops.render.render(write_still=True)
shoot('front34', 0, math.radians(-35))
shoot('side', 0, math.radians(90))
shoot('back', 0, math.radians(160))
shoot('impact', 15, math.radians(-40))
shoot('wind', 10, math.radians(-40))
