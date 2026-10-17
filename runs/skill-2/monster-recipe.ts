import { Asset, type V } from '../scripts/geometry';
import * as T from 'three';
const TX = 'C:/Users/aaron/skill-glb-creator-claude-demo/assets/textures/';
const rd = async (f: string) => new Uint8Array(await Bun.file(TX + f).arrayBuffer());

function curve(pts: V[], n = 14): V[] {
  const c = new T.CatmullRomCurve3(pts.map(p => new T.Vector3(...p)));
  return c.getPoints(n).map(v => [v.x, v.y, v.z] as V);
}

function rs(r: number[], n: number) {
  return Array.from({ length: n }, (_, i) => {
    const f = i / (n - 1) * (r.length - 1), k = Math.min(Math.floor(f), r.length - 2);
    return r[k] + (r[k + 1] - r[k]) * (f - k);
  });
}
const sc = (v: V): V => [v[0] * .6, v[1] * .6, v[2] * .6];
function mossy(a: Asset, c: V, r: V, bone: string, seed: number) {
  a.ell('moss', c, [r[0] * .75, Math.max(r[0], r[2]) * .5, r[2] * .75], bone, seed, true);
}
export default async function build() {
  const a = new Asset();
  for (const m of ['stone', 'bark', 'moss', 'ivory']) {
    const ext = m === 'moss' ? 'png' : 'jpg';
    a.surfaces.set(m, {
      baseColor: await rd(`${m}-albedo.${ext}`), normal: await rd(`${m}-normal.png`),
      roughness: await rd(`${m}-roughness.png`), normalScale: .8, ...(m==='bark'?{tint:[1,.8,.65]}:m==='moss'?{tint:[.9,1,.7]}:{}),
    } as any);
  }
  a.joint('Root', [0, 0, 0]);
  a.joint('Hips', [0, 2.1, 0], 'Root');
  a.joint('Chest', [0, 2.9, .15], 'Hips');
  a.joint('Head', [0, 3.85, .5], 'Chest');
  const sides: [number, string][] = [[-1, 'L'], [1, 'R']];
  for (const [s, n] of sides) {
    a.joint('Thigh' + n, [s * .75, 2.2, 0], 'Hips');
    a.joint('Shin' + n, [s * .85, 1.25, .45], 'Thigh' + n);
    a.joint('Foot' + n, [s * .85, .4, .1], 'Shin' + n);
    a.joint('Shoulder' + n, [s * 1.35, 3.6, .1], 'Chest');
    a.joint('Elbow' + n, [s * 1.95, 2.5, .35], 'Shoulder' + n);
    a.joint('Hand' + n, [s * 1.9, 1.4, .85], 'Elbow' + n);
  }

  // torso
  a.ell('bark', [0, 2.2, 0], [.95, .75, .7], 'Hips', 1);
  a.ell('bark', [0, 3.0, .2], [1.2, .95, .85], 'Chest', 2);
  for (let i = 0; i < 6; i++) {
    const ang = i / 6 * 6.28;
    a.tube('bark', curve([[Math.cos(ang) * .9, 2.0, .5], [Math.cos(ang + 1) * 1.1, 2.9, .9 + Math.sin(i) * .1], [Math.cos(ang + 2) * 1.0, 3.6, .5]]), rs([.2, .22, .17], 15), 'Chest', 6);
  }
  a.plate('stone', [0, 3.0, .95], sc([1.1, .9, .35]), 'Chest', 3, [.1, 0, .1]);
  a.plate('stone', [-.5, 2.4, .75], sc([.7, .6, .3]), 'Chest', 4, [-.2, .2, .3]);
  a.plate('stone', [.55, 2.5, .8], sc([.6, .7, .3]), 'Chest', 5, [.1, -.2, -.2]);
  a.plate('stone', [0, 3.7, -.4], sc([1.6, .8, .5]), 'Chest', 6, [-.3, 0, 0]);
  a.plate('stone', [0, 2.0, .6], sc([.8, .5, .3]), 'Hips', 7, [.1, 0, 0]);
  a.ell('moss', [-.4, 3.5, .9], [0.400, 0.280, 0.280], 'Chest', 8, true);
  a.ell('moss', [.5, 2.8, 1.0], [0.240, 0.168, 0.160], 'Chest', 9, true);

  // head
  a.ell('bark', [0, 3.85, .4], [.62, .6, .6], 'Head', 10);
  a.plate('stone', [0, 3.95, .8], sc([.65, .85, .35]), 'Head', 11, [.15, 0, 0]);
  a.plate('stone', [0, 3.55, .85], sc([.45, .45, .3]), 'Head', 12, [-.4, 0, 0]);
  a.plate('stone', [0, 4.25, .3], sc([.7, .45, .5]), 'Head', 13, [-.4, 0, 0]);
  a.ell('eye', [-.2, 3.95, .95], [.09, .06, .06], 'Head');
  a.ell('eye', [.2, 3.95, .95], [.09, .06, .06], 'Head');
  a.ell('moss', [.25, 4.35, .35], [0.200, 0.140, 0.200], 'Head', 14, true);
  for (const s of [-1, 1]) {
    const main = curve([[s * .3, 4.2, .3], [s * .6, 4.55, .2], [s * 1.0, 4.8, .1], [s * 1.5, 4.95, .3], [s * 1.9, 5.2, .2]], 16);
    a.tube('bark', main, main.map((_, i) => .13 * (1 - i / 20)), 'Head', 6);
    for (const [k, dy, dx] of [[4, .6, .1], [8, .7, -.3], [11, .5, .4]]) {
      const p = main[k];
      const br = curve([p, [p[0] + s * .3 + dx * s, p[1] + dy * .5, p[2] - .1], [p[0] + s * .4 + dx * s, p[1] + dy, p[2] + .15]], 8);
      a.tube('bark', br, br.map((_, i) => .08 * (1 - i / 10)), 'Head', 5);
    }
    mossy(a, main[10], [.12, .12, .12], 'Head', 20);
  }

  // arms
  for (const [s, n] of sides) {
    const big = s < 0 ? 1.25 : 1;
    a.plate('stone', [s * 1.5, 3.9, 0], sc([1.3 * big, 1.1 * big, 1.0 * big]), 'Shoulder' + n, 20 + (s > 0 ? 1 : 0), [-.2, s * .3, s * .3]);
    a.plate('stone', [s * 1.9, 3.5, .5], sc([.8, .8, .5]), 'Shoulder' + n, 22, [0, s * .5, 0]);
    mossy(a, [s * 1.5, 4.45, 0], [0.88, 0.24, 0.72], 'Shoulder' + n, 23);
    a.ell('bark', [s * 1.4, 3.5, .1], [.6, .6, .6], 'Shoulder' + n, 24);
    for (let k = 0; k < 3; k++) {
      const o = (k - 1) * .13;
      a.tube('bark', curve([[s * 1.4 + o, 3.5, .1 + o], [s * 1.8 - o, 3.0, .3], [s * 1.95 + o, 2.5, .35 - o]]), rs([.3, .3, .27], 15), 'Shoulder' + n, 6);
    }
    a.plate('stone', [s * 2.1, 2.9, .3], sc([.55, .9, .6]), 'Shoulder' + n, 25 + (s > 0 ? 1 : 0), [0, s * .3, s * .2]);
    a.ell('bark', [s * 1.95, 2.45, .4], [.42, .42, .42], 'Elbow' + n, 27);
    for (let k = 0; k < 3; k++) {
      const o = (k - 1) * .15;
      a.tube('bark', curve([[s * 1.95 + o, 2.5, .35], [s * 1.95 - o, 1.9, .6], [s * 1.9 + o, 1.45, .85 + o]]), rs([.33, .3, .27], 15), 'Elbow' + n, 6);
    }
    a.plate('stone', [s * 2.2, 2.0, .65], sc([.6, 1.1, .7]), 'Elbow' + n, 28 + (s > 0 ? 1 : 0), [.1, s * .2, s * .1]);
    a.plate('stone', [s * 1.9, 2.2, 1.0], sc([.5, .7, .4]), 'Elbow' + n, 30, [-.1, 0, 0]);
    mossy(a, [s * 2.1, 2.7, .7], [0.56, 0.16, 0.48], 'Elbow' + n, 31);
    a.ell('bark', [s * 1.9, 1.35, .85], [.4, .35, .4], 'Hand' + n, 32);
    for (let k = 0; k < 3; k++) {
      const x = s * (1.9 + (k - 1) * .28);
      const cl = curve([[x, 1.35, .9], [x + s * (k - 1) * .05, .9, 1.3], [x, .35 + k * .05, 1.45 + k * .05]], 10);
      a.tube('ivory', cl, cl.map((_, i) => .2 * (1 - i / 11) + .015), 'Hand' + n, 6);
    }
  }

  // legs
  for (const [s, n] of sides) {
    for (let k = 0; k < 3; k++) {
      const o = (k - 1) * .15;
      a.tube('bark', curve([[s * .75 + o, 2.3, 0], [s * .85 - o, 1.8, .3], [s * .85 + o, 1.25, .45]]), rs([.4, .38, .33], 15), 'Thigh' + n, 6);
      a.tube('bark', curve([[s * .85 + o, 1.25, .45], [s * .85 - o, .8, .3], [s * .85, .45, .15]]), rs([.33, .3, .3], 15), 'Shin' + n, 6);
    }
    a.plate('stone', [s * 1.1, 1.85, .35], sc([.6, .9, .6]), 'Thigh' + n, 50 + (s > 0 ? 1 : 0), [0, s * .3, 0]);
    a.plate('stone', [s * .85, 1.2, .9], sc([.7, .55, .4]), 'Shin' + n, 52, [.2, 0, 0]);
    a.plate('stone', [s * 1.05, .8, .4], sc([.5, .7, .5]), 'Shin' + n, 53, [0, s * .2, 0]);
    mossy(a, [s * .85, 1.55, .85], [0.56, 0.16, 0.4], 'Shin' + n, 54);
    a.ell('stone', [s * .85, .3, .2], [.65, .3, .75], 'Foot' + n, 55 + (s > 0 ? 1 : 0), true);
    for (let k = 0; k < 4; k++) a.ell('stone', [s * (.85 + (k - 1.5) * .25), .2, .85 + (k % 2) * .1], [.2, .2, .28], 'Foot' + n, 60 + k, true);
    mossy(a, [s * .85, .6, .1], [0.64, 0.16, 0.64], 'Foot' + n, 66);
  }
  const fung: [V, string][] = [[[-1.9, 4.2, .6], 'ShoulderL'], [[-1.7, 3.8, .85], 'ShoulderL'], [[-2.3, 2.5, .8], 'ElbowL'], [[-2.35, 2.2, .75], 'ElbowL'], [[.9, 4.3, -.2], 'ShoulderR'], [[2.3, 3.5, .5], 'ShoulderR'], [[1.2, 1.6, .9], 'ThighR']];
  fung.forEach(([p, b], i) => a.ell('ivory', p, [.28, .05, .2], b, 70 + i));

  const clip = a.doc.createAnimation('attack');
  const t = [0, .35, .55, .7, 1.2];
  a.channel(clip, 'ShoulderR', t, [[0, 0, 0], [-1.3, .3, -.6], [.9, -.4, .3], [.7, -.4, .2], [0, 0, 0]]);
  a.channel(clip, 'ElbowR', t, [[0, 0, 0], [-.8, 0, 0], [.2, 0, 0], [.1, 0, 0], [0, 0, 0]]);
  a.channel(clip, 'HandR', t, [[0, 0, 0], [-.4, 0, 0], [.4, 0, 0], [.2, 0, 0], [0, 0, 0]]);
  a.channel(clip, 'Chest', t, [[0, 0, 0], [-.1, .5, 0], [.15, -.6, 0], [.1, -.5, 0], [0, 0, 0]]);
  a.channel(clip, 'Hips', t, [[0, 0, 0], [0, .15, 0], [.05, -.2, 0], [.04, -.15, 0], [0, 0, 0]]);
  a.channel(clip, 'Head', t, [[0, 0, 0], [-.1, .1, 0], [.2, -.2, 0], [.1, -.15, 0], [0, 0, 0]]);
  a.channel(clip, 'ShoulderL', t, [[0, 0, 0], [.2, 0, 0], [-.3, 0, 0], [-.2, 0, 0], [0, 0, 0]]);
  return a;
}
