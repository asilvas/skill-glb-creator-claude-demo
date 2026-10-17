import bpy, bmesh, math, random, os
from mathutils import Vector, Euler, Matrix, Quaternion

OUT = r"C:\Users\aaron\skill-glb-creator-claude-demo\runs\baseline-2"
TEX = r"C:\Users\aaron\skill-glb-creator-claude-demo\assets\textures"
random.seed(7)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = 30

# ---------------- materials ----------------
def load_img(fn, nc):
    img = bpy.data.images.load(os.path.join(TEX, fn))
    img.colorspace_settings.name = 'Non-Color' if nc else 'sRGB'
    return img

def make_mat(name, albedo, normal, rough, normal_strength=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Metallic'].default_value = 0.0
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = load_img(albedo, False)
    nt.links.new(t.outputs['Color'], bsdf.inputs['Base Color'])
    r = nt.nodes.new('ShaderNodeTexImage'); r.image = load_img(rough, True)
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(r.outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = load_img(normal, True)
    nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = normal_strength
    nt.links.new(n.outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    return m

MATS = {
    'stone': make_mat('stone', 'stone-albedo.jpg', 'stone-normal.png', 'stone-roughness.png', 1.2),
    'bark': make_mat('bark', 'bark-albedo.jpg', 'bark-normal.png', 'bark-roughness.png', 1.0),
    'moss': make_mat('moss', 'moss-albedo.png', 'moss-normal.png', 'moss-roughness.png', 0.8),
    'ivory': make_mat('ivory', 'ivory-albedo.jpg', 'ivory-normal.png', 'ivory-roughness.png', 0.8),
}
eye = bpy.data.materials.new('amber_eye'); eye.use_nodes = True
b = eye.node_tree.nodes['Principled BSDF']
b.inputs['Base Color'].default_value = (1.0, 0.55, 0.05, 1)
b.inputs['Emission Color'].default_value = (1.0, 0.55, 0.05, 1)
b.inputs['Emission Strength'].default_value = 6.0
b.inputs['Roughness'].default_value = 0.3
MATS['eye'] = eye

PARTS = []
def finish(bm, name, mat, bone):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    me.materials.append(MATS[mat])
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    vg = ob.vertex_groups.new(name=bone)
    vg.add(list(range(len(me.vertices))), 1.0, 'REPLACE')
    PARTS.append(ob)
    return ob

def box_uv(bm, tile, seed=0):
    uv = bm.loops.layers.uv.verify()
    rnd = random.Random(seed)
    ox, oy = rnd.random(), rnd.random()
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for l in f.loops:
            c = l.vert.co
            if ax == 0: u, v = c.y, c.z
            elif ax == 1: u, v = c.x, c.z
            else: u, v = c.x, c.y
            l[uv].uv = (u / tile + ox, v / tile + oy)

# ---------------- primitives ----------------
def rot_apply(rot, v):
    return Euler(rot, 'XYZ').to_matrix() @ Vector(v)

def rock(name, center, size, bone, rot=(0, 0, 0), cuts=4, subdiv=2, moss=0.0, floor=False, tile=1.4, mat='stone', jitter=0.18):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
    for v in bm.verts:
        v.co *= random.uniform(1 - jitter, 1 + jitter * 0.5)
    for _ in range(cuts):
        n = Vector((random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1))).normalized()
        d = random.uniform(0.45, 0.8)
        for v in bm.verts:
            t = v.co.dot(n) - d
            if t > 0: v.co -= n * t
    S = Matrix.Diagonal((size[0], size[1], size[2], 1))
    R = Euler(rot, 'XYZ').to_matrix().to_4x4()
    T = Matrix.Translation(center)
    bmesh.ops.transform(bm, matrix=T @ R @ S, verts=bm.verts)
    if floor:
        for v in bm.verts: v.co.z = max(v.co.z, 0.0)
    bm.normal_update()
    for f in bm.faces: f.smooth = False
    box_uv(bm, tile, random.randint(0, 999))
    top = max(v.co.z for v in bm.verts)
    cen = center
    finish(bm, name, mat, bone)
    if moss > 0 and random.random() < moss:
        blob(name + '_moss', Vector((cen.x + random.uniform(-.1, .1) * size[0], cen.y + random.uniform(-.1, .1) * size[1], top - 0.04)),
             max(size[0], size[1]) * random.uniform(0.45, 0.7), bone)

def blob(name, center, r, bone, mat='moss', flat=0.35):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    for v in bm.verts:
        v.co *= random.uniform(0.75, 1.15)
        v.co.x *= r; v.co.y *= r * 0.85; v.co.z *= r * flat
        v.co += center
        v.co.z = max(v.co.z, center.z - r * flat * 0.4)
    bm.normal_update()
    for f in bm.faces: f.smooth = True
    box_uv(bm, 0.6, random.randint(0, 999))
    finish(bm, name, mat, bone)

def catmull(ctrl, n):
    P = [ctrl[0]] + list(ctrl) + [ctrl[-1]]
    out = []
    segs = len(ctrl) - 1
    for s in range(segs):
        p0, p1, p2, p3 = P[s], P[s + 1], P[s + 2], P[s + 3]
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(ctrl[-1])
    return out

def interp_r(radii, m):
    out = []
    for i in range(m):
        t = i / (m - 1) * (len(radii) - 1)
        a = int(min(math.floor(t), len(radii) - 2)); f = t - a
        out.append(radii[a] * (1 - f) + radii[a + 1] * f)
    return out

def compute_frames(pts):
    m = len(pts)
    Ts = [(pts[min(i + 1, m - 1)] - pts[max(i - 1, 0)]).normalized() for i in range(m)]
    ref = Vector((1, 0, 0)) if abs(Ts[0].x) < 0.9 else Vector((0, 1, 0))
    N = (ref - Ts[0] * ref.dot(Ts[0])).normalized()
    fr = []
    for i in range(m):
        N = (N - Ts[i] * N.dot(Ts[i])).normalized()
        fr.append((N.copy(), Ts[i].cross(N).normalized()))
    return fr

def add_tube(bm, pts, rad, sides, ax=1.0, ay=1.0, tile=1.0, smooth=True, caps=(True, True)):
    uvl = bm.loops.layers.uv.verify()
    m = len(pts)
    frames = compute_frames(pts)
    verts = []; arc = [0.0]
    for i in range(1, m): arc.append(arc[-1] + (pts[i] - pts[i - 1]).length)
    for i in range(m):
        Ni, Bi = frames[i]
        ring = []
        for s in range(sides):
            th = 2 * math.pi * s / sides
            ring.append(bm.verts.new(pts[i] + (Ni * math.cos(th) * ax + Bi * math.sin(th) * ay) * rad[i]))
        verts.append(ring)
    ravg = sum(rad) / m
    for i in range(m - 1):
        for s in range(sides):
            s2 = (s + 1) % sides
            try:
                f = bm.faces.new((verts[i][s], verts[i][s2], verts[i + 1][s2], verts[i + 1][s]))
            except ValueError:
                continue
            f.smooth = smooth
            us = [s / sides, (s + 1) / sides, (s + 1) / sides, s / sides]
            vs = [arc[i], arc[i], arc[i + 1], arc[i + 1]]
            for l, u, v in zip(f.loops, us, vs):
                l[uvl].uv = (u * 2 * math.pi * ravg / tile, v / tile)
    for end, idx in ((caps[0], 0), (caps[1], m - 1)):
        if not end: continue
        c = bm.verts.new(pts[idx])
        for s in range(sides):
            s2 = (s + 1) % sides
            tri = (verts[idx][s2], verts[idx][s], c) if idx == m - 1 else (verts[idx][s], verts[idx][s2], c)
            try:
                f = bm.faces.new(tri)
            except ValueError:
                continue
            f.smooth = smooth
            for l in f.loops:
                l[uvl].uv = (l.vert.co.x / tile, l.vert.co.y / tile)

def limb(name, ctrl, radii, bone, mat='bark', sides=8, strands=0, helix=0.55, turns=1.5, ax=1.0, ay=1.0, n=6, tile=1.0, caps=(True, True), core=0.62, srad=0.55):
    pts = catmull([Vector(c) for c in ctrl], n)
    rad = interp_r(radii, len(pts))
    bm = bmesh.new()
    if strands == 0:
        add_tube(bm, pts, rad, sides, ax, ay, tile, True, caps)
    else:
        add_tube(bm, pts, [r * core for r in rad], sides, ax, ay, tile, True, caps)
        m = len(pts)
        fr = compute_frames(pts)
        for k in range(strands):
            ph = 2 * math.pi * k / strands
            sp = []
            for i in range(m):
                t = i / (m - 1)
                a = ph + turns * 2 * math.pi * t
                off = (fr[i][0] * math.cos(a) * ax + fr[i][1] * math.sin(a) * ay) * helix * rad[i]
                sp.append(pts[i] + off)
            add_tube(bm, sp, [r * srad for r in rad], 6, 1, 1, tile * 0.7, True, caps)
    bm.normal_update()
    return finish(bm, name, mat, bone)

def sphere(name, c, r, bone, mat='bark', scale=(1, 1, 1), tile=1.0, smooth=True):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
    for v in bm.verts:
        v.co = Vector((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2])) + Vector(c)
    bm.normal_update()
    for f in bm.faces: f.smooth = smooth
    box_uv(bm, tile)
    return finish(bm, name, mat, bone)

def shelf(name, c, r, bone, rot=(0, 0, 0), n=3):
    for i in range(n):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
        rr = r * (1 - 0.18 * i)
        for v in bm.verts:
            v.co = Vector((v.co.x * rr, v.co.y * rr * 0.8, v.co.z * 0.05))
            if v.co.y > 0: v.co.y *= 0.2
        R = Euler(rot, 'XYZ').to_matrix().to_4x4()
        bmesh.ops.transform(bm, matrix=Matrix.Translation(Vector(c) + rot_apply(rot, (0, 0, 1)) * i * 0.11) @ R, verts=bm.verts)
        bm.normal_update()
        for f in bm.faces: f.smooth = True
        box_uv(bm, 0.5)
        finish(bm, '%s_%d' % (name, i), 'ivory', bone)

def claw(name, base, direction, length, r, bone, curl=0.6):
    d = Vector(direction).normalized()
    b = Vector(base)
    ctrl = [b, b + d * length * 0.35 + Vector((0, 0, -0.03)), b + d * length * 0.7 + Vector((0, -curl * 0.1, -length * 0.25 * curl)),
            b + d * length * 0.95 + Vector((0, -curl * 0.2, -length * 0.55 * curl))]
    pts = catmull(ctrl, 5)
    rad = [r * (1 - (i / (len(pts) - 1)) ** 0.9 * 0.97) + 0.004 for i in range(len(pts))]
    bm = bmesh.new()
    add_tube(bm, pts, rad, 6, 1.0, 0.8, 0.5, True, (True, True))
    for v in bm.verts: v.co.z = max(v.co.z, 0.03)
    bm.normal_update()
    return finish(bm, name, 'ivory', bone)

def antler(prefix, start, direction, length, r, depth, bone):
    d = Vector(direction).normalized()
    side = Vector((random.uniform(-.3, .3), random.uniform(-.3, .3), 0.2))
    p0 = Vector(start)
    p1 = p0 + d * length * 0.5 + side * length * 0.15
    p2 = p0 + d * length
    limb(prefix, [p0, p1, p2], [r, r * 0.75, r * 0.35], bone, sides=6, n=5, tile=0.6)
    if depth > 0:
        for k, t in enumerate((0.45, 0.75)):
            q = p0 + (p2 - p0) * t
            sgn = 1 if k == 0 else -1
            nd = (d + Vector((sgn * 0.7, random.uniform(-0.4, 0.2), 0.3))).normalized()
            antler('%s_%d' % (prefix, k), q, nd, length * 0.55, r * 0.6, depth - 1, bone)
    else:
        if random.random() < 0.8:
            blob(prefix + '_tuft', p2 - d * 0.05, 0.1, bone, flat=0.7)

# ---------------- skeleton definition ----------------
def V(*a):
    return Vector(a) if len(a) > 1 else Vector(a[0])
BONES = {
 'root':   (None,       (0, 0.05, 0.0),  (0, 0.05, 0.4)),
 'hips':   ('root',     (0, 0.05, 2.0),  (0, 0.0, 2.4)),
 'spine':  ('hips',     (0, 0.0, 2.4),   (0, -0.15, 3.0)),
 'chest':  ('spine',    (0, -0.15, 3.0), (0, -0.4, 3.6)),
 'neck':   ('chest',    (0, -0.4, 3.6),  (0, -0.7, 3.95)),
 'head':   ('neck',     (0, -0.7, 3.95), (0, -0.85, 4.5)),
}
for s, sx in (('L', 1), ('R', -1)):
    BONES['shoulder.' + s] = ('chest', (0.35*sx, -0.35, 3.45), (1.2*sx, -0.35, 3.5))
    BONES['upperarm.' + s] = ('shoulder.' + s, (1.2*sx, -0.35, 3.4), (1.65*sx, -0.5, 2.1))
    BONES['forearm.' + s] = ('upperarm.' + s, (1.65*sx, -0.5, 2.1), (1.65*sx, -0.85, 0.9))
    BONES['hand.' + s] = ('forearm.' + s, (1.65*sx, -0.85, 0.9), (1.6*sx, -1.0, 0.45))
    BONES['thigh.' + s] = ('root', (0.65*sx, 0.0, 2.1), (0.8*sx, -0.4, 1.1))
    BONES['shin.' + s] = ('thigh.' + s, (0.8*sx, -0.4, 1.1), (0.8*sx, 0.1, 0.4))
    BONES['foot.' + s] = ('shin.' + s, (0.8*sx, 0.1, 0.4), (0.8*sx, -0.55, 0.12))

# ---------------- geometry ----------------
limb('pelvis', [(0, 0.1, 1.9), (0, 0.05, 2.2), (0, 0.0, 2.5)], [0.55, 0.62, 0.6], 'hips', strands=5, ax=1.35, ay=1.0, turns=1.0, sides=10)
limb('belly', [(0, 0.0, 2.4), (0, -0.1, 2.75), (0, -0.2, 3.1)], [0.6, 0.66, 0.78], 'spine', strands=6, ax=1.3, ay=1.0, turns=1.0, sides=10)
limb('ribs', [(0, -0.1, 3.0), (0, -0.3, 3.35), (0, -0.45, 3.65)], [0.78, 0.9, 0.7], 'chest', strands=6, ax=1.4, ay=1.0, turns=1.0, sides=10)
for i, (a, bb) in enumerate((((-0.9, -0.7, 3.5), (0.5, -0.6, 2.5)), ((0.9, -0.7, 3.5), (-0.5, -0.6, 2.4)), ((-0.6, 0.45, 3.5), (0.6, 0.35, 2.6)), ((0.3, -0.85, 3.7), (-0.3, -0.9, 3.0)))):
    mid = ((a[0] + bb[0]) / 2, (a[1] + bb[1]) / 2 - 0.12, (a[2] + bb[2]) / 2)
    limb('torsoroot%d' % i, [a, mid, bb], [0.17, 0.2, 0.15], 'chest' if i != 1 else 'spine', strands=3, turns=2.0, sides=6)
limb('neck', [(0, -0.45, 3.5), (0, -0.62, 3.75), (0, -0.78, 4.0)], [0.38, 0.32, 0.3], 'neck', strands=4, turns=1.5, sides=8)
rock('helm', V(0, -0.85, 4.25), (0.62, 0.6, 0.55), 'head', rot=(0.3, 0, 0.2), moss=1.0, cuts=5)
rock('brow', V(0, -1.2, 4.2), (0.45, 0.25, 0.2), 'head', rot=(-0.4, 0, 0), cuts=3)
rock('mask', V(0, -1.12, 3.85), (0.38, 0.32, 0.55), 'head', rot=(0.2, 0, 0.0), cuts=5, tile=0.9)
rock('jaw', V(0, -1.2, 3.55), (0.22, 0.2, 0.3), 'head', rot=(0.35, 0, 0.3), cuts=3, tile=0.7)
rock('cheekL', V(0.4, -0.95, 3.95), (0.2, 0.3, 0.3), 'head', rot=(0, 0.3, 0.5), cuts=3, tile=0.7)
rock('cheekR', V(-0.4, -0.95, 3.95), (0.2, 0.3, 0.3), 'head', rot=(0, -0.3, -0.5), cuts=3, tile=0.7)
rock('crest', V(0, -0.55, 4.55), (0.2, 0.4, 0.35), 'head', rot=(0.4, 0, 0), cuts=3, tile=0.7)
for sx in (1, -1):
    sphere('eye%d' % sx, (0.17 * sx, -1.4, 4.06), 0.075, 'head', 'eye', scale=(1, 0.5, 0.7))
    antler('antler%d' % sx, (0.3 * sx, -0.75, 4.4), (1.0 * sx, 0.1, 0.7), 0.68, 0.15, 2, 'head')
antler('antlerC', (0.1, -0.6, 4.5), (0.0, 0.3, 1.0), 0.4, 0.1, 1, 'head')

rock('pauldronL', V(1.35, -0.2, 3.85), (1.15, 0.95, 0.75), 'shoulder.L', rot=(0.1, 0.25, 0.3), moss=1.0, cuts=5, tile=1.6)
rock('pauldronL2', V(1.8, -0.1, 3.4), (0.45, 0.55, 0.6), 'shoulder.L', rot=(0.2, 0.4, 0.8), moss=1.0, cuts=4)
rock('pauldronL3', V(0.9, 0.0, 4.15), (0.55, 0.5, 0.4), 'shoulder.L', rot=(0.3, 0.0, 0.1), moss=1.0, cuts=4)
rock('pauldronR', V(-1.3, -0.25, 3.75), (0.8, 0.7, 0.55), 'shoulder.R', rot=(0.1, -0.25, -0.3), moss=1.0, cuts=5, tile=1.5)
rock('pauldronR2', V(-1.75, -0.2, 3.35), (0.4, 0.5, 0.55), 'shoulder.R', rot=(0.2, -0.4, -0.8), moss=1.0, cuts=4)
rock('backslab', V(0.1, 0.5, 3.6), (0.9, 0.35, 0.7), 'chest', rot=(-0.2, 0, 0.1), moss=1.0, cuts=5, tile=1.5)
rock('backslab2', V(-0.5, 0.45, 3.2), (0.5, 0.3, 0.5), 'chest', rot=(-0.2, 0, -0.3), moss=1.0, cuts=4)
rock('chest1', V(0.35, -0.85, 3.3), (0.6, 0.3, 0.5), 'chest', rot=(0.15, 0.2, -0.3), moss=1.0, cuts=5, tile=1.2)
rock('chest2', V(-0.45, -0.8, 3.4), (0.5, 0.3, 0.45), 'chest', rot=(0.2, -0.2, 0.4), moss=1.0, cuts=5, tile=1.2)
rock('chest3', V(0.1, -0.85, 2.85), (0.55, 0.28, 0.4), 'spine', rot=(0.1, 0, 0.1), moss=0.8, cuts=5)
rock('chest4', V(-0.5, -0.65, 2.6), (0.35, 0.25, 0.3), 'spine', rot=(0.1, 0, 0.4), moss=0.8, cuts=4)
rock('hipplate', V(0.55, -0.35, 2.15), (0.4, 0.3, 0.35), 'hips', rot=(0.1, 0.2, 0.3), moss=0.8, cuts=4)
rock('hipplateR', V(-0.55, -0.3, 2.1), (0.4, 0.3, 0.35), 'hips', rot=(0.1, -0.2, -0.3), moss=0.8, cuts=4)
shelf('fungusSh', (1.0, -0.25, 3.95), 0.28, 'shoulder.L', rot=(0.5, 0.0, 0.0), n=3)
shelf('fungusSh2', (2.05, -0.15, 3.65), 0.22, 'shoulder.L', rot=(0.0, 1.3, 0.0), n=3)
shelf('fungusChest', (0.7, -0.8, 3.5), 0.2, 'chest', rot=(1.2, 0, 0), n=3)

for s, sx in (('L', 1), ('R', -1)):
    big = 1.0 if s == 'L' else 0.9
    sphere('shJoint' + s, (1.2*sx, -0.35, 3.4), 0.45, 'upperarm.' + s, 'bark')
    limb('upperarm' + s, [(1.2*sx, -0.35, 3.4), (1.5*sx, -0.4, 2.8), (1.65*sx, -0.5, 2.1)], [0.42, 0.4, 0.34], 'upperarm.' + s, strands=5, turns=1.6, sides=8, n=5)
    rock('uaPlate' + s, V(1.75*sx, -0.45, 2.75), (0.3*big, 0.35, 0.55), 'upperarm.' + s, rot=(0, 0.3*sx, 0.2*sx), moss=1.0, cuts=4)
    sphere('elbow' + s, (1.65*sx, -0.5, 2.1), 0.36, 'forearm.' + s, 'bark')
    limb('forearm' + s, [(1.65*sx, -0.5, 2.1), (1.7*sx, -0.65, 1.5), (1.65*sx, -0.85, 0.95)], [0.36, 0.38, 0.3], 'forearm.' + s, strands=5, turns=1.3, sides=8, n=5)
    rock('bracerA' + s, V(1.95*sx, -0.6, 1.6), (0.32*big, 0.42, 0.8*big), 'forearm.' + s, rot=(0.1, 0.1*sx, 0.15*sx), moss=1.0, cuts=5, tile=1.2)
    rock('bracerB' + s, V(1.55*sx, -0.95, 1.5), (0.28, 0.3, 0.6), 'forearm.' + s, rot=(0.2, 0, 0.0), moss=1.0, cuts=4)
    rock('bracerC' + s, V(1.85*sx, -0.35, 1.0), (0.25, 0.3, 0.4), 'forearm.' + s, rot=(0.1, 0.2*sx, 0.3), moss=0.7, cuts=4)
    sphere('palm' + s, (1.62*sx, -0.9, 0.7), 0.34, 'hand.' + s, 'bark', scale=(1.0, 1.0, 0.9))
    limb('wrist' + s, [(1.65*sx, -0.85, 0.95), (1.62*sx, -0.9, 0.7), (1.6*sx, -1.0, 0.5)], [0.3, 0.3, 0.25], 'hand.' + s, strands=4, turns=1.0, sides=8, n=4)
    for k, dx in enumerate((-0.2, 0.0, 0.2)):
        claw('claw%s%d' % (s, k), (1.6*sx + dx, -1.0, 0.7), (0.0, -0.85, -0.3), 1.0 - 0.1 * abs(dx) * 3, 0.13, 'hand.' + s, curl=0.5)
    claw('claw%sT' % s, (1.6*sx - 0.3*sx, -0.85, 0.6), (-0.5*sx, -0.7, -0.2), 0.65, 0.1, 'hand.' + s, curl=0.5)
    shelf('fungusArm' + s, (2.15*sx, -0.55, 1.9), 0.2, 'forearm.' + s, rot=(0, 1.4*sx, 0), n=3)

for s, sx in (('L', 1), ('R', -1)):
    sphere('hipJoint' + s, (0.65*sx, 0.0, 2.1), 0.5, 'thigh.' + s, 'bark')
    limb('thigh' + s, [(0.65*sx, 0.0, 2.1), (0.78*sx, -0.25, 1.6), (0.8*sx, -0.4, 1.1)], [0.5, 0.47, 0.4], 'thigh.' + s, strands=5, turns=1.3, sides=8, n=5)
    rock('thighPlate' + s, V(0.95*sx, -0.35, 1.7), (0.3, 0.38, 0.55), 'thigh.' + s, rot=(0.1, 0.2*sx, 0.1), moss=1.0, cuts=4)
    rock('thighPlateB' + s, V(0.65*sx, -0.5, 1.55), (0.25, 0.3, 0.45), 'thigh.' + s, rot=(0.2, 0, 0), moss=1.0, cuts=4)
    sphere('knee' + s, (0.8*sx, -0.4, 1.1), 0.38, 'shin.' + s, 'bark')
    rock('kneeCap' + s, V(0.8*sx, -0.8, 1.15), (0.35, 0.28, 0.35), 'shin.' + s, rot=(0.2, 0, 0.3*sx), moss=1.0, cuts=4)
    limb('shin' + s, [(0.8*sx, -0.4, 1.1), (0.8*sx, -0.3, 0.8), (0.8*sx, 0.1, 0.45)], [0.38, 0.34, 0.3], 'shin.' + s, strands=5, turns=1.2, sides=8, n=5)
    rock('shinPlate' + s, V(0.95*sx, -0.35, 0.85), (0.22, 0.32, 0.4), 'shin.' + s, rot=(-0.2, 0, 0), moss=1.0, cuts=4)
    rock('calf' + s, V(0.75*sx, 0.25, 0.85), (0.3, 0.3, 0.35), 'shin.' + s, rot=(0.2, 0, 0), moss=1.0, cuts=4)
    limb('ankle' + s, [(0.8*sx, 0.1, 0.5), (0.8*sx, -0.1, 0.3), (0.8*sx, -0.35, 0.2)], [0.3, 0.32, 0.25], 'foot.' + s, strands=4, turns=0.8, sides=8, n=4)
    rock('footMain' + s, V(0.8*sx, -0.25, 0.22), (0.5, 0.75, 0.28), 'foot.' + s, rot=(0.05, 0, 0.1*sx), moss=1.0, cuts=3, floor=True, tile=1.0)
    for k, (dx, dy) in enumerate(((-0.3, -0.85), (0.0, -0.95), (0.3, -0.85))):
        rock('toe%s%d' % (s, k), V(0.8*sx + dx, dy, 0.14), (0.17, 0.25, 0.17), 'foot.' + s, rot=(0.2, 0, dx), moss=0.5, cuts=3, floor=True, tile=0.6, subdiv=1)
    rock('heel' + s, V(0.8*sx, 0.35, 0.2), (0.3, 0.3, 0.2), 'foot.' + s, cuts=3, floor=True, moss=1.0)

# ---------------- join ----------------
bpy.ops.object.select_all(action='DESELECT')
for o in PARTS: o.select_set(True)
bpy.context.view_layer.objects.active = PARTS[0]
bpy.ops.object.join()
mesh_ob = bpy.context.view_layer.objects.active
mesh_ob.name = 'Warden'; mesh_ob.data.name = 'Warden'
for v in mesh_ob.data.vertices:
    if v.co.z < 0: v.co.z = 0.0

# ---------------- armature ----------------
arm_data = bpy.data.armatures.new('WardenRig')
arm = bpy.data.objects.new('WardenRig', arm_data)
bpy.context.collection.objects.link(arm)
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = arm
arm.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for n in BONES:
    par, h, t = BONES[n]
    eb = arm_data.edit_bones.new(n)
    eb.head = V(h); eb.tail = V(t)
    if par: eb.parent = arm_data.edit_bones[par]
bpy.ops.object.mode_set(mode='OBJECT')
mesh_ob.parent = arm
mod = mesh_ob.modifiers.new('Armature', 'ARMATURE'); mod.object = arm

# ---------------- animation ----------------
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')
F0, F1 = 0, 36
scene.frame_start, scene.frame_end = F0, F1

def curve(keys, f):
    if f <= keys[0][0]: return keys[0][1]
    for (fa, va), (fb, vb) in zip(keys, keys[1:]):
        if fa <= f <= fb:
            t = (f - fa) / (fb - fa) if fb > fa else 1
            t = t * t * (3 - 2 * t)
            return va + (vb - va) * t
    return keys[-1][1]

D = math.radians
ANIM = {
 'upperarm.L': {'x': [(0, 0), (11, 150), (13, 150), (19, 320), (23, 320), (36, 360)], 'z': [(0, 0), (11, -10), (19, -35), (23, -30), (36, 0)]},
 'forearm.L':  {'x': [(0, 0), (11, -55), (14, -55), (19, -15), (24, -10), (36, 0)]},
 'hand.L':     {'x': [(0, 0), (11, 25), (19, -20), (36, 0)]},
 'shoulder.L': {'x': [(0, 0), (11, 20), (19, -18), (36, 0)]},
 'upperarm.R': {'x': [(0, 0), (11, -25), (19, 30), (26, 10), (36, 0)], 'z': [(0, 0), (11, 10), (19, -8), (36, 0)]},
 'forearm.R':  {'x': [(0, 0), (11, -20), (19, -30), (36, 0)]},
 'chest':      {'x': [(0, 0), (11, 12), (19, -20), (26, -8), (36, 0)], 'z': [(0, 0), (11, -28), (19, 22), (26, 8), (36, 0)]},
 'spine':      {'x': [(0, 0), (11, 8), (19, -12), (36, 0)], 'z': [(0, 0), (11, -12), (19, 10), (36, 0)]},
 'hips':       {'x': [(0, 0), (11, 5), (19, -8), (36, 0)], 'z': [(0, 0), (11, -8), (19, 6), (36, 0)]},
 'neck':       {'x': [(0, 0), (11, 8), (19, -10), (36, 0)]},
 'head':       {'x': [(0, 0), (11, 6), (19, -8), (36, 0)], 'z': [(0, 0), (11, 5), (19, -5), (36, 0)]},
 'thigh.L':    {'x': [(0, 0), (11, 6), (19, -8), (36, 0)]},
 'thigh.R':    {'x': [(0, 0), (11, 4), (19, -12), (36, 0)]},
 'shin.L':     {'x': [(0, 0), (11, -4), (19, 10), (36, 0)]},
 'shin.R':     {'x': [(0, 0), (11, -4), (19, 14), (36, 0)]},
}
act = bpy.data.actions.new('attack')
arm.animation_data_create(); arm.animation_data.action = act
prev = {}
for f in range(F0, F1 + 1):
    for bn, tl in ANIM.items():
        pb = arm.pose.bones[bn]
        pb.rotation_mode = 'QUATERNION'
        rx = (-1 if bn in ('hips','spine','chest','neck','head') else 1) * D(curve(tl['x'], f)) if 'x' in tl else 0.0
        ry = D(curve(tl['y'], f)) if 'y' in tl else 0.0
        rz = D(curve(tl['z'], f)) if 'z' in tl else 0.0
        R = Euler((rx, ry, rz), 'XYZ').to_matrix()
        M3 = pb.bone.matrix_local.to_3x3()
        q = (M3.inverted() @ R @ M3).to_quaternion()
        if bn in prev and prev[bn].dot(q) < 0: q.negate()
        prev[bn] = q
        pb.rotation_quaternion = q
        pb.keyframe_insert('rotation_quaternion', frame=f)
bpy.ops.object.mode_set(mode='OBJECT')
act.name = 'attack'
scene.frame_set(0)

# ---------------- export ----------------
bpy.ops.object.select_all(action='DESELECT')
arm.select_set(True); mesh_ob.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'warden.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'monster.glb'), export_format='GLB', use_selection=True,
    export_yup=True, export_skins=True, export_animations=True, export_animation_mode='ACTIONS',
    export_image_format='AUTO', export_apply=False, export_force_sampling=True, export_frame_step=1)
print('POLYS', len(mesh_ob.data.polygons))
