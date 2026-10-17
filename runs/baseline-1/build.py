import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Euler

OUT = r"C:\Users\aaron\skill-glb-creator-claude-demo\runs\baseline-1"
TEX = r"C:\Users\aaron\skill-glb-creator-claude-demo\assets\textures"
random.seed(11)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------------------------------------------------------------- bones
BONE_DEFS = {}  # name: (head, tail, parent)
def V(x, y, z): return Vector((x, y, z))

# joints (facing -Y, Z up). Right side = -X
J = dict(
    pelvis=V(0, 0.25, 2.0), spine=V(0, 0.15, 2.55), chest=V(0, -0.05, 3.05), chest_top=V(0, -0.35, 3.65),
    neck=V(0, -0.55, 3.65), head=V(0, -0.75, 3.85), head_top=V(0, -0.8, 4.35),
)
SIDES = {'L': 1, 'R': -1}
for n, s in SIDES.items():
    J['shoulder' + n] = V(s * 1.15, -0.25, 3.45)
    J['elbow' + n] = V(s * 1.65, -0.15, 2.4)
    J['wrist' + n] = V(s * 1.7, -0.7, 1.3)
    J['fingers' + n] = V(s * 1.7, -0.95, 0.75)
    J['hip' + n] = V(s * 0.62, 0.25, 2.0)
    J['knee' + n] = V(s * 0.82, -0.4, 1.1)
    J['ankle' + n] = V(s * 0.76, 0.0, 0.42)
    J['toe' + n] = V(s * 0.76, -0.65, 0.18)

BONE_DEFS['root'] = (V(0, 0.25, 0), V(0, 0.25, 0.5), None)
BONE_DEFS['pelvis'] = (J['pelvis'], J['spine'], 'root')
BONE_DEFS['spine'] = (J['spine'], J['chest'], 'pelvis')
BONE_DEFS['chest'] = (J['chest'], J['chest_top'], 'spine')
BONE_DEFS['neck'] = (J['neck'] + V(0, 0, 0), J['head'], 'chest')
BONE_DEFS['head'] = (J['head'], J['head_top'], 'neck')
for n in 'LR':
    BONE_DEFS['shoulder.' + n] = (J['chest_top'] * 0.5 + J['shoulder' + n] * 0.5 + V(0, 0, 0), J['shoulder' + n], 'chest')
    BONE_DEFS['upper_arm.' + n] = (J['shoulder' + n], J['elbow' + n], 'shoulder.' + n)
    BONE_DEFS['forearm.' + n] = (J['elbow' + n], J['wrist' + n], 'upper_arm.' + n)
    BONE_DEFS['hand.' + n] = (J['wrist' + n], J['fingers' + n], 'forearm.' + n)
    BONE_DEFS['thigh.' + n] = (J['hip' + n], J['knee' + n], 'root')
    BONE_DEFS['shin.' + n] = (J['knee' + n], J['ankle' + n], 'thigh.' + n)
    BONE_DEFS['foot.' + n] = (J['ankle' + n], J['toe' + n], 'shin.' + n)
BONE_NAMES = list(BONE_DEFS.keys())

# ---------------------------------------------------------------- mesh builder
MATS = ['stone', 'bark', 'moss', 'ivory', 'eye']
bm = bmesh.new()
dl = bm.verts.layers.deform.verify()
uvl = bm.loops.layers.uv.verify()
UVS = 0.55

def bi(name): return BONE_NAMES.index(name)

def setw(v, w):
    for k, val in w.items():
        v[dl][bi(k)] = val

def box_uv(faces, scale=UVS):
    for f in faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for l in f.loops:
            c = l.vert.co
            if ax == 0: uv = (c.y, c.z)
            elif ax == 1: uv = (c.x, c.z)
            else: uv = (c.x, c.y)
            l[uvl].uv = (uv[0] * scale, uv[1] * scale)

def finish(verts, mat, w, smooth, uv=True):
    faces = list({f for v in verts for f in v.link_faces})
    for v in verts: setw(v, w)
    for f in faces:
        f.material_index = MATS.index(mat)
        f.smooth = smooth
    bm.normal_update()
    if uv: box_uv(faces)
    return faces

def blob(center, size, mat, w, rot=None, jitter=0.2, sub=1, smooth=False, squash=None):
    res = bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    verts = res['verts']
    if rot is None: rot = [random.uniform(-40, 40) for _ in range(3)]
    M = Matrix.Translation(center) @ Euler([math.radians(a) for a in rot], 'XYZ').to_matrix().to_4x4()
    for v in verts:
        v.co = v.co * (1 + random.uniform(-jitter, jitter))
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
        v.co = M @ v.co
    return finish(verts, mat, w, smooth)

def stone(center, size, w, moss=0.6, rot=None, jitter=0.22, sub=1):
    """Faceted stone plate; optionally topped with a moss cap and fungal shelves."""
    if rot is None: rot = [random.uniform(-35, 35) for _ in range(3)]
    blob(center, size, 'stone', w, rot, jitter, sub)
    if random.random() < moss * 0.85:
        top = center + V(random.uniform(-.1, .1) * size[0], random.uniform(-.1, .1) * size[1], size[2] * 0.7)
        blob(top, (size[0] * 0.6, size[1] * 0.55, size[2] * 0.2), 'moss', w, [rot[0] * .3, rot[1] * .3, rot[2]], 0.3, 2, True)

def shelf(center, r, w, n=3, dirv=V(0, 0, 1)):
    for i in range(n):
        c = center + V(random.uniform(-.03, .03), random.uniform(-.03, .03), 0.0) + dirv * (i * r * 0.7)
        rr = r * (1 - i * 0.15)
        blob(c, (rr, rr * 0.85, rr * 0.26), 'ivory', w, [random.uniform(-15, 15), random.uniform(-15, 15), random.uniform(0, 360)], 0.1, 1, True)

def frames(pts):
    out = []
    prev_n = None
    for i, p in enumerate(pts):
        a = pts[max(i - 1, 0)]; b = pts[min(i + 1, len(pts) - 1)]
        t = (b - a).normalized()
        ref = V(1, 0, 0) if abs(t.x) < 0.85 else V(0, 1, 0)
        n = (ref - t * ref.dot(t)).normalized()
        bn = t.cross(n).normalized()
        out.append((t, n, bn))
    return out

def sample_chain(joints, per, smooth_passes=3):
    pts = []
    for a, b in zip(joints[:-1], joints[1:]):
        for k in range(per):
            pts.append(a.lerp(b, k / per))
    pts.append(joints[-1])
    for _ in range(smooth_passes):
        new = [pts[0]]
        for i in range(1, len(pts) - 1):
            new.append((pts[i - 1] + pts[i] * 2 + pts[i + 1]) / 4)
        new.append(pts[-1]); pts = new
    return pts

def wfun_chain(bones, per, width=0.12):
    nseg = len(bones)
    def f(i, n):
        s = i / (n - 1) * nseg  # in segment units
        idx = int(min(s, nseg - 1e-6))
        # blend near joints
        res = {}
        for j in range(1, nseg):
            if abs(s - j) < width * nseg:
                t = (s - (j - width * nseg)) / (2 * width * nseg)
                t = t * t * (3 - 2 * t)
                return {bones[j - 1]: 1 - t, bones[j]: t}
        return {bones[idx]: 1.0}
    return f

def tube(pts, radii, mat, wf, sides=12, ell=(1, 1), lobes=0, amp=0.0, tw=0.0, cap_start=False, cap_end=True,
         smooth=True, uvs=UVS, noise=0.0, ph=0.0):
    fr = frames(pts)
    n = len(pts)
    rings = []
    length = 0.0
    lens = [0.0]
    for i in range(1, n):
        lens.append(lens[-1] + (pts[i] - pts[i - 1]).length)
    for i, (p, (t, nn, bn)) in enumerate(zip(pts, fr)):
        ring = []
        w = wf(i, n)
        for j in range(sides):
            ang = j / sides * math.tau
            r = radii[i] * (1 + amp * math.sin(lobes * ang + tw * lens[i] + ph) + random.uniform(-noise, noise))
            co = p + nn * (math.cos(ang) * r * ell[0]) + bn * (math.sin(ang) * r * ell[1])
            v = bm.verts.new(co)
            setw(v, w)
            ring.append(v)
        rings.append(ring)
    mi = MATS.index(mat)
    circ = 2 * math.pi * (sum(radii) / n) * (ell[0] + ell[1]) / 2
    allv = [v for r in rings for v in r]
    for i in range(n - 1):
        for j in range(sides):
            j2 = (j + 1) % sides
            f = bm.faces.new([rings[i][j], rings[i][j2], rings[i + 1][j2], rings[i + 1][j]])
            f.material_index = mi; f.smooth = smooth
            u0 = j / sides * circ * uvs * 1.0; u1 = (j + 1) / sides * circ * uvs
            v0 = lens[i] * uvs; v1 = lens[i + 1] * uvs
            for l, uv in zip(f.loops, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]):
                l[uvl].uv = uv
    for flag, ring, idx in ((cap_start, rings[0], 0), (cap_end, rings[-1], n - 1)):
        if flag:
            f = bm.faces.new(list(reversed(ring)) if idx == 0 else ring)
            f.material_index = mi; f.smooth = smooth
            for l in f.loops:
                c = l.vert.co
                l[uvl].uv = (c.x * uvs, c.y * uvs)
    bm.normal_update()
    return fr

def strands(pts, radii, count, turns, tr, wf, mat='bark', phase=0.0, sides=6, off=0.92):
    fr = frames(pts)
    n = len(pts)
    for k in range(count):
        ph = phase + k / count * math.tau
        sp = []
        for i, (p, (t, nn, bn)) in enumerate(zip(pts, fr)):
            a = ph + turns * math.tau * i / (n - 1)
            sp.append(p + (nn * math.cos(a) + bn * math.sin(a)) * radii[i] * off)
        rr = [tr * (1 - 0.35 * abs(2 * i / (n - 1) - 1)) for i in range(n)]
        tube(sp, rr, mat, wf, sides=sides, cap_start=True, cap_end=True, noise=0.05)

def curved_tube(pts, r0, r1, mat, w, sides=8, taper=1.0, subdiv=6, uvs=UVS, tip=0.012):
    # smooth through pts with Catmull-Rom-ish subdivision
    P = []
    for i in range(len(pts) - 1):
        p0 = pts[max(i - 1, 0)]; p1 = pts[i]; p2 = pts[i + 1]; p3 = pts[min(i + 2, len(pts) - 1)]
        for k in range(subdiv):
            t = k / subdiv
            P.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    P.append(pts[-1])
    n = len(P)
    R = [max(tip, r0 + (r1 - r0) * (i / (n - 1)) ** taper) for i in range(n)]
    tube(P, R, mat, lambda i, nn: w, sides=sides, cap_start=True, cap_end=True, uvs=uvs)
    return P

# ---------------------------------------------------------------- torso
def torso():
    jn = [J['pelvis'] + V(0, 0, -0.1), J['spine'], J['chest'] + V(0, 0, 0.1), J['chest_top'] + V(0, 0, 0.1)]
    pts = sample_chain(jn, 7, 4)
    n = len(pts)
    radii = []
    for i in range(n):
        s = i / (n - 1)
        radii.append(0.62 + 0.38 * math.sin(min(s * 1.25, 1) * math.pi * 0.62) + 0.1 * s)
    wf = wfun_chain(['pelvis', 'spine', 'chest'], 7, 0.15)
    # three-seg wf needs 3 bones but chain has 3 segments -> ok
    tube(pts, radii, 'bark', wf, sides=20, ell=(1.25, 0.85), lobes=5, amp=0.06, tw=2.5, cap_start=True, cap_end=True)
    strands(pts, radii, 6, 1.3, 0.14, wf)
    # hips
    blob(J['pelvis'] + V(0, 0.05, -0.1), (0.9, 0.62, 0.5), 'bark', {'pelvis': 1}, [0, 0, 0], 0.08, 3, True)
    # neck
    npts = sample_chain([J['chest_top'] + V(0, 0, 0.0), J['neck'] + V(0, -0.05, 0.1), J['head'] + V(0, 0, -0.05)], 4, 2)
    nr = [0.42 - 0.08 * i / (len(npts) - 1) for i in range(len(npts))]
    tube(npts, nr, 'bark', wfun_chain(['chest', 'neck'], 4, 0.2), sides=14, lobes=4, amp=0.08, tw=3, cap_end=True)
    strands(npts, nr, 4, 1.2, 0.09, wfun_chain(['chest', 'neck'], 4, 0.2))
    c = {'chest': 1}
    # shoulder boulders (big stone masses)
    for n_, s in SIDES.items():
        k = 1.15 if n_ == 'L' else 1.0
        stone(V(s * 1.25, -0.15, 3.8), (0.88 * k, 0.75 * k, 0.55 * k), {'shoulder.' + n_: 1}, 1.0, [8, s * -10, s * 20], 0.18, 1)
        stone(V(s * 1.55, -0.1, 3.35), (0.55, 0.6, 0.45), {'shoulder.' + n_: 1}, 0.8)
        shelf(V(s * 1.7, -0.5, 3.7), 0.26, {'shoulder.' + n_: 1}, 3)
    # back hump
    stone(V(0.2, 0.5, 3.9), (0.8, 0.6, 0.55), c, 1.0)
    stone(V(-0.45, 0.45, 3.5), (0.55, 0.5, 0.65), c, 0.9)
    stone(V(0.0, 0.55, 3.3), (0.7, 0.4, 0.7), c, 0.6)
    # chest plates
    stone(V(0.0, -0.78, 3.35), (0.75, 0.3, 0.52), c, 0.7, [20, 0, 5])
    stone(V(-0.55, -0.62, 3.05), (0.45, 0.28, 0.45), c, 0.5, [10, 15, 20])
    stone(V(0.55, -0.62, 3.0), (0.45, 0.28, 0.5), c, 0.5, [15, -15, -10])
    stone(V(0.0, -0.68, 2.65), (0.5, 0.25, 0.4), {'spine': 1}, 0.5, [15, 0, 0])
    stone(V(0.5, -0.5, 2.3), (0.4, 0.25, 0.3), {'spine': 1}, 0.4)
    stone(V(-0.45, -0.5, 2.35), (0.4, 0.25, 0.32), {'spine': 1}, 0.4)
    stone(V(0.0, 0.45, 2.5), (0.65, 0.35, 0.5), {'spine': 1}, 0.5)
    stone(V(0.0, -0.55, 2.0), (0.55, 0.3, 0.3), {'pelvis': 1}, 0.4)
    # head
    h = {'head': 1}
    stone(V(0, -0.78, 3.97), (0.42, 0.42, 0.5), h, 0.5, [-10, 0, 10], 0.15)
    stone(V(0, -1.02, 3.72), (0.25, 0.3, 0.5), h, 0.0, [-25, 0, 0], 0.12)
    stone(V(0.0, -0.88, 4.3), (0.4, 0.3, 0.2), h, 0.9, [-15, 0, 0])
    stone(V(0.38, -0.8, 4.0), (0.2, 0.3, 0.4), h, 0.4)
    stone(V(-0.38, -0.8, 3.95), (0.2, 0.3, 0.4), h, 0.4)
    # eyes
    for s in (1, -1):
        blob(V(s * 0.16, -1.1, 4.0), (0.09, 0.05, 0.06), 'eye', h, [0, 0, s * -15], 0.0, 2, True)
    # antlers
    def antler(s):
        base = V(s * 0.3, -0.7, 4.15)
        main = [base, V(s * 0.65, -0.62, 4.3), V(s * 1.05, -0.5, 4.5), V(s * 1.35, -0.45, 4.8), V(s * 1.45, -0.5, 5.0)]
        curved_tube(main, 0.14, 0.03, 'bark', h, sides=10, taper=0.8)
        for pts_ in ([V(s * .7, -.62, 4.33), V(s * .65, -.7, 4.65), V(s * .55, -.75, 4.95)],
                     [V(s * 1.0, -.52, 4.47), V(s * 1.0, -.4, 4.8), V(s * 0.85, -.35, 5.0)],
                     [V(s * 1.2, -.47, 4.62), V(s * 1.7, -.4, 4.65), V(s * 1.95, -.4, 4.9)],
                     [V(s * 1.35, -.45, 4.8), V(s * 1.15, -.5, 5.0), V(s * 1.1, -.55, 5.15)]):
            curved_tube(pts_, 0.075, 0.015, 'bark', h, sides=8, taper=0.9, subdiv=4)
        blob(V(s * 1.05, -0.5, 4.58), (0.12, 0.12, 0.07), 'moss', h, None, 0.3, 1, True)
        blob(V(s * 1.45, -0.5, 4.95), (0.1, 0.1, 0.07), 'moss', h, None, 0.3, 1, True)
    antler(1); antler(-1)

# ---------------------------------------------------------------- limbs
def arm(n):
    s = SIDES[n]
    joints = [J['shoulder' + n] + V(0, 0, 0.05), J['elbow' + n], J['wrist' + n] + V(0, -0.05, 0.0)]
    pts = sample_chain(joints, 9, 3)
    m = len(pts)
    radii = []
    for i in range(m):
        t = i / (m - 1)
        radii.append(0.52 - 0.12 * t + 0.08 * math.sin(t * math.pi * 2) ** 2 + (0.0 if t < 0.85 else -0.04))
    bones = ['upper_arm.' + n, 'forearm.' + n]
    wf = wfun_chain(bones, 9, 0.12)
    tube(pts, radii, 'bark', wf, sides=14, lobes=4, amp=0.09, tw=4, cap_end=True)
    strands(pts, radii, 5, 1.6, 0.11, wf, phase=0.5 * s)
    # elbow joint blob
    blob(J['elbow' + n], (0.34, 0.34, 0.34), 'bark', {'upper_arm.' + n: 0.5, 'forearm.' + n: 0.5}, [0, 0, 0], 0.08, 2, True)
    # hand mass
    hw = {'hand.' + n: 1}
    blob(J['wrist' + n] + V(0, -0.1, -0.2), (0.34, 0.4, 0.38), 'bark', hw, [0, 0, 0], 0.1, 2, True)
    # armor on arm
    ua = {'upper_arm.' + n: 1}
    fa = {'forearm.' + n: 1}
    stone(V(s * 1.95, -0.1, 2.8), (0.38, 0.55, 0.6), ua, 0.9, [0, 0, s * 15])
    stone(V(s * 2.0, -0.35, 1.7), (0.4, 0.62, 0.9), fa, 0.9, [5, 0, s * 10])
    stone(V(s * 1.95, -0.62, 1.15), (0.34, 0.5, 0.5), fa, 0.6)
    shelf(V(s * 2.2, -0.45, 2.2), 0.24, ua, 4, V(0, 0, 1))
    # claws
    for k, off in enumerate((-0.28, 0.0, 0.28)):
        base = J['wrist' + n] + V(off * 1.1, -0.2, -0.3)
        pts_ = [base, base + V(off * 0.1, -0.15, -0.25), base + V(off * 0.0, -0.3, -0.55), base + V(0, -0.28, -0.82)]
        curved_tube(pts_, 0.13, 0.0, 'ivory', hw, sides=8, taper=0.9, subdiv=5)
    # moss drape on fingers
    blob(J['wrist' + n] + V(0, -0.25, -0.2), (0.3, 0.25, 0.12), 'moss', hw, None, 0.3, 1, True)

def leg(n):
    s = SIDES[n]
    joints = [J['hip' + n] + V(0, 0, 0.1), J['knee' + n], J['ankle' + n] + V(0, 0, 0.1)]
    pts = sample_chain(joints, 9, 3)
    m = len(pts)
    radii = [0.58 - 0.17 * (i / (m - 1)) + 0.05 * math.sin(i / (m - 1) * math.pi) for i in range(m)]
    bones = ['thigh.' + n, 'shin.' + n]
    wf = wfun_chain(bones, 9, 0.12)
    tube(pts, radii, 'bark', wf, sides=14, lobes=4, amp=0.09, tw=4, cap_end=True, cap_start=True)
    strands(pts, radii, 5, 1.5, 0.12, wf, phase=1.0)
    blob(J['knee' + n], (0.4, 0.4, 0.4), 'bark', {'thigh.' + n: 0.5, 'shin.' + n: 0.5}, [0, 0, 0], 0.08, 2, True)
    th = {'thigh.' + n: 1}; sh = {'shin.' + n: 1}; ft = {'foot.' + n: 1}
    stone(V(s * 1.1, 0.15, 1.9), (0.4, 0.55, 0.65), th, 0.8)
    stone(V(s * 0.85, -0.5, 1.5), (0.45, 0.35, 0.5), th, 0.7)
    stone(V(s * 0.8, -0.78, 1.05), (0.42, 0.32, 0.5), sh, 0.5, [10, 0, 0])
    stone(V(s * 1.1, -0.2, 0.9), (0.32, 0.45, 0.6), sh, 0.8)
    # foot stones
    blob(J['ankle' + n] + V(0, -0.1, -0.1), (0.4, 0.45, 0.3), 'bark', ft, [0, 0, 0], 0.08, 2, True)
    stone(V(s * 0.76, 0.2, 0.28), (0.4, 0.35, 0.3), ft, 0.8, [0, 0, 10])
    stone(V(s * 0.76, -0.2, 0.22), (0.45, 0.4, 0.26), ft, 0.8, [0, 0, 10])
    for dx, dy, sz in ((-0.3, -0.62, 0.22), (0.0, -0.75, 0.26), (0.3, -0.62, 0.22)):
        stone(V(s * 0.76 + dx, dy, sz * 0.78), (0.2, 0.28, sz), ft, 0.5, [0, 0, dx * 40])

torso()
for n in 'LR':
    arm(n); leg(n)

# lower fix: ensure ground; compute min z
minz = min(v.co.z for v in bm.verts)
maxz = max(v.co.z for v in bm.verts)
print("MESH minz", minz, "maxz", maxz)
for v in bm.verts:
    v.co.z -= minz
DZ = V(0, 0, -minz)

me = bpy.data.meshes.new('WardenMesh')
bm.to_mesh(me)
me.update()
obj = bpy.data.objects.new('Warden', me)
scene.collection.objects.link(obj)
for name in BONE_NAMES:
    obj.vertex_groups.new(name=name)

# ---------------------------------------------------------------- materials
def load(path, nc=False):
    img = bpy.data.images.load(path)
    img.colorspace_settings.name = 'Non-Color' if nc else 'sRGB'
    img.pack()
    return img

def mk(name, uvscale=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL' and n.type != 'BSDF_PRINCIPLED':
            nt.nodes.remove(n)
    bsdf = nt.nodes['Principled BSDF']
    ext = {'stone': 'jpg', 'bark': 'jpg', 'moss': 'png', 'ivory': 'jpg'}[name]
    def tex(fn, nc, loc):
        t = nt.nodes.new('ShaderNodeTexImage')
        t.image = load(os.path.join(TEX, fn), nc)
        t.location = loc
        t.extension = 'REPEAT'
        return t
    a = tex(f'{name}-albedo.{ext}', False, (-600, 300))
    r = tex(f'{name}-roughness.png', True, (-600, 0))
    nm = tex(f'{name}-normal.png', True, (-900, -300))
    nmap = nt.nodes.new('ShaderNodeNormalMap'); nmap.location = (-300, -300)
    nmap.inputs['Strength'].default_value = 1.0
    nt.links.new(a.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(r.outputs['Color'], bsdf.inputs['Roughness'])
    nt.links.new(nm.outputs['Color'], nmap.inputs['Color'])
    nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Metallic'].default_value = 0.0
    return m

for name in MATS:
    if name == 'eye':
        m = bpy.data.materials.new('eye'); m.use_nodes = True
        b = m.node_tree.nodes['Principled BSDF']
        b.inputs['Base Color'].default_value = (1.0, 0.55, 0.05, 1)
        b.inputs['Emission Color'].default_value = (1.0, 0.5, 0.05, 1)
        b.inputs['Emission Strength'].default_value = 6.0
        b.inputs['Roughness'].default_value = 0.2
    else:
        m = mk(name)
    obj.data.materials.append(m)

# ---------------------------------------------------------------- armature
arm_data = bpy.data.armatures.new('WardenRig')
arm_obj = bpy.data.objects.new('WardenRig', arm_data)
scene.collection.objects.link(arm_obj)
bpy.context.view_layer.objects.active = arm_obj
arm_obj.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for name, (h, t, p) in BONE_DEFS.items():
    eb = arm_data.edit_bones.new(name)
    eb.head = h + DZ; eb.tail = t + DZ
    if name == 'root':
        eb.head = V(0, 0.25, 0); eb.tail = V(0, 0.25, 0.5)
for name, (h, t, p) in BONE_DEFS.items():
    if p:
        eb = arm_data.edit_bones[name]
        eb.parent = arm_data.edit_bones[p]
        # connect hierarchy visually where heads coincide
        if (eb.head - eb.parent.tail).length < 1e-4: eb.use_connect = True
bpy.ops.object.mode_set(mode='OBJECT')

obj.parent = arm_obj
mod = obj.modifiers.new('Armature', 'ARMATURE')
mod.object = arm_obj

# uniform scale to bring antler tips to ~5 m
for o in (obj, arm_obj):
    o.scale = (0.95, 0.95, 0.95)
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True); arm_obj.select_set(True)
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
# ---------------------------------------------------------------- animation
scene.render.fps = 25
scene.frame_start = 0
scene.frame_end = 30
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='POSE')
act = bpy.data.actions.new('attack')
arm_obj.animation_data_create()
arm_obj.animation_data.action = act
for pb in arm_obj.pose.bones:
    pb.rotation_mode = 'QUATERNION'

def R(*deg): return Euler([math.radians(a) for a in deg], 'XYZ')

# world-axis rotations (deg, XYZ order) per bone per key frame. R arm (-X side) does the slash.
POSES = {
    0: {},
    9: {   # anticipation: coil back, raise arm
        'spine': R(-8, 0, 14), 'chest': R(-10, 0, 22), 'head': R(6, 0, -10),
        'shoulder.R': R(-10, 0, 0),
        'upper_arm.R': R(172, 0, -25), 'forearm.R': R(-20, 0, 0), 'hand.R': R(-15, 0, 0),
        'upper_arm.L': R(-12, 0, -8), 'pelvis': R(0, 0, 6),
    },
    14: {  # impact: heavy downward sweep
        'spine': R(14, 0, -18), 'chest': R(18, 0, -30), 'head': R(-10, 0, 14),
        'shoulder.R': R(12, 0, 0),
        'upper_arm.R': R(-32, 0, 20), 'forearm.R': R(-35, 0, 0), 'hand.R': R(-20, 0, 0),
        'upper_arm.L': R(12, 0, 6), 'pelvis': R(8, 0, -8),
    },
    18: {  # follow through
        'spine': R(10, 0, -13), 'chest': R(13, 0, -22), 'head': R(-6, 0, 9),
        'shoulder.R': R(8, 0, 0),
        'upper_arm.R': R(-26, 0, 16), 'forearm.R': R(-28, 0, 0), 'hand.R': R(-12, 0, 0),
        'upper_arm.L': R(9, 0, 4), 'pelvis': R(6, 0, -6),
    },
    30: {},
}

def key_pose(frame, d):
    for pb in arm_obj.pose.bones:
        e = d.get(pb.name)
        if e is None:
            q = Matrix.Identity(3).to_quaternion()
        else:
            Rrest = pb.bone.matrix_local.to_3x3()
            q = (Rrest.inverted() @ e.to_matrix() @ Rrest).to_quaternion()
        pb.rotation_quaternion = q
        pb.keyframe_insert('rotation_quaternion', frame=frame)

for f, d in POSES.items():
    key_pose(f, d)
bpy.ops.object.mode_set(mode='OBJECT')
# smooth interpolation
for fc in act.fcurves if hasattr(act, 'fcurves') else []:
    for kp in fc.keyframe_points:
        kp.interpolation = 'BEZIER'
act.use_fake_user = False
arm_obj.animation_data.action = act
# make sure the actions list only has attack
for a in list(bpy.data.actions):
    if a.name != 'attack': bpy.data.actions.remove(a)

# ---------------------------------------------------------------- export
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True); arm_obj.select_set(True)
bpy.context.view_layer.objects.active = arm_obj
out = os.path.join(OUT, 'monster.glb')
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True, export_animations=True,
                          export_apply=False, export_yup=True, export_skins=True, export_image_format='AUTO')
print("EXPORTED", out, os.path.getsize(out))
print("TRIS", len(me.polygons), "VERTS", len(me.vertices))
