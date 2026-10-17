import { Asset, type V } from '../scripts/geometry';
const T = 'C:/Users/aaron/skill-glb-creator-claude-demo/assets/textures/';
const rd = async (f: string) => new Uint8Array(await Bun.file(T + f).arrayBuffer());

export default async function build() {
  const a = new Asset();
  a.joint('Root', [0, 0, 0]);
  a.joint('Hips', [0, 1.9, 0], 'Root');
  a.joint('Chest', [0, 2.6, .2], 'Hips');
  a.joint('Head', [0, 3.4, .75], 'Chest');
  for (const [n, s] of [['L', 1], ['R', -1]] as [string, number][]) {
    a.joint('Shoulder' + n, [s * 1.1, 3.2, .2], 'Chest');
    a.joint('Elbow' + n, [s * 1.65, 2.2, .45], 'Shoulder' + n);
    a.joint('Hand' + n, [s * 1.55, 1.2, .95], 'Elbow' + n);
    a.joint('Thigh' + n, [s * .65, 1.9, 0], 'Hips');
    a.joint('Knee' + n, [s * .85, 1.0, .5], 'Thigh' + n);
    a.joint('Foot' + n, [s * .85, .3, .15], 'Knee' + n);
  }
  for (const m of ['stone', 'bark', 'moss', 'ivory']) {
    const ext = m === 'moss' ? 'png' : 'jpg';
    a.surfaces.set(m, {
      baseColor: await rd(`${m}-albedo.${ext}`),
      normal: await rd(`${m}-normal.png`),
      roughness: await rd(`${m}-roughness.png`),
      normalScale: .8,
    });
  }
  const P = (m: string, c: V, z: V, b: string, s: number, r: V) => a.plate(m, c, [z[0] * .68, z[1] * .68, z[2] * .6] as V, b, s, r);
  let sd = 1;
  const S = () => sd++;

  // Torso: braided bark core
  a.ell('bark', [0, 2.0, .05], [.8, .6, .6], 'Hips');
  a.ell('bark', [0, 2.9, .3], [1.0, .75, .75], 'Chest');
  a.ell('bark', [0, 2.5, .15], [.8, .6, .6], 'Chest');
  for (let i = 0; i < 5; i++) a.tube('bark', [[-.6 + i * .3, 2.0, .5], [-.4 + i * .2, 2.8, .75], [-.3 + i * .15, 3.4, .6]], [.16, .12, .1], 'Chest');
  P('stone', [.35, 2.9, .95], [.8, .8, .3], 'Chest', S(), [.1, .2, .1]);
  P('stone', [-.4, 2.7, .9], [.7, .7, .3], 'Chest', S(), [.1, -.3, 0]);
  P('stone', [0, 2.2, .8], [.8, .5, .25], 'Chest', S(), [-.3, 0, 0]);
  P('stone', [0, 3.5, -.35], [1.6, .9, .8], 'Chest', S(), [.2, 0, 0]);
  P('stone', [0, 3.0, -.7], [1.1, .8, .5], 'Chest', S(), [.3, .2, 0]);
  a.ell('moss', [0, 3.95, -.3], [.7, .3, .5], 'Chest', S(), true);
  P('stone', [0, 1.9, .55], [.8, .5, .3], 'Hips', S(), [.1, 0, 0]);
  P('stone', [0, 1.9, -.6], [1.0, .6, .3], 'Hips', S(), [.1, 3.1, 0]);

  // Head
  a.ell('bark', [0, 3.5, .75], [.4, .4, .45], 'Head');
  P('stone', [0, 3.65, 1.0], [.7, .8, .45], 'Head', S(), [.35, 0, 0]);
  P('stone', [0, 3.2, 1.05], [.5, .6, .3], 'Head', S(), [-.4, 0, 0]);
  P('stone', [0, 3.95, .6], [.7, .4, .5], 'Head', S(), [.4, 0, 0]);
  for (const s of [1, -1]) {
    a.ell('eye', [s * .2, 3.55, 1.2], [.07, .05, .05], 'Head');
    P('stone', [s * .55, 3.5, .6], [.3, .6, .25], 'Head', S(), [0, s * 1.0, 0]);
    const b: V[] = [[s * .3, 3.9, .55], [s * .6, 4.2, .4], [s * 1.1, 4.7, .3], [s * 1.5, 5.05, .3]];
    a.tube('bark', b, [.14, .1, .08, .04], 'Head', 8);
    a.tube('bark', [b[1], [s * .55, 4.8, .1], [s * .5, 5.3, 0]], [.06, .045, .02], 'Head');
    a.tube('bark', [b[2], [s * 1.7, 4.95, .6], [s * 2.0, 5.25, .7]], [.05, .04, .015], 'Head');
    a.tube('bark', [b[3], [s * 1.2, 5.45, .2]], [.04, .015], 'Head');
    a.ell('moss', [s * .7, 4.3, .4], [.12, .1, .12], 'Head', S());
  }
  a.ell('moss', [.2, 3.95, .8], [.25, .08, .25], 'Head', S(), true);

  for (const [n, s] of [['L', 1], ['R', -1]] as [string, number][]) {
    P('stone', [s * 1.25, 3.6, .1], [1.2, .9, 1.0], 'Shoulder' + n, S(), [.2, s * .3, s * .2]);
    P('stone', [s * 1.5, 3.4, .5], [.8, .7, .6], 'Shoulder' + n, S(), [0, s * .6, 0]);
    a.ell('moss', [s * 1.2, 4.05, .1], [.5, .28, .4], 'Shoulder' + n, S(), true);
    a.ell('bark', [s * 1.2, 3.2, .2], [.5, .5, .5], 'Shoulder' + n);
    for (let k = 0; k < 3; k++) {
      const o = (k - 1) * .13;
      a.tube('bark', [[s * 1.15 + o, 3.2, .2], [s * 1.5 + o, 2.7, .35], [s * 1.65 + o, 2.2, .45]], [.4, .36, .32], 'Shoulder' + n);
    }
    P('stone', [s * 1.85, 2.6, .4], [.35, .9, .6], 'Shoulder' + n, S(), [0, s * .5, s * .1]);
    a.ell('bark', [s * 1.65, 2.2, .45], [.33, .33, .33], 'Elbow' + n);
    for (let k = 0; k < 3; k++) {
      const o = (k - 1) * .13;
      a.tube('bark', [[s * 1.65 + o, 2.2, .45], [s * 1.62 + o, 1.7, .75], [s * 1.55 + o, 1.2, .95]], [.36, .38, .3], 'Elbow' + n);
    }
    P('stone', [s * 1.95, 1.8, .6], [.4, 1.1, .7], 'Elbow' + n, S(), [0, s * .4, 0]);
    P('stone', [s * 1.55, 1.9, 1.05], [.6, .8, .3], 'Elbow' + n, S(), [.2, 0, 0]);
    a.ell('moss', [s * 1.95, 2.35, .6], [.3, .15, .4], 'Elbow' + n, S(), true);
    for (let k = 0; k < 3; k++) a.ell('ivory', [s * (2.05 + .04 * k), 2.0 - .2 * k, .6], [.12, .03, .1], 'Elbow' + n, S());
    a.ell('bark', [s * 1.55, 1.15, .95], [.3, .25, .3], 'Hand' + n);
    for (let k = 0; k < 3; k++) {
      const x = s * (1.55 + (k - 1) * .22);
      a.tube('ivory', [[x, 1.1, .95], [x + s * (k - 1) * .05, .8, 1.15], [x, .4, 1.5], [x, .05, 1.75]], [.16, .13, .08, .01], 'Hand' + n, 6);
    }
    a.ell('bark', [s * .65, 1.9, 0], [.5, .5, .5], 'Thigh' + n);
    for (let k = 0; k < 3; k++) {
      const o = (k - 1) * .12;
      a.tube('bark', [[s * .65 + o, 1.9, 0], [s * .8 + o, 1.45, .3], [s * .85 + o, 1.0, .5]], [.42, .38, .34], 'Thigh' + n);
      a.tube('bark', [[s * .85 + o, 1.0, .5], [s * .85 + o, .6, .3], [s * .85 + o, .3, .15]], [.36, .32, .32], 'Knee' + n);
    }
    P('stone', [s * 1.05, 1.5, .25], [.4, .9, .6], 'Thigh' + n, S(), [0, s * .4, 0]);
    P('stone', [s * .8, 1.15, .85], [.55, .5, .35], 'Knee' + n, S(), [-.3, 0, 0]);
    P('stone', [s * 1.1, .7, .3], [.35, .8, .5], 'Knee' + n, S(), [0, s * .4, 0]);
    a.ell('moss', [s * 1.0, 1.85, .2], [.3, .12, .35], 'Thigh' + n, S(), true);
    for (let k = 0; k < 4; k++) a.ell('stone', [s * (.65 + k * .12), .2, .35 + k * .12], [.28, .2, .3], 'Foot' + n, S(), true);
    a.ell('stone', [s * .85, .22, .1], [.55, .22, .5], 'Foot' + n, S(), true);
    a.ell('moss', [s * .85, .42, .3], [.45, .1, .45], 'Foot' + n, S(), true);
  }
  for (const [p, bn] of [[[-1.0, 4.0, -.1], 'Chest'], [[1.4, 3.6, .9], 'Chest'], [[-2.1, 2.4, .5], 'ShoulderR'], [[.6, 3.1, -.9], 'Chest']] as [V, string][])
    for (let k = 0; k < 3; k++) a.ell('ivory', [p[0], p[1] - k * .12, p[2] + k * .04], [.2 - k * .03, .03, .17 - k * .03], bn, S());

  const clumps: [V, string, number][] = [[[-.5,3.9,-.4],'Chest',.3],[[.5,3.8,-.2],'Chest',.25],[[0,3.3,-.9],'Chest',.28],[[.9,3.2,.9],'Chest',.22],[[-.8,2.3,.9],'Chest',.2],[[.3,4.0,.4],'Head',.2],[[-.3,3.0,1.0],'Head',.14],[[1.0,3.9,.5],'ShoulderL',.3],[[-1.5,3.7,.7],'ShoulderR',.28],[[2.0,2.7,.8],'ShoulderL',.2],[[-2.0,2.0,.9],'ElbowR',.22],[[1.9,1.7,1.0],'ElbowL',.22],[[1.0,1.9,.7],'ThighL',.2],[[-1.0,1.7,.6],'ThighR',.2],[[.9,1.2,1.0],'KneeL',.18],[[-.8,.5,.8],'KneeR',.2]];
  clumps.forEach(([p, bn, r]) => { for (let k = 0; k < 3; k++) a.ell('moss', [p[0] + (k - 1) * r * .8, p[1] + (k % 2) * r * .3, p[2] + (k - 1) * r * .3], [r, r * .8, r], bn, S(), true); });
  const clip = a.doc.createAnimation('attack');
  const t = [0, .35, .55, .7, 1.2];
  a.channel(clip, 'ShoulderR', t, [[0, 0, 0], [-1.6, -.3, -.7], [.9, .4, .5], [.7, .3, .4], [0, 0, 0]]);
  a.channel(clip, 'ElbowR', t, [[0, 0, 0], [-.8, 0, 0], [.2, 0, 0], [.3, 0, 0], [0, 0, 0]]);
  a.channel(clip, 'Chest', t, [[0, 0, 0], [-.1, .5, 0], [.15, -.6, 0], [.1, -.5, 0], [0, 0, 0]]);
  a.channel(clip, 'Hips', t, [[0, 0, 0], [-.1, .2, 0], [.1, -.25, 0], [.1, -.2, 0], [0, 0, 0]]);
  a.channel(clip, 'Head', t, [[0, 0, 0], [.15, .2, 0], [.1, -.3, 0], [.05, -.25, 0], [0, 0, 0]]);
  a.channel(clip, 'ShoulderL', t, [[0, 0, 0], [.3, 0, .1], [-.4, 0, 0], [-.3, 0, 0], [0, 0, 0]]);
  a.scale(.86);
  return a;
}
