// Hero image: reference vs best Blender-CLI result vs best skill result, one row with labels.
// Also renders an animated attack WebP of the best skill asset.
import sharp from '../skills/glb-creator/node_modules/sharp';
import { Preview } from '../skills/glb-creator/scripts/preview';
import { resolve } from 'node:path';
const root=resolve(import.meta.dir,'..');

const H=760,LABEL=56;
const panels=[
  {path:resolve(root,'assets/reference.png'),label:'Reference (concept art)'},
  {path:resolve(root,'results/eval/baseline-1.png'),label:'Agent + Blender CLI — 5.6 min, 113k tokens'},
  {path:resolve(root,'results/eval/skillv4-3.png'),label:'Agent + glb-creator — 1.6 min, 81k tokens'},
];
const imgs=await Promise.all(panels.map(async p=>{
  const b=await sharp(p.path).resize({height:H}).toBuffer({resolveWithObject:true});
  return {...p,buf:b.data,w:b.info.width};
}));
const W=imgs.reduce((a,i)=>a+i.w,0)+(imgs.length-1)*6;
let x=0;const comps:any[]=[],texts:string[]=[];
for(const i of imgs){
  comps.push({input:i.buf,left:x,top:0});
  texts.push(`<rect x="${x}" y="${H}" width="${i.w}" height="${LABEL}" fill="#1b1b1f"/><text x="${x+i.w/2}" y="${H+35}" text-anchor="middle" font-family="-apple-system,Segoe UI,sans-serif" font-size="21" font-weight="bold" fill="#fff">${i.label}</text>`);
  x+=i.w+6;
}
const svg=Buffer.from(`<svg width="${W}" height="${H+LABEL}" xmlns="http://www.w3.org/2000/svg">${texts.join('')}</svg>`);
const hero=await sharp({create:{width:W,height:H+LABEL,channels:3,background:'#1b1b1f'}}).composite([...comps,{input:svg,left:0,top:0}]).png().toBuffer();
await Bun.write(resolve(root,'results/charts/comparison.png'),hero);
console.log('comparison.png',W,'x',H+LABEL);

// Animated attack turntable of the best skill asset.
const p=await Preview.create();
try{
  const bytes=new Uint8Array(await Bun.file(resolve(root,'runs/skillv4-3/monster.glb')).arrayBuffer());
  await p.load(bytes);
  const N=18,size=420,frames:Buffer[]=[];
  for(let i=0;i<N;i++){
    const f=await p.frame({time:1.2*i/(N-1),yaw:-.5,size,format:'png'});
    frames.push(Buffer.from(f.bytes));
  }
  const anim=await sharp(frames,{join:{animated:true}})
    .webp({quality:80,loop:0,delay:Array(N).fill(67)}).toBuffer();
  await Bun.write(resolve(root,'results/charts/attack.webp'),anim);
  console.log('attack.webp',anim.length,'bytes');
}finally{await p.dispose();}
