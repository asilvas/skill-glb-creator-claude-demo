import { Asset, type V } from '../scripts/geometry';
import * as T from 'three';

const TX = 'C:/Users/aaron/skill-glb-creator-claude-demo/assets/textures/';
const rd = async (f: string) => new Uint8Array(await Bun.file(TX + f).arrayBuffer());

function curve(pts: V[], n = 14): V[] {
  const c = new T.CatmullRomCurve3(pts.map(p => new T.Vector3(...p)));
  return c.getPoints(n).map(p => [p.x, p.y, p.z] as V);
}
let s = 7; const rnd = () => (s = (s * 16807) % 2147483647) / 2147483647;

export default async function build() {
  s = 7;
  const a = new Asset();
  for (const m of ['stone', 'bark', 'moss', 'ivory']) {
    a.surfaces.set(m, {
      baseColor: await rd(`${m}-albedo.${m === 'moss' ? 'png' : 'jpg'}`),
      normal: await rd(`${m}-normal.png`),
      roughness: await rd(`${m}-roughness.png`),
      normalScale: 0.9, tint: ({stone:[1,1,1],bark:[1,.8,.62],moss:[.9,1,.6],ivory:[1,1,.95]} as any)[m],
    });
  }

  // ---- skeleton ----
  a.joint('Root', [0, 0, 0]);
  a.joint('Hips', [0, 2.0, -.2], 'Root');
  a.joint('Spine', [0, 2.6, 0], 'Hips');
  a.joint('Chest', [0, 3.2, .3], 'Spine');
  a.joint('Neck', [0, 3.7, .8], 'Chest');
  a.joint('Head', [0, 4.0, 1.3], 'Neck');
  const sides: [string, number][] = [['L', -1], ['R', 1]];
  for (const [sd, X] of sides) {
    a.joint('Shoulder' + sd, [X * .9, 3.6, .1], 'Chest');
    a.joint('UpperArm' + sd, [X * 1.45, 3.5, .1], 'Shoulder' + sd);
    a.joint('Forearm' + sd, [X * 1.85, 2.4, .45], 'UpperArm' + sd);
    a.joint('Hand' + sd, [X * 1.95, 1.45, .8], 'Forearm' + sd);
    a.joint('Thigh' + sd, [X * .65, 2.0, -.05], 'Hips');
    a.joint('Shin' + sd, [X * .8, 1.1, .35], 'Thigh' + sd);
    a.joint('Foot' + sd, [X * .85, .35, .3], 'Shin' + sd);
  }
  a.joint('AntlerL', [-.35, 4.5, 1.2], 'Head');
  a.joint('AntlerR', [.35, 4.5, 1.2], 'Head');

  const braid = (pts: V[], r: number, bone: string, strands = 3, tw = 5, mat = 'bark') => {
    const cl = curve(pts, 18);
    for (let k = 0; k < strands; k++) {
      const path: V[] = cl.map((p, i) => {
        const ang = (i / cl.length) * Math.PI * tw + (k / strands) * Math.PI * 2;
        const off = r * .55;
        return [p[0] + Math.cos(ang) * off, p[1] + Math.sin(ang) * off * .6, p[2] + Math.sin(ang) * off] as V;
      });
      const radii = path.map((_, i) => r * (.62 + .1 * Math.sin(i * 1.3 + k)));
      a.tube(mat, path, radii, bone, 8);
    }
  };
  const rock = (c: V, r: V, bone: string, mat = 'stone') => a.ell(mat, c, r, bone, Math.floor(rnd() * 99), true);
  const mossAt = (c: V, r: number, bone: string) => a.ell('moss', c, [r, r * .5, r], bone, Math.floor(rnd() * 99), true);
  const shelf = (c: V, r: number, bone: string) => {
    for (let i = 0; i < 3; i++) a.ell('ivory', [c[0], c[1] - i * r * .5, c[2] + i * r * .15], [r * (1 - i * .12), r * .18, r * (1 - i * .12)], bone);
  };
  const claw = (base: V, dir: V, len: number, bone: string, r = .09) => {
    const d = new T.Vector3(...dir).normalize();
    const b = new T.Vector3(...base);
    const mid = b.clone().add(d.clone().multiplyScalar(len * .55)).add(new T.Vector3(0, -.05, .08 * len));
    const end = b.clone().add(d.clone().multiplyScalar(len)).add(new T.Vector3(0, -.12 * len, .45 * len));
    const pts = curve([base, [mid.x, mid.y, mid.z], [end.x, end.y, end.z]], 8);
    a.tube('ivory', pts, pts.map((_, i) => r * (1 - i / pts.length * .95) + .005), bone, 6);
  };


  // ---- torso ----
  braid([[0, 2.1, -.2], [0, 2.7, 0], [0, 3.2, .3]], .75, 'Spine', 4, 4);
  a.ell('bark', [0, 2.7, 0], [.85, .75, .7], 'Spine');
  a.ell('bark', [0, 3.3, .3], [1.1, .7, .8], 'Chest');
  a.ell('bark', [0, 2.1, -.2], [.8, .5, .6], 'Hips');
  a.plate('stone', [.15, 3.25, 1.05], [.85, .7, .3], 'Chest', 3, [-.05, -.15, .12]);
  a.plate('stone', [-.6, 2.7, .8], [.7, .7, .3], 'Spine', 4, [.1, .35, .1]);
  a.plate('stone', [.6, 2.7, .8], [.7, .8, .3], 'Spine', 5, [.1, -.35, -.15]);
  a.plate('stone', [0, 2.2, .6], [.7, .6, .28], 'Hips', 6, [.1, 0, 0]);
  rock([0, 3.5, -.55], [1.2, .6, .8], 'Chest');
  a.plate('stone', [0, 3.7, -.5], [1.3, .6, .5], 'Chest', 8, [-.6, 0, 0]);
  a.plate('stone', [-.85, 3.4, -.8], [.8, .9, .4], 'Chest', 9, [-.2, -.5, .1]);
  a.plate('stone', [.85, 3.4, -.8], [.8, .9, .4], 'Chest', 10, [-.2, .5, -.1]);
  mossAt([0, 3.95, -.5], .45, 'Chest'); mossAt([-.5, 3.7, 1.1], .35, 'Chest'); mossAt([.2, 2.5, .9], .3, 'Spine'); mossAt([-.7, 2.3, .8], .25, 'Hips'); shelf([.9, 3.3, 1.0], .25, 'Chest'); shelf([-1.0, 3.0, .9], .2, 'Chest'); mossAt([.6, 3.7, 1.0], .22, 'Chest');

  // ---- neck & head (head pushed forward of the shoulders) ----
  braid([[0, 3.4, .5], [0, 3.75, .9], [0, 4.0, 1.3]], .55, 'Neck', 3, 3);
  a.ell('bark', [0, 4.0, 1.4], [.6, .55, .65], 'Head');
  a.plate('stone', [0, 4.35, 1.6], [.85, .8, .35], 'Head', 11, [.45, 0, 0]);
  a.plate('stone', [0, 3.7, 1.85], [.6, .8, .3], 'Head', 12, [.95, 0, 0]);
  a.plate('stone', [-.5, 4.1, 1.3], [.3, .6, .3], 'Head', 13, [0, -.8, .2]);
  a.plate('stone', [.5, 4.1, 1.3], [.3, .6, .3], 'Head', 14, [0, .8, -.2]);
  a.ell('eye', [-.27, 4.1, 1.93], [.12, .07, .07], 'Head');
  a.ell('eye', [.27, 4.1, 1.93], [.12, .07, .07], 'Head');
  mossAt([0, 4.6, 1.5], .25, 'Head');

  // ---- antlers ----
  for (const [sd, X] of sides) {
    const b = 'Antler' + sd;
    const P = (x: number, y: number, z: number): V => [X * x, 4.2 + y * .5, 1.2 + z];
    const main = curve([P(.3, 0, 0), P(.55, .4, -.1), P(.95, .7, -.2), P(1.5, .8, -.1), P(1.95, 1.0, -.05)], 16);
    a.tube('bark', main, main.map((_, i) => .13 * (1 - i / main.length * .8) + .02), b, 7);
    const br = (pts: V[], r: number) => { const c = curve(pts, 8); a.tube('bark', c, c.map((_, i) => r * (1 - i / c.length * .85) + .015), b, 6); };
    br([P(.95, .7, -.2), P(1.05, 1.0, -.2), P(1.0, 1.4, -.1)], .07);
    br([P(1.5, .8, -.1), P(1.55, 1.2, -.1), P(1.8, 1.5, -.1)], .06);
    br([P(.6, .4, -.1), P(.5, .8, -.15), P(.65, 1.1, -.2)], .06);
    mossAt(P(1.0, .75, -.2), .12, b);
  }

  // ---- arms ----
  for (const [sd, X] of sides) {
    const S = 'Shoulder' + sd, U = 'UpperArm' + sd, F = 'Forearm' + sd, H = 'Hand' + sd;
    const q = X > 0 ? 1 : 0;
    rock([X * 1.55, 3.5, -.05], [.8, .55, .7], S);
    a.plate('stone', [X * 1.7, 3.65, .0], [.9, .6, .55], S, 20 + q, [-.4, X * .2, X * -.2]);
    a.plate('stone', [X * 1.7, 3.55, .5], [.7, .8, .35], S, 22 + q, [.1, X * .5, 0]);
    mossAt([X * 1.6, 4.0, -.1], .45, S); mossAt([X * 1.15, 3.95, .3], .3, S); shelf([X * 2.1, 3.9, .3], .22, S);
    braid([[X * 1.3, 3.55, .1], [X * 1.6, 3.0, .25], [X * 1.85, 2.45, .45]], .5, U, 3, 3);
    a.ell('bark', [X * 1.6, 3.0, .25], [.4, .6, .4], U);
    a.plate('stone', [X * 2.0, 3.0, .35], [.5, .9, .45], U, 30 + q, [0, X * .6, X * -.1]);
    braid([[X * 1.85, 2.45, .45], [X * 1.9, 1.9, .6], [X * 1.95, 1.45, .8]], .45, F, 3, 3);
    a.ell('bark', [X * 1.9, 1.95, .62], [.4, .6, .4], F);
    a.plate('stone', [X * 2.25, 2.1, .6], [.55, 1.2, .55], F, 40 + q, [0, X * .5, X * -.15]);
    a.plate('stone', [X * 1.9, 2.15, 1.0], [.6, .9, .35], F, 42 + q, [.2, 0, 0]);
    mossAt([X * 2.2, 2.8, .6], .35, F); mossAt([X * 1.9, 1.7, 1.0], .2, F); shelf([X * 2.5, 2.2, .6], .2, F);
    a.ell('bark', [X * 1.95, 1.35, .85], [.35, .3, .35], H);
    a.ell('stone', [X * 1.95, 1.5, .8], [.3, .2, .3], H, 3, true);
    for (let i = 0; i < 3; i++) {
      const o = (i - 1) * .22;
      claw([X * 1.95 + o, 1.25, .95], [o * .5, -1, .35], 1.0 - Math.abs(i - 1) * .1, H, .1);
    }
    claw([X * 1.7, 1.3, 1.0], [-X * .3, -.8, .5], .75, H, .08);
  }

  // ---- legs ----
  for (const [sd, X] of sides) {
    const Th = 'Thigh' + sd, Sh = 'Shin' + sd, Ft = 'Foot' + sd;
    const q = X > 0 ? 1 : 0;
    braid([[X * .6, 2.1, -.05], [X * .75, 1.6, .15], [X * .8, 1.1, .35]], .6, Th, 3, 3);
    a.ell('bark', [X * .7, 1.7, .05], [.55, .6, .55], Th);
    a.plate('stone', [X * .95, 1.8, .45], [.7, .8, .4], Th, 50 + q, [0, X * .4, 0]);
    a.plate('stone', [X * .75, 1.45, .8], [.55, .6, .35], Th, 52 + q, [.1, 0, 0]);
    mossAt([X * .7, 2.2, .1], .28, Th);
    braid([[X * .8, 1.1, .35], [X * .85, .7, .3], [X * .85, .35, .3]], .45, Sh, 3, 3);
    a.ell('bark', [X * .82, .8, .32], [.45, .5, .45], Sh);
    a.plate('stone', [X * .85, .95, .75], [.55, .7, .3], Sh, 54 + q, [.2, 0, 0]);
    a.plate('stone', [X * 1.1, .9, .3], [.4, .8, .4], Sh, 56 + q, [0, X * .6, 0]);
    a.ell('stone', [X * .85, .3, .45], [.55, .3, .75], Ft, 60 + q, true);
    for (let i = 0; i < 3; i++)
      a.plate('stone', [X * .85 + (i - 1) * .35, .22, 1.0], [.32, .4, .4], Ft, 62 + i + q * 5, [.3, 0, 0]);
    mossAt([X * .85, .58, .35], .3, Ft);
  }

  // ---- animation: right arm heavy slash, 1.2s ----
  const clip = a.doc.createAnimation('attack');
  const t = [0, .35, .5, .62, .8, 1.2];
  a.channel(clip, 'ShoulderR', t, [[0,0,0],[.3,0,.35],[.4,0,.4],[-.5,0,-.15],[-.2,0,-.05],[0,0,0]]);
  a.channel(clip, 'UpperArmR', t, [[0,0,0],[2.5,0,.4],[2.7,0,.5],[-1.1,0,-.2],[-.7,0,-.1],[0,0,0]]);
  a.channel(clip, 'ForearmR', t, [[0,0,0],[-.9,0,0],[-1.1,0,0],[-.3,0,0],[-.2,0,0],[0,0,0]]);
  a.channel(clip, 'HandR', t, [[0,0,0],[.3,0,0],[.5,0,0],[-.5,0,0],[-.2,0,0],[0,0,0]]);
  a.channel(clip, 'Chest', t, [[0,0,0],[-.12,.35,0],[-.15,.4,0],[.22,-.4,0],[.1,-.2,0],[0,0,0]]);
  a.channel(clip, 'Spine', t, [[0,0,0],[-.05,.15,0],[-.06,.2,0],[.12,-.2,0],[.05,-.1,0],[0,0,0]]);
  a.channel(clip, 'Head', t, [[0,0,0],[-.15,0,0],[-.2,0,0],[.25,0,0],[.1,0,0],[0,0,0]]);
  a.channel(clip, 'UpperArmL', t, [[0,0,0],[.1,0,0],[.15,0,0],[-.2,0,0],[-.1,0,0],[0,0,0]]);
  a.channel(clip, 'Hips', t, [[0,0,0],[-.05,.1,0],[-.06,.12,0],[.1,-.1,0],[.04,0,0],[0,0,0]]);
  return a;
}
