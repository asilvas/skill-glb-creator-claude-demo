import { Asset, type V } from '../scripts/geometry';
import * as T from 'three';

const TX = 'C:/Users/aaron/skill-glb-creator-claude-demo/assets/textures/';
const rd = async (f: string) => new Uint8Array(await Bun.file(TX + f).arrayBuffer());

export default async function build() {
  const a = new Asset();
  for (const m of ['stone', 'bark', 'ivory', 'moss']) {
    const ext = m === 'moss' ? 'albedo.png' : 'albedo.jpg';
    a.surfaces.set(m, {
      baseColor: await rd(`${m}-${ext}`),
      normal: await rd(`${m}-normal.png`),
      roughness: await rd(`${m}-roughness.png`),
      normalScale: 0.8,
    });
  }

  // ---- skeleton
  a.joint('Root', [0, 0, 0]);
  a.joint('Hips', [0, 1.9, 0], 'Root');
  a.joint('Chest', [0, 2.6, .15], 'Hips');
  a.joint('Head', [0, 3.7, .8], 'Chest');
  for (const [n, s] of [['L', 1], ['R', -1]] as const) {
    a.joint('Shoulder' + n, [s * 1.25, 3.3, .1], 'Chest');
    a.joint('Elbow' + n, [s * 1.65, 2.3, .3], 'Shoulder' + n);
    a.joint('Hand' + n, [s * 1.6, 1.2, .75], 'Elbow' + n);
    a.joint('Thigh' + n, [s * .65, 1.9, 0], 'Hips');
    a.joint('Shin' + n, [s * .85, 1.0, .4], 'Thigh' + n);
    a.joint('Foot' + n, [s * .85, .3, .15], 'Shin' + n);
  }

  const plate0 = a.plate.bind(a);
  (a as any).plate = (m: string, c: V, sz: V, b: string, seed?: number, rot?: V) => plate0(m, c, [sz[0]*.7, sz[1]*.7, sz[2]*.8] as V, b, seed, rot);
  const ell0 = a.ell.bind(a);
  (a as any).ell = (m: string, c: V, r: V, b: string, seed?: number, rock?: boolean) => m === 'moss' ? ell0(m, c, [r[0]*1.7, r[1]*2.6, r[2]*1.7] as V, b, seed, rock) : ell0(m, c, r, b, seed, rock);
  const curve = (pts: V[], n = 14) =>
    new T.CatmullRomCurve3(pts.map(p => new T.Vector3(...p))).getPoints(n).map(p => [p.x, p.y, p.z] as V);
  // braided root: several strands twisted around a spine
  const rope = (pts: V[], r: number, bone: string, strands = 4, twist = 2.5, mat = 'bark') => {
    const sp = curve(pts, 16);
    for (let k = 0; k < strands; k++) {
      const path: V[] = sp.map((p, i) => {
        const t = i / (sp.length - 1);
        const ang = (k / strands) * Math.PI * 2 + t * twist * Math.PI * 2;
        const nx = Math.cos(ang) * r * .7, nz = Math.sin(ang) * r * .7;
        return [p[0] + nx, p[1], p[2] + nz] as V;
      });
      a.tube(mat, path, path.map((_, i) => r * (.8 + .12 * Math.sin(i + k))), bone, 6);
    }
  };

  // ---- torso
  a.ell('bark', [0, 2.9, .2], [1.0, .95, .75], 'Chest', 1);
  rope([[-.8, 2.2, .3], [-.3, 2.9, .75], [.4, 3.3, .7], [.9, 3.0, .4]], .3, 'Chest', 3);
  rope([[.8, 2.2, .3], [.3, 2.9, .78], [-.4, 3.3, .7], [-.9, 3.0, .4]], .28, 'Chest', 3, 2);
  rope([[0, 2.7, -.6], [.3, 3.2, -.5], [0, 3.7, -.2]], .35, 'Chest', 3);
  a.ell('bark', [0, 1.95, 0], [.85, .65, .65], 'Hips', 2);
  rope([[-.5, 1.6, .3], [0, 2.1, .6], [.5, 1.6, .3]], .25, 'Hips', 3);
  // chest plates
  a.plate('stone', [-.35, 3.0, .85], [.8, .75, .35], 'Chest', 3, [.1, .15, .1]);
  a.plate('stone', [.45, 2.75, .8], [.75, .7, .3], 'Chest', 4, [.05, -.2, -.1]);
  a.plate('stone', [0, 2.2, .75], [.8, .55, .3], 'Chest', 5, [.3, 0, 0]);
  a.plate('stone', [0, 3.4, -.7], [1.2, .9, .4], 'Chest', 6, [-.1, Math.PI, 0]);
  a.plate('stone', [-.5, 2.8, -.7], [.7, .8, .35], 'Chest', 7, [0, Math.PI, .2]);
  a.plate('stone', [0, 1.7, .65], [.7, .5, .3], 'Hips', 8, [.2, 0, 0]);
  a.plate('stone', [0, 1.9, -.6], [.9, .6, .3], 'Hips', 9, [0, Math.PI, 0]);
  // moss patches + fungus
  a.ell('moss', [-.2, 3.45, .55], [.5, .15, .35], 'Chest', 1);
  a.ell('moss', [.7, 2.5, .55], [.25, .12, .2], 'Chest', 2);
  for (let i = 0; i < 4; i++) a.ell('ivory', [2.0 + i * .02, 3.9 - i * .14, .4], [.25 - i * .02, .05, .22 - i * .02], 'ShoulderL', i);

  a.ell('moss', [-1.9, 3.85, .3], [.3, .08, .3], 'ShoulderR', 4);
  a.ell('moss', [.5, 3.6, -.6], [.4, .08, .3], 'Chest', 4);
  a.ell('moss', [0, 1.5, .6], [.3, .08, .3], 'Hips', 4);
  // ---- head
  a.ell('stone', [0, 3.95, 1.05], [.42, .5, .45], 'Head', 3, true);
  a.plate('stone', [0, 4.05, 1.40], [.6, .75, .3], 'Head', 11, [-.15, 0, 0]);
  a.plate('stone', [0, 3.55, 1.30], [.4, .5, .25], 'Head', 12, [.5, 0, 0]);
  a.plate('stone', [0, 4.40, 0.90], [.7, .5, .45], 'Head', 13, [.5, 0, 0]);
  a.ell('bark', [0, 3.65, 0.90], [.6, .4, .5], 'Head', 14);
  a.ell('eye', [-.2, 4.07, 1.62], [.12, .08, .08], 'Head');
  a.ell('eye', [.2, 4.07, 1.62], [.12, .08, .08], 'Head');
  a.ell('moss', [0, 4.55, 0.90], [.3, .1, .25], 'Head', 2);
  // antlers
  for (const s of [1, -1]) {
    const main = [[s * .35, 4.35, 0.80], [s * .7, 4.75, 0.70], [s * 1.2, 4.90, 0.60], [s * 1.8, 5.25, 0.70]] as V[];
    a.tube('bark', curve(main, 14), curve(main, 14).map((_, i) => .15 - i * .007), 'Head', 7);
    const b1 = [[s * .8, 4.80, 0.70], [s * .95, 5.25, 0.60], [s * .85, 5.65, 0.65]] as V[];
    a.tube('bark', curve(b1, 8), curve(b1, 8).map((_, i) => .09 - i * .006), 'Head', 6);
    const b2 = [[s * 1.3, 4.93, 0.60], [s * 1.5, 5.30, 0.80], [s * 1.55, 5.55, 1.00]] as V[];
    a.tube('bark', curve(b2, 8), curve(b2, 8).map((_, i) => .08 - i * .006), 'Head', 6);
    const b3 = [[s * 1.8, 5.25, 0.70], [s * 2.0, 5.45, 0.50], [s * 2.3, 5.55, 0.40]] as V[];
    a.tube('bark', curve(b3, 8), curve(b3, 8).map((_, i) => .07 - i * .006), 'Head', 6);
    a.ell('moss', [s * 1.2, 4.90, 0.60], [.15, .1, .12], 'Head', 1);
  }

  // ---- arms & legs
  for (const [n, s] of [['L', 1], ['R', -1]] as const) {
    const sh = 'Shoulder' + n, el = 'Elbow' + n, ha = 'Hand' + n;
    a.ell('stone', [s * 1.45, 3.45, -.05], [.7, .5, .65], sh, s > 0 ? 5 : 6, true);
    a.plate('stone', [s * 1.6, 3.75, .0], [.8, .55, .6], sh, 20 + s, [0, 0, s * .3]);
    a.ell('moss', [s * 1.5, 3.9, 0], [.3, .08, .3], sh, 3);
    rope([[s * 1.2, 3.2, .1], [s * 1.6, 2.8, .2], [s * 1.7, 2.3, .3]], .38, sh, 3);
    a.plate('stone', [s * 1.9, 2.7, .25], [.5, 1.0, .5], sh, 30 + s, [0, 0, s * .15]);
    rope([[s * 1.65, 2.3, .3], [s * 1.7, 1.7, .5], [s * 1.6, 1.1, .75]], .4, el, 3);
    a.plate('stone', [s * 1.95, 1.8, .5], [.5, 1.1, .6], el, 40 + s, [.1, 0, s * .1]);
    a.plate('stone', [s * 1.6, 1.9, .95], [.7, .8, .35], el, 45 + s, [.2, 0, 0]);
    a.ell('moss', [s * 1.85, 1.2, .5], [.2, .12, .2], el, 2);
    a.ell('bark', [s * 1.6, .95, .85], [.4, .35, .4], ha, 4);
    for (let c = 0; c < 3; c++) {
      const x = s * (1.35 + c * .25);
      const cl = [[x, .95, 1.0], [x + s * .03, .5, 1.45], [x + s * .05, -.05, 1.6]] as V[];
      a.tube('ivory', curve(cl, 9), curve(cl, 9).map((_, i) => .19 - i * .02), ha, 6);
    }
    const th = 'Thigh' + n, sn = 'Shin' + n, ft = 'Foot' + n;
    rope([[s * .6, 2.1, 0], [s * .9, 1.5, .3], [s * .85, 1.0, .4]], .42, th, 3);
    a.plate('stone', [s * 1.1, 1.6, .25], [.5, .8, .5], th, 50 + s, [0, 0, s * .2]);
    a.plate('stone', [s * .8, 1.3, .8], [.6, .5, .35], th, 55 + s, [.3, 0, 0]);
    rope([[s * .85, 1.0, .4], [s * .8, .6, .3], [s * .85, .3, .15]], .38, sn, 3);
    a.plate('stone', [s * .85, .75, .65], [.5, .7, .3], sn, 60 + s, [.2, 0, 0]);
    a.ell('moss', [s * 1.0, 1.15, .45], [.2, .12, .2], th, 2);
    a.ell('stone', [s * .85, .25, .35], [.55, .28, .75], ft, 70 + s, true);
    for (let t = 0; t < 3; t++) a.ell('stone', [s * (.55 + t * .3), .18, 1.0], [.2, .18, .25], ft, 80 + t, true);
    a.ell('moss', [s * .85, .5, .2], [.3, .1, .3], ft, 5);
  }

  // ---- animation: heavy right-arm slash (creature right = -X)
  const clip = a.doc.createAnimation('attack');
  const t = [0, .35, .55, .65, .9, 1.2];
  a.channel(clip, 'ShoulderR', t, [[0,0,0],[2.4,0,-.5],[2.4,0,-.5],[-.7,0,.25],[-.4,0,.1],[0,0,0]]);
  a.channel(clip, 'ElbowR', t, [[0,0,0],[-.6,0,0],[-.6,0,0],[-.1,0,0],[-.15,0,0],[0,0,0]]);
  a.channel(clip, 'Chest', t, [[0,0,0],[-.1,.5,0],[-.1,.5,0],[.15,-.55,0],[.05,-.2,0],[0,0,0]]);
  a.channel(clip, 'Hips', t, [[0,0,0],[-.08,.2,0],[-.08,.2,0],[.12,-.25,0],[.04,-.08,0],[0,0,0]]);
  a.channel(clip, 'Head', t, [[0,0,0],[.1,.2,0],[.1,.2,0],[.15,-.3,0],[.05,-.1,0],[0,0,0]]);
  a.channel(clip, 'ShoulderL', t, [[0,0,0],[.2,0,.1],[.2,0,.1],[-.3,0,0],[-.1,0,0],[0,0,0]]);
  for (const n of a.doc.getRoot().listScenes()[0].listChildren()) n.setScale([.85, .85, .85]);
  return a;
}
