// Uniform post-hoc evaluation: for each GLB, emit Khronos/inventory JSON, a 6-view
// contact sheet, and a 1024px portrait, all rendered with the same skill renderer.
//   GLB_CREATOR_CLEANUP=off bun tools/eval.ts runs/baseline-1/monster.glb ...
import { Preview } from '../skills/glb-creator/scripts/preview';
import { validate } from '../skills/glb-creator/scripts/validate';
import { resolve,sep } from 'node:path';

const outDir=resolve(import.meta.dir,'../results/eval');
for(const arg of process.argv.slice(2)){
  const path=resolve(arg),run=path.split(sep).slice(-2)[0];
  try{
    const bytes=new Uint8Array(await Bun.file(path).arrayBuffer());
    const v=await validate(bytes);
    const base={sourceBytes:v.bytes,triangles:v.report.info?.totalTriangleCount??null,errors:v.errors,warnings:v.warnings,
      textures:v.textures.length,joints:v.skins[0]?.joints?.length??0,
      clips:v.clips.map(c=>({name:c.name,duration:Math.round(c.duration*1000)/1000})),
      materials:v.materials.map((m:any)=>({name:m.name,baseColor:m.baseColor,normal:m.normal,roughness:m.roughness}))};
    const p=await Preview.create();
    try{
      await p.load(bytes);
      const sheet=await p.sheet({tile:416});
      await Bun.write(resolve(outDir,`${run}-sheet.webp`),sheet.bytes);
      const portrait=await p.frame({size:1024,time:0,yaw:-.35,format:'png'});
      await Bun.write(resolve(outDir,`${run}.png`),portrait.bytes);
      await Bun.write(resolve(outDir,`${run}.json`),JSON.stringify({...base,tiles:sheet.tiles},null,1));
    }catch(e){
      await Bun.write(resolve(outDir,`${run}.json`),JSON.stringify({...base,renderError:String(e)},null,1));
    }finally{await p.dispose();}
    console.log(`${run}: ok`);
  }catch(e){
    await Bun.write(resolve(outDir,`${run}.json`),JSON.stringify({fileError:String(e)},null,1));
    console.log(`${run}: FAILED ${e}`);
  }
}
