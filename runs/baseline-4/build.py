import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Euler, Quaternion

OUT = r"C:\Users\aaron\skill-glb-creator-claude-demo\runs\baseline-4\monster.glb"
TEX = r"C:\Users\aaron\skill-glb-creator-claude-demo\assets\textures"
random.seed(11)
V = Vector

bpy.ops.wm.read_factory_settings(use_empty=True)

# ---------------------------------------------------------------- bones
# name, parent, head, tail   (Blender Z-up, creature faces -Y)
B = []
def bone(n, p, h, t): B.append((n, p, V(h), V(t)))
bone('root', None, (0, 0, 0), (0, 0, 0.3))
bone('pelvis', 'root', (0, 0, 2.0), (0, 0, 2.4))
bone('spine', 'pelvis', (0, 0, 2.4), (0, -0.1, 2.9))
bone('chest', 'spine', (0, -0.1, 2.9), (0, -0.2, 3.5))
bone('neck', 'chest', (0, -0.2, 3.5), (0, -0.5, 3.85))
bone('head', 'neck', (0, -0.5, 3.85), (0, -0.7, 4.4))
for s, sn in ((1, 'R'), (-1, 'L')):
    bone('clavicle_' + sn, 'chest', (s * 0.3, -0.2, 3.4), (s * 1.3, -0.1, 3.4))
    bone('upper_arm_' + sn, 'clavicle_' + sn, (s * 1.3, -0.1, 3.4), (s * 1.75, -0.35, 2.3))
    bone('forearm_' + sn, 'upper_arm_' + sn, (s * 1.75, -0.35, 2.3), (s * 1.65, -0.8, 1.25))
    bone('hand_' + sn, 'forearm_' + sn, (s * 1.65, -0.8, 1.25), (s * 1.6, -1.0, 0.8))
    bone('thigh_' + sn, 'pelvis', (s * 0.6, 0, 2.1), (s * 0.7, -0.45, 1.15))
    bone('shin_' + sn, 'thigh_' + sn, (s * 0.7, -0.45, 1.15), (s * 0.65, -0.1, 0.35))
    bone('foot_' + sn, 'shin_' + sn, (s * 0.65, -0.1, 0.35), (s * 0.65, -0.65, 0.12))
BN = [b[0] for b in B]
BD = {b[0]: b for b in B}

# ---------------------------------------------------------------- mesh helpers
bm = bmesh.new()
dl = bm.verts.layers.deform.verify()
uvl = bm.loops.layers.uv.verify()
ST, BK, MS, IV, AM = 0, 1, 2, 3, 4

def seg_dist(p, a, b):
    ab = b - a
    t = max(0, min(1, (p - a).dot(ab) / max(ab.length_squared, 1e-9)))
    return (p - (a + ab * t)).length

def set_w(v, chain=None, rigid=None):
    if rigid:
        v[dl][BN.index(rigid)] = 1.0
        return
    ds = sorted(((seg_dist(v.co, BD[n][2], BD[n][3]), n) for n in chain))[:2]
    ws = [1.0 / (d + 0.08) ** 3 for d, _ in ds]
    tot = sum(ws)
    for (d, n), w in zip(ds, ws):
        v[dl][BN.index(n)] = w / tot

def catmull(pts, per=8):
    out = []
    P = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(per):
            t = k / per
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(V(pts[-1]))
    return out

def prof(pr, t):
    for (t0, r0), (t1, r1) in zip(pr, pr[1:]):
        if t <= t1:
            return r0 + (r1 - r0) * (t - t0) / max(t1 - t0, 1e-9)
    return pr[-1][1]

def frames(pts):
    n = len(pts)
    Ts = [(pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized() for i in range(n)]
    ref = V((0, 1, 0)) if abs(Ts[0].y) < 0.9 else V((1, 0, 0))
    N = Ts[0].cross(ref).normalized()
    out = []
    for T in Ts:
        N = (N - T * N.dot(T)).normalized()
        out.append((T, N, T.cross(N)))
    return out

def tube(pts, radii, sides=8, mat=BK, chain=None, rigid=None, uvs=(1.0, 1.0), smooth=True, twist=0.0, cap=True):
    fr = frames(pts)
    rings = []
    L = 0.0
    lens = [0.0]
    for i in range(1, len(pts)):
        L += (pts[i] - pts[i - 1]).length
        lens.append(L)
    for i, p in enumerate(pts):
        T, N, Bn = fr[i]
        ring = []
        for j in range(sides):
            a = 2 * math.pi * j / sides + twist * i
            v = bm.verts.new(p + (N * math.cos(a) + Bn * math.sin(a)) * radii[i])
            set_w(v, chain, rigid)
            ring.append(v)
        rings.append(ring)
    for i in range(len(pts) - 1):
        for j in range(sides):
            j2 = (j + 1) % sides
            vs = [rings[i][j], rings[i][j2], rings[i + 1][j2], rings[i + 1][j]]
            try:
                f = bm.faces.new(vs)
            except ValueError:
                continue
            f.material_index = mat
            f.smooth = smooth
            us = [j / sides * uvs[0], (j + 1) / sides * uvs[0]]
            vv = [lens[i] * uvs[1], lens[i + 1] * uvs[1]]
            for lp, (u, v_) in zip(f.loops, [(us[0], vv[0]), (us[1], vv[0]), (us[1], vv[1]), (us[0], vv[1])]):
                lp[uvl].uv = (u, v_)
    if cap:
        for ring in (rings[0], rings[-1][::-1]):
            try:
                f = bm.faces.new(ring)
                f.material_index = mat
                f.smooth = smooth
                for k, lp in enumerate(f.loops):
                    lp[uvl].uv = (0.5 + 0.3 * math.cos(k), 0.5 + 0.3 * math.sin(k))
            except ValueError:
                pass

def box_uv(faces, scale=0.55):
    for f in faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for lp in f.loops:
            c = lp.vert.co
            u, v = [(c.y, c.z), (c.x, c.z), (c.x, c.y)][ax]
            lp[uvl].uv = (u * scale, v * scale)

def blob(c, size, rot=(0, 0, 0), bone='chest', kind='ico', jit=0.2, mat=ST, subdiv=1, flat=True, chain=None):
    if kind == 'ico':
        r = bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
    elif kind == 'uv':
        r = bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=1.0)
    else:
        r = bmesh.ops.create_cube(bm, size=2.0)
    vs = r['verts']
    M = Euler([math.radians(a) for a in rot]).to_matrix()
    for v in vs:
        co = V((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
        if jit:
            co = co * V([1 + random.uniform(-jit, jit) for _ in range(3)])
        v.co = M @ co + V(c)
        if chain:
            set_w(v, chain=chain)
        else:
            set_w(v, rigid=bone)
    fs = {f for v in vs for f in v.link_faces}
    bm.normal_update()
    for f in fs:
        f.material_index = mat
        f.smooth = not flat
    box_uv(fs, 0.55 if mat == ST else 1.2)
    return fs

def rock(c, size, rot=(0, 0, 0), bone='chest', kind='cube', moss=0.0, jit=0.3):
    size = tuple(x * 0.95 for x in size)
    kind = random.choice(['cube', 'ico', 'cube'])
    blob(c, size, tuple(r + random.uniform(-12, 12) for r in rot), bone, kind, jit=jit, mat=ST)
    if moss > 0:
        M = Euler([math.radians(a) for a in rot]).to_matrix()
        top = V(c) + M @ V((random.uniform(-.2, .2) * size[0], random.uniform(-.2, .2) * size[1], size[2] * 0.85))
        blob(top, (size[0] * moss * 0.6, size[1] * moss * 0.6, size[2] * 0.18 + 0.03), rot, bone, 'ico', jit=0.25, mat=MS, subdiv=2, flat=False)

def shelf(c, r, rot, bone, n=3):
    M = Euler([math.radians(a) for a in rot]).to_matrix()
    for i in range(n):
        off = M @ V((0.02 * i, 0, 0.13 * i))
        rr = r * (1 - 0.18 * i)
        blob(V(c) + off, (rr, rr * 0.9, 0.05), rot, bone, 'uv', jit=0.05, mat=IV, flat=False)

def claw(base, direction, length, curl, bone, r0=0.075):
    d = V(direction).normalized()
    side = d.cross(V((0, 0, 1)))
    side = side.normalized() if side.length > 1e-3 else V((1, 0, 0))
    up = V((0, 0, 1))
    pts = []
    for k in range(9):
        t = k / 8
        # curve inward/down
        p = V(base) + d * length * t + up * (-curl * t * t * length) + side * 0
        pts.append(p)
    radii = [r0 * (1 - t / 8) ** 0.8 + 0.004 for t in range(9)]
    tube(pts, radii, sides=7, mat=IV, rigid=bone, uvs=(1.0, 1.0))

def braided(pts, prof_r, chain, n=4, turns=1.5, sr=0.1, core=0.85, per=8):
    path = catmull(pts, per)
    n_ = len(path)
    rad = [prof(prof_r, i / (n_ - 1)) for i in range(n_)]
    tube(path, [r * core for r in rad], sides=10, mat=BK, chain=chain, uvs=(2, 0.8))
    fr = frames(path)
    for sgn in (1, -1):
        for k in range(n):
            a0 = 2 * math.pi * k / n + (0.5 if sgn < 0 else 0)
            sp = []
            for i in range(n_):
                T, N, Bn = fr[i]
                a = a0 + sgn * turns * 2 * math.pi * i / (n_ - 1)
                sp.append(path[i] + (N * math.cos(a) + Bn * math.sin(a)) * rad[i] * 0.78)
            tube(sp, [sr * (0.8 + 0.4 * rad[i] / max(rad)) for i in range(n_)], sides=6, mat=BK, chain=chain, uvs=(1, 1.5), cap=True)

# ---------------------------------------------------------------- torso
for z0, z1 in ((2.0, 3.6),):
    for k in range(14):
        a0 = 2 * math.pi * k / 14
        sp = []
        for i in range(14):
            t = i / 13
            z = z0 + (z1 - z0) * t
            ax = 0.55 + 0.35 * math.sin(t * 2.4) + 0.25 * t
            ay = 0.45 + 0.15 * math.sin(t * 2.4)
            a = a0 + 1.6 * math.sin(t * 3.0) * (1 if k % 2 else -1)
            sp.append(V((ax * math.cos(a), -0.12 - 0.08 * t + ay * math.sin(a), z)))
        tube(sp, [0.2 + 0.04 * math.sin(i) for i in range(14)], sides=6, mat=BK, chain=['pelvis', 'spine', 'chest'], uvs=(1, 1.5))
blob((0, -0.12, 3.05), (0.95, 0.7, 0.9), bone='spine', kind='uv', jit=0.04, mat=BK, flat=False, chain=['pelvis', 'spine', 'chest'])
blob((0, 0.0, 2.2), (0.85, 0.6, 0.5), bone='pelvis', kind='uv', jit=0.04, mat=BK, flat=False)
# neck + head core
braided([V((0, -0.2, 3.4)), V((0, -0.4, 3.65)), V((0, -0.55, 3.9))], [(0, 0.3), (1, 0.28)], ['chest', 'neck', 'head'], n=3, turns=1, sr=0.08)
blob((0, -0.62, 4.05), (0.34, 0.36, 0.38), bone='head', kind='uv', jit=0.03, mat=BK, flat=False)

# ---------------------------------------------------------------- limbs
for s, sn in ((1, 'R'), (-1, 'L')):
    ua, fa, ha = 'upper_arm_' + sn, 'forearm_' + sn, 'hand_' + sn
    chain = ['clavicle_' + sn, ua, fa, ha]
    pts = [V((s * 0.5, -0.2, 3.4)), V((s * 1.3, -0.1, 3.4)), V((s * 1.75, -0.35, 2.3)), V((s * 1.65, -0.8, 1.25)), V((s * 1.6, -1.0, 0.85))]
    braided(pts, [(0, 0.5), (0.3, 0.42), (0.55, 0.33), (0.8, 0.36), (1, 0.28)], chain, n=5, turns=1.6, sr=0.15)
    # hands: palm + claws
    blob((s * 1.6, -1.0, 0.8), (0.28, 0.28, 0.25), bone=ha, kind='uv', jit=0.05, mat=BK, flat=False)
    for off, dyaw in ((-0.2, -0.25), (0.0, 0.0), (0.2, 0.25)):
        base = V((s * 1.6 + off, -1.05, 0.78))
        claw(base, V((s * dyaw * 0.4, -0.55, -0.9)), 0.8, 0.0, ha)
    claw(V((s * 1.6 - s * 0.3, -0.9, 0.9)), V((-s * 0.3, -0.7, -0.5)), 0.55, 0.0, ha, 0.06)
    # legs
    th, sh, ft = 'thigh_' + sn, 'shin_' + sn, 'foot_' + sn
    lp = [V((s * 0.6, 0, 2.2)), V((s * 0.7, -0.45, 1.15)), V((s * 0.65, -0.1, 0.35)), V((s * 0.65, -0.35, 0.2))]
    braided(lp, [(0, 0.5), (0.35, 0.42), (0.6, 0.3), (1, 0.3)], [th, sh, ft], n=5, turns=1.4, sr=0.14)

# ---------------------------------------------------------------- stone armour
def chain_of(n):
    return n
# big shoulder masses (asymmetric like reference)
rock((1.65, -0.05, 3.7), (0.75, 0.7, 0.55), (8, -10, 20), 'clavicle_R', moss=0.9)
rock((1.9, 0.0, 3.5), (0.45, 0.5, 0.45), (-20, 15, 5), 'upper_arm_R', moss=0.8)
rock((1.0, 0.3, 3.8), (0.5, 0.45, 0.4), (15, 5, -25), 'chest', moss=0.8)
rock((-1.6, 0.0, 3.55), (0.65, 0.6, 0.5), (-5, 12, -20), 'clavicle_L', moss=0.9)
rock((-1.8, 0.15, 3.35), (0.4, 0.55, 0.55), (10, -20, 10), 'upper_arm_L', moss=0.7)
rock((-1.2, -0.35, 3.8), (0.3, 0.3, 0.35), (30, 10, 10), 'clavicle_L')
# chest plates
rock((0.45, -0.7, 3.2), (0.55, 0.16, 0.5), (-10, 10, 20), 'chest', moss=0.8)
rock((-0.45, -0.72, 3.15), (0.5, 0.16, 0.55), (-5, -15, -20), 'chest', moss=0.7)
rock((0.0, -0.78, 2.7), (0.55, 0.16, 0.38), (15, 0, 0), 'spine', moss=0.6)
rock((0.9, -0.5, 3.5), (0.35, 0.2, 0.5), (0, -25, 30), 'chest')
rock((-0.9, -0.5, 3.45), (0.35, 0.2, 0.5), (0, 25, -30), 'chest')
rock((0.0, -0.55, 3.6), (0.5, 0.2, 0.3), (-30, 0, 0), 'chest')
# back plates
rock((0.0, 0.6, 3.3), (0.8, 0.22, 0.7), (-8, 0, 5), 'chest', moss=0.9)
rock((0.5, 0.5, 2.6), (0.45, 0.2, 0.5), (10, 10, 10), 'spine', moss=0.6)
rock((-0.5, 0.5, 2.7), (0.4, 0.2, 0.45), (10, -10, -15), 'spine')
rock((0.0, 0.6, 3.8), (0.5, 0.28, 0.3), (-20, 0, 0), 'chest')
# pelvis
rock((0, -0.45, 2.15), (0.5, 0.2, 0.3), (10, 0, 0), 'pelvis')
rock((0.65, 0.05, 2.3), (0.3, 0.3, 0.3), (0, 0, 30), 'pelvis')
rock((-0.65, 0.05, 2.3), (0.3, 0.3, 0.3), (0, 0, -30), 'pelvis')
for s, sn in ((1, 'R'), (-1, 'L')):
    ua, fa, ha = 'upper_arm_' + sn, 'forearm_' + sn, 'hand_' + sn
    # forearm gauntlet
    rock((s * 1.95, -0.5, 1.85), (0.3, 0.38, 0.55), (-10, s * 10, s * 8), fa, moss=0.7)
    rock((s * 1.9, -0.85, 1.4), (0.35, 0.3, 0.45), (15, -s * 15, 0), fa)
    rock((s * 1.5, -0.55, 1.7), (0.22, 0.3, 0.4), (5, s * 10, 0), fa)
    rock((s * 1.65, -0.55, 2.35), (0.3, 0.3, 0.35), (0, 0, s * 20), ua, moss=0.7)
    rock((s * 1.75, -0.95, 1.05), (0.28, 0.25, 0.25), (0, 0, 20), ha)
    rock((s * 1.75, -0.7, 1.0), (0.22, 0.3, 0.25), (0, 0, 20), ha)
    # thigh / knee / shin
    rock((s * 0.95, -0.2, 1.75), (0.3, 0.35, 0.5), (0, s * 10, 0), 'thigh_' + sn, moss=0.8)
    rock((s * 0.45, -0.3, 1.7), (0.22, 0.3, 0.45), (0, 0, 0), 'thigh_' + sn)
    rock((s * 0.72, -0.85, 1.2), (0.38, 0.28, 0.35), (-15, 0, 10 * s), 'thigh_' + sn, moss=0.7)
    rock((s * 0.85, -0.3, 0.8), (0.28, 0.35, 0.4), (0, 0, 10), 'shin_' + sn, moss=0.7)
    rock((s * 0.5, -0.1, 0.85), (0.22, 0.3, 0.38), (0, 0, -10), 'shin_' + sn)
    # feet
    fh = 'foot_' + sn
    rock((s * 0.65, -0.05, 0.28), (0.45, 0.5, 0.28), (0, 0, 0), fh, moss=0.8)
    for k, dx in enumerate((-0.28, 0.0, 0.28)):
        rock((s * 0.65 + dx, -0.62, 0.17), (0.2, 0.28, 0.17), (0, 0, dx * 40), fh, moss=0.6)
    rock((s * 0.65, 0.3, 0.2), (0.35, 0.18, 0.2), (0, 0, 0), fh)
    rock((s * 1.0, -0.2, 0.2), (0.2, 0.3, 0.2), (0, 0, 0), fh)


# extra plates cladding limbs and chest (stone coverage)
def plates(bone, n, rad, side, dirs=None, sz=(0.28, 0.22, 0.32), moss=0.7):
    h, t = BD[bone][2], BD[bone][3]
    for i in range(n):
        p = h + (t - h) * ((i + 0.5) / n + random.uniform(-0.08, 0.08))
        a = random.uniform(0, 2 * math.pi)
        off = V((math.cos(a) * rad + side * 0.12, math.sin(a) * rad * 0.9 - 0.05, 0))
        sc_ = random.uniform(0.8, 1.25)
        rock(p + off, tuple(x * sc_ for x in sz), (random.uniform(-25, 25), random.uniform(-25, 25), random.uniform(0, 360)), bone, moss=moss if random.random() < 0.5 else 0)
for s_, sn_ in ((1, 'R'), (-1, 'L')):
    plates('upper_arm_' + sn_, 3, 0.45, s_)
    plates('forearm_' + sn_, 4, 0.4, s_, sz=(0.3, 0.25, 0.35))
    plates('thigh_' + sn_, 4, 0.45, s_)
    plates('shin_' + sn_, 3, 0.38, s_)
plates('chest', 3, 0.7, 0, sz=(0.35, 0.22, 0.3))
plates('spine', 2, 0.65, 0, sz=(0.3, 0.2, 0.28))

# ---------------------------------------------------------------- head
rock((0, -0.62, 4.3), (0.38, 0.42, 0.34), (-10, 0, 0), 'head', moss=0.8)
rock((0.28, -0.55, 4.2), (0.2, 0.3, 0.3), (0, 15, 20), 'head')
rock((-0.28, -0.55, 4.2), (0.2, 0.3, 0.3), (0, -15, -20), 'head')
rock((0, -0.88, 3.95), (0.26, 0.14, 0.4), (-8, 0, 0), 'head')   # mask / snout
rock((0.28, -0.8, 3.95), (0.12, 0.2, 0.28), (0, 10, 0), 'head')
rock((-0.28, -0.8, 3.95), (0.12, 0.2, 0.28), (0, -10, 0), 'head')
rock((0, -0.95, 4.28), (0.3, 0.12, 0.12), (30, 0, 0), 'head')   # brow
# eyes
for s in (1, -1):
    blob((s * 0.16, -0.93, 4.13), (0.055, 0.04, 0.045), bone='head', kind='uv', jit=0, mat=AM, flat=False)
# antlers (bark)
def antler(s, main, branches):
    mp = [V((s * x, y, z - 0.55)) for x, y, z in main]
    path = catmull(mp, 6)
    n = len(path)
    tube(path, [0.075 * (1 - 0.7 * i / (n - 1)) + 0.012 for i in range(n)], sides=7, mat=BK, rigid='head', uvs=(1, 1.5))
    for bi, br in branches:
        st = mp[bi]
        bp = catmull([st] + [V((s * x, y, z - 0.55)) for x, y, z in br], 5)
        m = len(bp)
        tube(bp, [0.05 * (1 - 0.8 * i / (m - 1)) + 0.008 for i in range(m)], sides=6, mat=BK, rigid='head', uvs=(1, 1.5))
    return mp
antler(1, [(0.2, -0.5, 4.4), (0.45, -0.45, 4.7), (0.75, -0.35, 4.85), (1.2, -0.3, 4.75), (1.55, -0.3, 4.95)],
       [(2, [(0.8, -0.3, 5.1), (0.75, -0.25, 5.35)]), (3, [(1.3, -0.35, 4.55), (1.6, -0.4, 4.45)]), (1, [(0.35, -0.6, 5.0), (0.2, -0.7, 5.15)])])
antler(-1, [(0.2, -0.5, 4.4), (0.4, -0.5, 4.75), (0.55, -0.45, 5.0), (0.45, -0.4, 5.25), (0.7, -0.3, 5.45)],
       [(2, [(0.9, -0.4, 5.1), (1.25, -0.45, 5.2)]), (3, [(0.2, -0.35, 5.5), (0.15, -0.3, 5.7)]), (1, [(0.9, -0.5, 4.7), (1.25, -0.55, 4.7)])])
for s in (1, -1):
    for x, y, z in ((0.75, -0.35, 4.85), (1.2, -0.3, 4.75)) if s == 1 else ((0.55, -0.45, 5.0), (0.45, -0.4, 5.25)):
        blob((s * x, y, z - 0.6), (0.08, 0.08, 0.12), bone='head', kind='ico', jit=0.3, mat=MS, subdiv=2, flat=False)

# fungal shelves
shelf((1.2, 0.0, 4.1), 0.2, (0, 25, 0), 'clavicle_R', 4)
shelf((0.55, 0.25, 4.2), 0.16, (0, 20, 0), 'chest', 3)
shelf((1.25, -0.5, 3.0), 0.15, (0, 35, 0), 'upper_arm_R', 3)
shelf((-2.0, -0.1, 3.0), 0.16, (0, -35, 0), 'upper_arm_L', 4)
shelf((-2.25, -0.15, 3.45), 0.14, (0, -25, 0), 'clavicle_L', 3)
shelf((2.0, -0.5, 1.3), 0.14, (0, 35, 0), 'forearm_R', 3)
shelf((0.4, -0.55, 3.0), 0.13, (-30, 0, 0), 'chest', 3)

# extra moss tufts hanging on strands / limbs
for _ in range(40):
    bn = random.choice(['upper_arm_R', 'upper_arm_L', 'forearm_R', 'forearm_L', 'thigh_R', 'thigh_L', 'shin_R', 'shin_L', 'chest', 'spine'])
    h, t = BD[bn][2], BD[bn][3]
    p = h + (t - h) * random.random()
    p += V((random.uniform(-.3, .3), random.uniform(-.45, .1), random.uniform(-.05, .15)))
    blob(p, (0.1, 0.1, 0.07), bone=bn, kind='ico', jit=0.3, mat=MS, subdiv=2, flat=False)

for v in bm.verts:
    if v.co.z < 0: v.co.z = 0.0
# normalise weights
for v in bm.verts:
    g = v[dl]
    tot = sum(g.values())
    if tot > 0:
        for k in list(g.keys()):
            g[k] /= tot
bm.normal_update()
print('REST Z', min(v.co.z for v in bm.verts), max(v.co.z for v in bm.verts), min(v.co.x for v in bm.verts), max(v.co.x for v in bm.verts))
me = bpy.data.meshes.new('monster_mesh')
bm.to_mesh(me)
bm.free()

# ---------------------------------------------------------------- materials
def mk_mat(name, key, uvscale=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    ext = {'stone': ('jpg', 'png'), 'bark': ('jpg', 'png'), 'moss': ('png', 'png'), 'ivory': ('jpg', 'png')}[key]
    def img(fn, nc):
        i = bpy.data.images.load(os.path.join(TEX, fn))
        if nc:
            i.colorspace_settings.name = 'Non-Color'
        n = nt.nodes.new('ShaderNodeTexImage')
        n.image = i
        return n
    a = img(f'{key}-albedo.{ext[0]}', False)
    nrm = img(f'{key}-normal.png', True)
    r = img(f'{key}-roughness.png', True)
    nm = nt.nodes.new('ShaderNodeNormalMap')
    nm.inputs['Strength'].default_value = 1.0
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(a.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(nrm.outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    nt.links.new(r.outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
    bsdf.inputs['Metallic'].default_value = 0.0
    return m

mats = [mk_mat('stone', 'stone'), mk_mat('bark', 'bark'), mk_mat('moss', 'moss'), mk_mat('ivory', 'ivory')]
am = bpy.data.materials.new('amber_eyes')
am.use_nodes = True
b = am.node_tree.nodes['Principled BSDF']
b.inputs['Base Color'].default_value = (1.0, 0.55, 0.08, 1)
b.inputs['Emission Color'].default_value = (1.0, 0.5, 0.05, 1)
b.inputs['Emission Strength'].default_value = 4.0
b.inputs['Roughness'].default_value = 0.2
mats.append(am)
for m in mats:
    me.materials.append(m)

obj = bpy.data.objects.new('forest_warden', me)
bpy.context.scene.collection.objects.link(obj)
for n in BN:
    obj.vertex_groups.new(name=n)

# ---------------------------------------------------------------- armature
ad = bpy.data.armatures.new('warden_rig')
arm = bpy.data.objects.new('warden_armature', ad)
bpy.context.scene.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
arm.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for n, p, h, t in B:
    eb = ad.edit_bones.new(n)
    eb.head, eb.tail = h, t
    if p:
        eb.parent = ad.edit_bones[p]
bpy.ops.object.mode_set(mode='OBJECT')
obj.parent = arm
mod = obj.modifiers.new('Armature', 'ARMATURE')
mod.object = arm

# ---------------------------------------------------------------- animation
sc = bpy.context.scene
sc.render.fps = 25
sc.frame_start, sc.frame_end = 0, 30
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')
act = bpy.data.actions.new('attack')
arm.animation_data_create()
arm.animation_data.action = act
for pb in arm.pose.bones:
    pb.rotation_mode = 'QUATERNION'

def setrot(name, eul, frame):
    pb = arm.pose.bones[name]
    R = ad.bones[name].matrix_local.to_3x3()
    Q = Euler([math.radians(a) for a in eul]).to_matrix()
    q = (R.inverted() @ Q @ R).to_quaternion()
    pb.rotation_quaternion = q
    pb.keyframe_insert('rotation_quaternion', frame=frame)

def setloc(name, loc, frame):
    pb = arm.pose.bones[name]
    pb.location = loc
    pb.keyframe_insert('location', frame=frame)

# (frame): {bone: world-euler deg}
KEYS = {
    0:  {},
    10: {'spine': (-8, 0, 12), 'chest': (-14, 0, 22), 'neck': (8, 0, -10), 'head': (6, 0, -8),
         'clavicle_R': (0, 0, 8), 'upper_arm_R': (150, 0, 25), 'forearm_R': (35, 0, 0), 'hand_R': (15, 0, 0),
         'upper_arm_L': (-15, 0, -8), 'thigh_R': (10, 0, 0), 'thigh_L': (-8, 0, 0)},
    15: {'spine': (14, 0, -18), 'chest': (22, 0, -34), 'neck': (-10, 0, 12), 'head': (-12, 0, 14),
         'clavicle_R': (0, 0, -6), 'upper_arm_R': (-70, 0, -40), 'forearm_R': (-35, 0, 0), 'hand_R': (-25, 0, 0),
         'upper_arm_L': (12, 0, 8), 'thigh_R': (-14, 0, 0), 'thigh_L': (14, 0, 0)},
    19: {'spine': (12, 0, -15), 'chest': (18, 0, -30), 'neck': (-8, 0, 10), 'head': (-10, 0, 12),
         'upper_arm_R': (-62, 0, -36), 'forearm_R': (-30, 0, 0), 'hand_R': (-20, 0, 0),
         'upper_arm_L': (10, 0, 6), 'thigh_R': (-12, 0, 0), 'thigh_L': (12, 0, 0)},
    30: {},
}
ROOTLOC = {0: (0, 0, 0), 10: (0, 0.2, -0.12), 15: (0, -0.4, -0.18), 19: (0, -0.35, -0.16), 30: (0, 0, 0)}
animated = set()
for k in KEYS.values():
    animated |= set(k)
for fr, d in KEYS.items():
    for n in animated:
        setrot(n, d.get(n, (0, 0, 0)), fr)
for fr, loc in ROOTLOC.items():
    setloc('root', loc, fr)
bpy.ops.object.mode_set(mode='OBJECT')
arm.animation_data.action = act
act.name = 'attack'
for a in list(bpy.data.actions):
    if a.name != 'attack':
        bpy.data.actions.remove(a)
# rest pose at frame 0
sc.frame_set(0)

# ---------------------------------------------------------------- export
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
arm.select_set(True)
bpy.ops.export_scene.gltf(
    filepath=OUT, export_format='GLB', use_selection=True, export_yup=True,
    export_skins=True, export_animations=True, export_animation_mode='ACTIONS',
    export_image_format='AUTO', export_apply=False, export_normals=True,
    export_force_sampling=True)
print('EXPORTED', OUT, 'verts', len(me.vertices), 'polys', len(me.polygons))
