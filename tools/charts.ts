// Generate README SVG charts from results/metrics.json.
//   bun tools/charts.ts [outDir]
import { resolve } from 'node:path';
const metrics=await Bun.file(resolve(import.meta.dir,'../results/metrics.json')).json();
const outDir=resolve(import.meta.dir,'..',process.argv[2]??'results/charts');

const ARMS:[string,string,string][]=[ // key, display, color
  ['blender-cli','Blender CLI','#e07a5f'],
  ['glb-creator-v2','skill v2','#b8c4c2'],
  ['glb-creator-v3','skill v3','#7fa8d9'],
  ['glb-creator-v4','skill v4 (final)','#3a86ff'],
];
const runs=Object.entries(metrics.runs) as [string,any][];
const byArm=(arm:string)=>runs.filter(([,r])=>r.arm===arm).map(([k,r])=>({run:k,...r}));
const mean=(xs:number[])=>xs.reduce((a,b)=>a+b,0)/xs.length;

function chart({title,unit,get,fmt,outFile}:{title:string,unit:string,get:(r:any)=>number,fmt:(v:number)=>string,outFile:string}){
  const groups=ARMS.map(([key,label,color])=>({label,color,values:byArm(key).map(get)})).filter(g=>g.values.length);
  const W=860,H=420,padL=70,padR=20,padT=64,padB=78;
  const maxV=Math.max(...groups.flatMap(g=>g.values))*1.15;
  const plotW=W-padL-padR,plotH=H-padT-padB;
  const groupW=plotW/groups.length;
  let bars='',labels='',means='';
  groups.forEach((g,gi)=>{
    const bw=Math.min(44,(groupW-40)/g.values.length);
    const x0=padL+gi*groupW+(groupW-bw*g.values.length-6*(g.values.length-1))/2;
    g.values.forEach((v,i)=>{
      const h=v/maxV*plotH,x=x0+i*(bw+6),y=padT+plotH-h;
      bars+=`<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${bw}" height="${h.toFixed(1)}" rx="4" fill="${g.color}"/>`;
      bars+=`<text x="${(x+bw/2).toFixed(1)}" y="${(y-6).toFixed(1)}" text-anchor="middle" font-size="12" fill="#555">${fmt(v)}</text>`;
    });
    const m=mean(g.values),my=padT+plotH-m/maxV*plotH;
    means+=`<line x1="${(padL+gi*groupW+14).toFixed(1)}" x2="${(padL+(gi+1)*groupW-14).toFixed(1)}" y1="${my.toFixed(1)}" y2="${my.toFixed(1)}" stroke="#222" stroke-width="2" stroke-dasharray="6 4"/>`;
    means+=`<text x="${(padL+(gi+.5)*groupW).toFixed(1)}" y="${(my-8).toFixed(1)}" text-anchor="middle" font-size="13" font-weight="bold" fill="#222">mean ${fmt(m)}</text>`;
    labels+=`<text x="${(padL+(gi+.5)*groupW).toFixed(1)}" y="${H-padB+28}" text-anchor="middle" font-size="15" font-weight="bold" fill="#333">${g.label}</text>`;
    labels+=`<text x="${(padL+(gi+.5)*groupW).toFixed(1)}" y="${H-padB+48}" text-anchor="middle" font-size="12" fill="#777">4 parallel agents</text>`;
  });
  const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" font-family="-apple-system,Segoe UI,sans-serif">
<rect width="${W}" height="${H}" fill="#ffffff" rx="10"/>
<text x="${W/2}" y="30" text-anchor="middle" font-size="19" font-weight="bold" fill="#111">${title}</text>
<text x="${W/2}" y="50" text-anchor="middle" font-size="13" fill="#666">${unit}</text>
<line x1="${padL}" x2="${W-padR}" y1="${padT+plotH}" y2="${padT+plotH}" stroke="#ccc"/>
${bars}${means}${labels}
</svg>`;
  return Bun.write(resolve(outDir,outFile),svg);
}

await chart({title:'Wall-clock time per asset',unit:'minutes per finished monster (lower is better) — one bar per agent run',get:r=>r.seconds/60,fmt:v=>v.toFixed(1),outFile:'time.svg'});
await chart({title:'Agent tokens per asset',unit:'thousands of tokens (lower is better) — one bar per agent run',get:r=>r.tokens/1000,fmt:v=>v.toFixed(0)+'k',outFile:'tokens.svg'});
await chart({title:'Visual quality vs reference',unit:'score out of 10 from uniform renders (higher is better) — one bar per agent run',get:r=>r.quality,fmt:v=>String(v),outFile:'quality.svg'});
console.log('charts written to',outDir);
