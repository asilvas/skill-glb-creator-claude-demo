import bpy, sys, math, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
tag = argv[0]
OUT = r"C:\Users\aaron\skill-glb-creator-claude-demo\runs\baseline-1"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(OUT, 'monster.glb'))
sc = bpy.context.scene
try: sc.render.engine = 'BLENDER_EEVEE'
except Exception: sc.render.engine = 'BLENDER_EEVEE_NEXT'
sc.render.resolution_x = 900; sc.render.resolution_y = 900
sc.render.film_transparent = False
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.78, 0.74, 0.66, 1); bg.inputs[1].default_value = 1.0
# ground
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
g = bpy.context.object
gm = bpy.data.materials.new('g'); gm.use_nodes = True
gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.7, 0.66, 0.58, 1)
g.data.materials.append(gm)
def light(loc, e, kind='SUN', rot=None):
    d = bpy.data.lights.new('l', kind); d.energy = e
    o = bpy.data.objects.new('l', d); sc.collection.objects.link(o); o.location = loc
    o.rotation_euler = rot or (0, 0, 0)
    return o
light((0, 0, 8), 3.0, 'SUN', (math.radians(40), math.radians(10), math.radians(-30)))
light((0, 0, 8), 1.2, 'SUN', (math.radians(60), 0, math.radians(150)))
cam_d = bpy.data.cameras.new('c'); cam_d.lens = 50
cam = bpy.data.objects.new('c', cam_d); sc.collection.objects.link(cam); sc.camera = cam
def shoot(name, pos, target=(0, 0, 2.3)):
    cam.location = pos
    d = Vector(target) - Vector(pos)
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(OUT, f'{tag}_{name}.png')
    bpy.ops.render.render(write_still=True)
# glTF Y-up imported to Blender Z-up; creature faces -Y in Blender
views = argv[1] if len(argv) > 1 else 'all'
shoot('front34', (-7.5, -9, 3.6))
shoot('side', (11, 0, 3.0))
shoot('back', (5, 9, 3.8))
if views == 'all':
    arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
    print('ACTIONS', [(a.name, a.frame_range[:]) for a in bpy.data.actions])
    for f in (0, 9, 14, 18, 30):
        sc.frame_set(f)
        shoot(f'anim{f}', (-9, -8, 3.6))
        shoot(f'animS{f}', (-11, 0, 3.0))
