import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Euler

OUT = r"C:\Users\aaron\skill-glb-creator-claude-demo\runs\baseline-3"
TEX = r"C:\Users\aaron\skill-glb-creator-claude-demo\assets\textures"
rng = random.Random(7)

bpy.ops.wm.read_factory_settings(use_empty=True)

# ---------------------------------------------------------------- skeleton def
BONES = {  # name: (head, tail, parent)
    "root":    ((0, 0, 0), (0, 0, 0.4), None),
    "hips":    ((0, 0, 2.0), (0, -0.1, 2.5), "root"),
    "spine":   ((0, -0.1, 2.5), (0, -0.3, 3.1), "hips"),
    "chest":   ((0, -0.3, 3.1), (0, -0.4, 3.7), "spine"),
    "neck":    ((0, -0.4, 3.6), (0, -0.85, 3.95), "chest"),
    "head":    ((0, -0.85, 3.95), (0, -1.0, 4.5), "neck"),
}
for s, sx in (("L", 1), ("R", -1)):
    BONES[f"upper_arm.{s}"] = ((sx*1.5, -0.2, 3.5), (sx*1.95, -0.5, 2.3), "chest")
    BONES[f"forearm.{s}"] = ((sx*1.95, -0.5, 2.3), (sx*1.95, -0.75, 1.2), f"upper_arm.{s}")
    BONES[f"hand.{s}"] = ((sx*1.95, -0.75, 1.2), (sx*1.95, -0.9, 0.7), f"forearm.{s}")
    BONES[f"thigh.{s}"] = ((sx*0.7, 0, 2.0), (sx*0.95, -0.3, 1.1), "hips")
    BONES[f"shin.{s}"] = ((sx*0.95, -0.3, 1.1), (sx*0.85, 0, 0.25), f"thigh.{s}")
    BONES[f"foot.{s}"] = ((sx*0.85, 0, 0.25), (sx*0.85, -0.6, 0.1), f"shin.{s}")
BONE_NAMES = list(BONES.keys())

def V(t): return Vector(t)

# ---------------------------------------------------------------- weights
def rigid(b):
    return lambda co: {b: 1.0}

def mix(*pairs):
    return lambda co: {b: w for b, w in pairs}

def chain(names):
    pts = [V(BONES[names[0]][0])] + [V(BONES[n][1]) for n in names]
    # joints are bone tails (children start at parent tail except for neck etc.)
    def fn(co):
        best = None
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i+1]
            ab = b - a
            t = max(0.0, min(1.0, (co - a).dot(ab) / max(ab.length_squared, 1e-6)))
            d = (a + ab * t - co).length
            if best is None or d < best[0]:
                best = (d, i + t)
        f = best[1]
        n = len(names)
        w = {}
        for k in range(n):
            x = max(0.0, 1 - max(0.0, abs(f - (k + 0.5)) - 0.15) / 0.55)
            if x > 0: w[names[k]] = x
        s = sum(w.values())
        return {k: v / s for k, v in w.items()}
    return fn

# ---------------------------------------------------------------- builders
MATS = ["stone", "bark", "moss", "ivory", "eye"]
BM = {m: bmesh.new() for m in MATS}
DL = {m: BM[m].verts.layers.deform.verify() for m in MATS}

def assign(mat, n0, wfn, smooth):
    bm = BM[mat]; bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    dl = DL[mat]
    for v in bm.verts[n0:]:
        for b, w in wfn(v.co).items():
            v[dl][BONE_NAMES.index(b)] = w
    newv = set(bm.verts[n0:])
    for f in bm.faces:
        if all(v in newv for v in f.verts):
            f.smooth = smooth

def rot_mat(rot):
    return Euler(rot, 'XYZ').to_matrix().to_4x4()

def blob(mat, c, size, rot, wfn, kind="rock", jit=0.25, seed=None, sub=1):
    bm = BM[mat]; n0 = len(bm.verts)
    r = random.Random(seed if seed is not None else rng.random())
    if kind == "slab":
        res = bmesh.ops.create_cube(bm, size=2.0)
        bmesh.ops.subdivide_edges(bm, edges=list(set(e for v in res['verts'] for e in v.link_edges)), cuts=1, use_grid_fill=True)
        bm.verts.ensure_lookup_table()
        for v in bm.verts[n0:]:
            v.co += Vector((r.uniform(-jit, jit), r.uniform(-jit, jit), r.uniform(-jit, jit)))
    else:
        bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
        bm.verts.ensure_lookup_table()
        for v in bm.verts[n0:]:
            v.co *= r.uniform(1 - jit, 1 + jit * 0.6)
    bm.verts.ensure_lookup_table()
    M = Matrix.Translation(c) @ rot_mat(rot) @ Matrix.Diagonal((size[0], size[1], size[2], 1))
    for v in bm.verts[n0:]:
        v.co = M @ v.co
    assign(mat, n0, wfn, kind == "smooth")
    return M

def catmull(pts, per=8):
    P = [V(p) for p in pts]
    if len(P) == 2:
        return [P[0].lerp(P[1], i / per) for i in range(per + 1)]
    ext = [P[0] * 2 - P[1]] + P + [P[-1] * 2 - P[-2]]
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i-1], ext[i], ext[i+1], ext[i+2]
        for k in range(per):
            t = k / per
            out.append(0.5 * ((2*p1) + (-p0 + p2) * t + (2*p0 - 5*p1 + 4*p2 - p3) * t*t + (-p0 + 3*p1 - 3*p2 + p3) * t**3))
    out.append(P[-1])
    return out

def tube(mat, pts, rad, wfn, sides=7, helix=None, per=7, smooth=True, taper=None):
    """rad: float or (r0, r1). helix=(radius, turns, phase)"""
    bm = BM[mat]; n0 = len(bm.verts)
    path = catmull(pts, per)
    N = len(path)
    r0, r1 = (rad, rad) if not isinstance(rad, tuple) else rad
    T0 = (path[1] - path[0]).normalized()
    ref = Vector((0, 0, 1)) if abs(T0.z) < 0.9 else Vector((1, 0, 0))
    Nv = (ref - T0 * ref.dot(T0)).normalized()
    rings = []
    for i, p in enumerate(path):
        t = i / (N - 1)
        T = ((path[min(i+1, N-1)] - path[max(i-1, 0)])).normalized()
        Nv = (Nv - T * Nv.dot(T)).normalized()
        B = T.cross(Nv)
        c = p
        if helix:
            hr, turns, ph = helix
            ang = ph + 2 * math.pi * turns * t
            c = p + hr * (math.cos(ang) * Nv + math.sin(ang) * B)
        r = r0 + (r1 - r0) * t
        if taper == "claw":
            r = r0 * (1 - t) ** 0.8 + 0.008
        ring = []
        for s in range(sides):
            a = 2 * math.pi * s / sides
            ring.append(bm.verts.new(c + r * (math.cos(a) * Nv + math.sin(a) * B)))
        rings.append(ring)
    for i in range(N - 1):
        for s in range(sides):
            bm.faces.new((rings[i][s], rings[i][(s+1) % sides], rings[i+1][(s+1) % sides], rings[i+1][s]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    assign(mat, n0, wfn, smooth)

def shelf(c, size, rot, wfn):
    bm = BM["ivory"]; n0 = len(bm.verts)
    bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=1.0, radius2=0.85, depth=0.25)
    bm.verts.ensure_lookup_table()
    M = Matrix.Translation(c) @ rot_mat(rot) @ Matrix.Diagonal((size, size * 0.8, size * 0.5, 1))
    for v in bm.verts[n0:]:
        v.co = M @ v.co
    assign("ivory", n0, wfn, True)

def moss_on(c, rsize, wfn, n=2):
    for _ in range(n):
        off = Vector((rng.uniform(-.6, .6), rng.uniform(-.6, .6), 0)) * rsize
        blob("moss", c + off, (rsize * rng.uniform(.5, .8), rsize * rng.uniform(.5, .8), rsize * 0.4),
             (0, 0, rng.uniform(0, 6)), wfn, kind="rock", jit=0.35, sub=1)

RS = 0.86
def rock(c, size, rot, wfn, moss=0.5, kind="slab", seed=None):
    size = tuple(x * RS for x in size)
    blob("stone", c, size, rot, wfn, kind=kind, jit=0.28, seed=seed)
    if rng.random() < max(moss, 0.8):
        top = Vector(c) + Vector((0, 0, size[2] * 0.7))
        moss_on(top, max(size[0], size[1]) * 1.1, wfn, n=rng.choice([2, 3]))

def braid(mat, pts, r, wfn, n=3, turns=1.5, hr=None, sides=6, per=7, core=True):
    r *= 1.25
    hr = hr if hr is not None else r * 0.6
    if core:
        tube(mat, pts, r * 0.8, wfn, sides=8, per=per)
    for i in range(n):
        tube(mat, pts, r * 0.55, wfn, sides=sides, per=per, helix=(hr, turns, 2 * math.pi * i / n))

# ---------------------------------------------------------------- body
# torso core
blob("bark", (0, -0.05, 2.1), (0.95, 0.65, 0.6), (0, 0, 0), chain(["hips", "spine"]), kind="smooth", jit=0.05, sub=2)
blob("bark", (0, -0.2, 2.75), (0.85, 0.65, 0.65), (0, 0, 0), chain(["hips", "spine", "chest"]), kind="smooth", jit=0.05, sub=2)
blob("bark", (0, -0.4, 3.3), (1.35, 0.9, 0.85), (0, 0, 0), chain(["spine", "chest"]), kind="smooth", jit=0.05, sub=2)
# braided cords over torso
tw = chain(["hips", "spine", "chest"])
for sx in (-1, 1):
    for k, off in enumerate((0.25, 0.55, 0.85)):
        braid("bark", [(sx*off, -0.5, 2.0), (sx*(off+0.25), -0.75, 2.7), (sx*(off+0.35), -0.95, 3.3), (sx*(off+0.8), -0.5, 3.75)],
              0.17, tw, n=3, turns=2, sides=5, per=6)
for sx in (-1, 1):
    braid("bark", [(sx*0.9, 0.5, 2.2), (sx*1.1, 0.55, 2.9), (sx*1.2, 0.35, 3.5)], 0.2, tw, n=3)
# back hump of cords
braid("bark", [(-0.6, 0.6, 2.4), (-0.2, 0.9, 3.2), (0.3, 0.8, 3.7)], 0.25, tw, n=3)
braid("bark", [(0.7, 0.6, 2.4), (0.4, 0.95, 3.3), (0.0, 0.7, 3.8)], 0.25, tw, n=3)

# chest plates
chestw = chain(["spine", "chest"])
rock((0.55, -1.05, 3.35), (0.55, 0.22, 0.4), (0.4, 0.3, 0.5), chestw)
rock((-0.5, -1.0, 3.25), (0.6, 0.22, 0.4), (0.3, -0.25, -0.4), chestw)
rock((0.0, -1.15, 2.95), (0.65, 0.28, 0.3), (0.5, 0, 0.1), chestw)
rock((-0.7, -0.95, 2.6), (0.4, 0.25, 0.35), (0.2, 0.2, 0.5), chain(["hips", "spine"]))
rock((0.65, -0.9, 2.55), (0.4, 0.25, 0.35), (0.1, -0.2, -0.3), chain(["hips", "spine"]))
rock((0.0, -0.75, 2.2), (0.45, 0.3, 0.3), (0.3, 0.1, 0.2), chain(["hips", "spine"]))
# back plates
for x, z, s in ((-0.6, 3.5, 0.55), (0.5, 3.6, 0.5), (0.0, 3.0, 0.5), (-0.5, 2.6, 0.4), (0.6, 2.7, 0.4)):
    rock((x, 1.0 if z > 3 else 0.7, z), (s, 0.28, s * 0.85), (0.4, 0.0, rng.uniform(-.5, .5)), chestw, seed=int(x*10+z))

# big shoulder masses (right arm bigger, as in reference)
shR = mix(("chest", 0.7), ("upper_arm.R", 0.3))
shL = mix(("chest", 0.7), ("upper_arm.L", 0.3))
rock((-1.7, -0.1, 3.8), (0.95, 0.75, 0.6), (0.2, -0.3, 0.4), shR, moss=1, seed=3)
rock((-1.3, 0.1, 4.0), (0.65, 0.55, 0.5), (0.3, 0.1, 0.9), shR, moss=1, seed=4)
rock((-1.95, 0.0, 3.6), (0.55, 0.6, 0.5), (0.1, 0.5, 0.3), shR, moss=0.8, seed=5)
rock((-0.9, -0.3, 3.95), (0.5, 0.45, 0.5), (0.2, 0.2, 0.2), shR, moss=0.8, seed=6)
rock((1.6, -0.05, 3.7), (0.7, 0.55, 0.55), (0.2, 0.3, -0.3), shL, moss=1, seed=8)
rock((1.2, 0.15, 3.9), (0.5, 0.45, 0.4), (0.1, 0.2, 0.3), shL, moss=1, seed=9)
rock((1.9, -0.1, 3.45), (0.4, 0.5, 0.45), (0.1, -0.4, 0.3), shL, moss=0.8, seed=10)
# bark shoulder joints
for s, sx in (("L", 1), ("R", -1)):
    blob("bark", (sx*1.55, -0.2, 3.5), (0.55, 0.5, 0.5), (0, 0, 0), mix(("chest", 0.5), (f"upper_arm.{s}", 0.5)), kind="smooth", jit=0.05, sub=2)

# neck cords
nk = chain(["neck", "head"])
for sx in (-1, 1):
    braid("bark", [(sx*0.35, -0.3, 3.5), (sx*0.35, -0.65, 3.8), (sx*0.28, -0.95, 4.0)], 0.2, mix(("neck", 1.0)), n=3, sides=5)

# ---------------------------------------------------------------- head
H = rigid("head")
blob("bark", (0, -1.0, 4.1), (0.5, 0.5, 0.5), (0, 0, 0), H, kind="smooth", jit=0.04, sub=2)
rock((0, -1.1, 4.4), (0.5, 0.45, 0.4), (-0.25, 0, 0), H, moss=1, seed=21)             # brow / helmet
rock((0, -1.22, 4.1), (0.5, 0.32, 0.55), (-0.15, 0, 0), H, moss=0, seed=22)         # mask
rock((0, -1.3, 3.7), (0.36, 0.3, 0.62), (0.1, 0, 0), H, moss=0, seed=23)            # jaw wedge
rock((-0.45, -0.95, 4.35), (0.3, 0.3, 0.45), (0.2, 0.3, -0.4), H, moss=1, seed=24)
rock((0.45, -0.95, 4.3), (0.3, 0.3, 0.45), (0.2, -0.3, 0.4), H, moss=1, seed=25)
rock((0.0, -0.7, 4.6), (0.4, 0.3, 0.3), (0.5, 0, 0), H, moss=1, seed=26)
for sx in (-1, 1):
    blob("eye", (sx*0.22, -1.68, 4.2), (0.1, 0.07, 0.07), (0, 0, 0), H, kind="rock", jit=0.02, sub=1)
    shelf((sx*0.5, -0.8, 4.65), 0.18, (0.2, sx*0.4, 0), H)

# antlers
def antler(sx):
    H_ = rigid("head")
    main = [(sx*0.3, -0.9, 4.4), (sx*0.5, -0.8, 4.65), (sx*0.85, -0.85, 4.85), (sx*1.25, -0.95, 4.8)]
    tube("bark", main, (0.11, 0.05), H_, sides=6, helix=(0.03, 2, 0))
    tube("bark", [(sx*0.5, -0.8, 4.65), (sx*0.45, -1.0, 4.9), (sx*0.55, -1.2, 5.0)], (0.07, 0.025), H_, sides=5)
    tube("bark", [(sx*0.85, -0.85, 4.85), (sx*0.95, -0.7, 5.1), (sx*1.1, -0.65, 5.3)], (0.065, 0.02), H_, sides=5)
    tube("bark", [(sx*1.2, -0.95, 4.82), (sx*1.35, -1.1, 4.95), (sx*1.55, -1.15, 4.9)], (0.05, 0.015), H_, sides=5)
    tube("bark", [(sx*0.7, -0.82, 4.78), (sx*0.65, -0.55, 4.9)], (0.05, 0.015), H_, sides=5)
    moss_on(Vector((sx*0.85, -0.85, 4.92)), 0.12, H_, 1)
    moss_on(Vector((sx*0.5, -0.8, 4.72)), 0.1, H_, 1)
antler(-1); antler(1)

# ---------------------------------------------------------------- arms
for s, sx, big in (("L", 1, 0.9), ("R", -1, 1.1)):
    aw = chain([f"upper_arm.{s}", f"forearm.{s}", f"hand.{s}"])
    pts = [(sx*1.5, -0.2, 3.5), (sx*1.95, -0.5, 2.3), (sx*1.95, -0.75, 1.2)]
    braid("bark", pts, 0.42 * big, aw, n=4, turns=2, hr=0.28 * big, per=9)
    # elbow bulge
    blob("bark", (sx*2.0, -0.55, 2.3), (0.4*big, 0.4*big, 0.4*big), (0, 0, 0), mix((f"upper_arm.{s}", 0.5), (f"forearm.{s}", 0.5)), kind="smooth", jit=0.05, sub=2)
    # upper-arm plates
    ua = rigid(f"upper_arm.{s}")
    rock((sx*2.15, -0.3, 2.9), (0.35*big, 0.4*big, 0.5), (0.1, sx*0.2, 0.3), ua, seed=30+sx)
    rock((sx*1.75, -0.7, 2.9), (0.3*big, 0.2, 0.35), (0.3, 0, 0.2), ua, seed=31+sx)
    # forearm gauntlet rocks
    fa = rigid(f"forearm.{s}")
    rock((sx*2.3, -0.65, 1.75), (0.3*big, 0.5*big, 0.7*big), (0.1, sx*0.2, 0), fa, seed=40+sx)
    rock((sx*2.0, -1.05, 1.8), (0.4*big, 0.25*big, 0.6*big), (0.2, 0, 0.2), fa, seed=41+sx)
    rock((sx*1.7, -0.5, 1.7), (0.25*big, 0.35*big, 0.55*big), (0, sx*-0.2, 0.1), fa, seed=42+sx)
    rock((sx*2.2, -0.4, 2.2), (0.35*big, 0.35*big, 0.4*big), (0.3, 0.1, 0.0), fa, seed=43+sx)
    for k in range(3):
        shelf((sx*2.35, -0.7 + 0.0, 2.1 - k*0.18), 0.17, (0.1, sx*0.9, 0.0), fa)
    # hand
    hd = rigid(f"hand.{s}")
    blob("bark", (sx*1.95, -0.85, 0.95), (0.38*big, 0.33*big, 0.33*big), (0, 0, 0), hd, kind="smooth", jit=0.05, sub=2)
    rock((sx*2.1, -0.8, 1.1), (0.28, 0.25, 0.2), (0.2, 0, 0.3), hd, seed=50+sx)
    for k, dx in enumerate((-0.28, 0.0, 0.28)):
        x = sx*1.95 + dx
        tube("ivory", [(x, -0.9, 1.0), (x, -1.05, 0.55), (x + dx*0.3, -1.35, 0.2), (x + dx*0.5, -1.65, 0.12)], (0.17, 0.0), hd, sides=6, taper="claw", per=6)
    # side claw
    tube("ivory", [(sx*1.95 + sx*0.35, -0.7, 1.0), (sx*2.3, -0.85, 0.75), (sx*2.35, -1.05, 0.5)], (0.12, 0.0), hd, sides=5, taper="claw", per=5)

# ---------------------------------------------------------------- legs
for s, sx in (("L", 1), ("R", -1)):
    lw = chain([f"thigh.{s}", f"shin.{s}", f"foot.{s}"])
    pts = [(sx*0.7, 0, 2.0), (sx*0.95, -0.3, 1.1), (sx*0.85, 0, 0.3)]
    braid("bark", pts, 0.5, lw, n=4, turns=2, hr=0.3, per=9)
    blob("bark", (sx*0.95, -0.3, 1.1), (0.45, 0.45, 0.45), (0, 0, 0), mix((f"thigh.{s}", 0.5), (f"shin.{s}", 0.5)), kind="smooth", jit=0.05, sub=2)
    th = rigid(f"thigh.{s}")
    rock((sx*1.25, -0.1, 1.7), (0.35, 0.5, 0.55), (0.1, sx*0.2, 0.2), th, seed=60+sx)
    rock((sx*0.8, -0.55, 1.65), (0.45, 0.3, 0.5), (0.3, 0, -0.2), th, seed=61+sx)
    rock((sx*0.5, 0.35, 1.8), (0.3, 0.3, 0.45), (0.2, 0.1, 0.2), th, seed=62+sx)
    sh = rigid(f"shin.{s}")
    rock((sx*0.95, -0.75, 1.15), (0.5, 0.3, 0.45), (0.3, 0, 0.1), sh, seed=63+sx)   # knee cap
    rock((sx*1.15, -0.1, 0.7), (0.35, 0.4, 0.45), (0.1, sx*0.1, 0.3), sh, seed=64+sx)
    rock((sx*0.65, -0.1, 0.65), (0.3, 0.4, 0.45), (0.2, 0.0, -0.3), sh, seed=65+sx)
    ft = rigid(f"foot.{s}")
    for i, (dx, dy, sz) in enumerate(((0, -0.55, 0.28), (-0.35, -0.3, 0.26), (0.35, -0.3, 0.26), (0.0, 0.15, 0.3), (0.45, 0.1, 0.22), (-0.45, 0.1, 0.22))):
        rock((sx*0.85 + dx, dy, sz*0.75), (sz*1.1, sz*1.2, sz*0.8), (rng.uniform(-.2, .2), rng.uniform(-.2, .2), rng.uniform(0, 3)), ft, seed=70+i+(5 if sx > 0 else 0))
    blob("bark", (sx*0.85, -0.1, 0.35), (0.45, 0.55, 0.25), (0, 0, 0), ft, kind="smooth", jit=0.05, sub=2)

# ---------------------------------------------------------------- finish meshes
GS = 0.86
for m in MATS:
    for v in BM[m].verts: v.co *= GS
for k, (h, t, p) in list(BONES.items()):
    BONES[k] = (tuple(x*GS for x in h), tuple(x*GS for x in t), p)
# simple box UVs (world-space)
UVS = {"stone": 1 / 1.6, "bark": 1 / 1.7, "moss": 1 / 0.7, "ivory": 1 / 0.9, "eye": 1.0}
for m in MATS:
    bm = BM[m]
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    uv = bm.loops.layers.uv.new("UVMap")
    sc = UVS[m]
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for l in f.loops:
            c = l.vert.co
            if ax == 0: u, v = c.y, c.z
            elif ax == 1: u, v = c.x, c.z
            else: u, v = c.x, c.y
            l[uv].uv = (u * sc, v * sc)

# material creation
def mk_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
    out = nt.nodes["Material Output"]
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    if name == "eye":
        bsdf.inputs["Base Color"].default_value = (1, 0.55, 0.05, 1)
        bsdf.inputs["Emission Color"].default_value = (1, 0.5, 0.05, 1)
        bsdf.inputs["Emission Strength"].default_value = 6.0
        bsdf.inputs["Roughness"].default_value = 0.3
        return mat
    def img(fn, cs):
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = bpy.data.images.load(os.path.join(TEX, fn))
        n.image.colorspace_settings.name = cs
        return n
    ext = {"stone": ("jpg",), "bark": ("jpg",), "moss": ("png",), "ivory": ("jpg",)}[name][0]
    a = img(f"{name}-albedo.{ext}", "sRGB")
    nt.links.new(a.outputs["Color"], bsdf.inputs["Base Color"])
    r = img(f"{name}-roughness.png", "Non-Color")
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(r.outputs["Color"], sep.inputs["Color"])
    nt.links.new(sep.outputs["Green"], bsdf.inputs["Roughness"])
    nm = img(f"{name}-normal.png", "Non-Color")
    nmn = nt.nodes.new("ShaderNodeNormalMap")
    nmn.inputs["Strength"].default_value = 1.0
    nt.links.new(nm.outputs["Color"], nmn.inputs["Color"])
    nt.links.new(nmn.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Metallic"].default_value = 0.0
    return mat

# armature
arm_data = bpy.data.armatures.new("WardenArmature")
arm = bpy.data.objects.new("WardenArmature", arm_data)
bpy.context.scene.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
arm.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
eb = {}
for n in BONE_NAMES:
    h, t, p = BONES[n]
    b = arm_data.edit_bones.new(n)
    b.head, b.tail = V(h), V(t)
    eb[n] = b
for n in BONE_NAMES:
    p = BONES[n][2]
    if p: eb[n].parent = eb[p]
bpy.ops.object.mode_set(mode='OBJECT')

objs = []
for m in MATS:
    mesh = bpy.data.meshes.new(m + "_mesh")
    BM[m].to_mesh(mesh)
    BM[m].free()
    ob = bpy.data.objects.new("Warden_" + m, mesh)
    bpy.context.scene.collection.objects.link(ob)
    for n in BONE_NAMES: ob.vertex_groups.new(name=n)
    mesh.materials.append(mk_mat(m))
    ob.parent = arm
    mod = ob.modifiers.new("Armature", 'ARMATURE'); mod.object = arm
    objs.append(ob)

# ground at Y=0 (Z in Blender)
mz = min((ob.matrix_world @ v.co).z for ob in objs for v in ob.data.vertices)
print("MIN Z", mz)
top = max((ob.matrix_world @ v.co).z for ob in objs for v in ob.data.vertices)
print("MAX Z", top)
for ob in objs:
    for v in ob.data.vertices: v.co.z -= mz
    ob.data.update()

# ---------------------------------------------------------------- animation
scene = bpy.context.scene
scene.render.fps = 30
scene.frame_start, scene.frame_end = 1, 37
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')
AX = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}
def q_for(bone, rots):
    R = Matrix.Identity(3)
    for ax, deg in rots:
        R = Matrix.Rotation(math.radians(deg), 3, AX[ax]) @ R
    M = arm_data.bones[bone].matrix_local.to_3x3()
    return (M.inverted() @ R @ M).to_quaternion()
for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'

POSES = {
    1: {},
    10: {  # anticipation: rear back, arm raised
        "root": dict(loc=(0, 0.13, -0.17)),
        "hips": dict(rots=[("z", 12)]),
        "spine": dict(rots=[("z", 15), ("x", -8)]),
        "chest": dict(rots=[("z", 18), ("x", -10)]),
        "head": dict(rots=[("x", -10), ("z", -10)]),
        "upper_arm.R": dict(rots=[("x", 150), ("y", -25)]),
        "forearm.R": dict(rots=[("x", 35)]),
        "hand.R": dict(rots=[("x", 20)]),
        "upper_arm.L": dict(rots=[("x", 25)]),
        "thigh.L": dict(rots=[("x", 15)]), "shin.L": dict(rots=[("x", -20)]),
        "thigh.R": dict(rots=[("x", -10)]),
    },
    16: {  # impact: arm slammed forward and down
        "root": dict(loc=(0, -0.4, -0.13)),
        "hips": dict(rots=[("z", -15)]),
        "spine": dict(rots=[("z", -20), ("x", 12)]),
        "chest": dict(rots=[("z", -25), ("x", 15)]),
        "head": dict(rots=[("x", 15), ("z", 10)]),
        "upper_arm.R": dict(rots=[("x", -75), ("y", 20)]),
        "forearm.R": dict(rots=[("x", -15)]),
        "hand.R": dict(rots=[("x", -10)]),
        "upper_arm.L": dict(rots=[("x", 20), ("y", -10)]),
        "thigh.L": dict(rots=[("x", -25)]), "shin.L": dict(rots=[("x", 15)]),
        "thigh.R": dict(rots=[("x", 20)]), "shin.R": dict(rots=[("x", -25)]),
    },
    24: {  # follow-through hold, slight settle
        "root": dict(loc=(0, -0.33, -0.09)),
        "hips": dict(rots=[("z", -12)]),
        "spine": dict(rots=[("z", -16), ("x", 10)]),
        "chest": dict(rots=[("z", -20), ("x", 12)]),
        "head": dict(rots=[("x", 10), ("z", 8)]),
        "upper_arm.R": dict(rots=[("x", -68), ("y", 18)]),
        "forearm.R": dict(rots=[("x", -12)]),
        "upper_arm.L": dict(rots=[("x", 15)]),
        "thigh.L": dict(rots=[("x", -20)]), "shin.L": dict(rots=[("x", 12)]),
        "thigh.R": dict(rots=[("x", 16)]), "shin.R": dict(rots=[("x", -20)]),
    },
    37: {},
}
for fr, pose in POSES.items():
    for pb in arm.pose.bones:
        d = pose.get(pb.name, {})
        pb.rotation_quaternion = q_for(pb.name, d["rots"]) if "rots" in d else (1, 0, 0, 0)
        pb.location = d.get("loc", (0, 0, 0)) if pb.name == "root" else (0, 0, 0)
        pb.keyframe_insert("rotation_quaternion", frame=fr)
        if pb.name == "root":
            pb.keyframe_insert("location", frame=fr)
bpy.ops.object.mode_set(mode='OBJECT')
for a in bpy.data.actions: a.name = "attack"
for a in bpy.data.actions: print("ACTION", a.name, a.frame_range[:])

# export
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "monster.glb"), export_format='GLB',
    use_selection=True, export_animations=True, export_skins=True, export_yup=True,
    export_image_format='AUTO', export_apply=False)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "monster.blend"))
print("DONE")
