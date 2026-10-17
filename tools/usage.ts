// Aggregate token usage, duration, and tool-call counts from subagent JSONL transcripts.
// Prints ONLY numeric aggregates — never transcript content.
//   bun tools/usage.ts <label=path.output> ...
for(const arg of process.argv.slice(2)){
  const [label,...rest]=arg.split('=');const path=rest.join('=');
  const text=await Bun.file(path).text();
  let input=0,output=0,cacheRead=0,cacheWrite=0,turns=0,toolCalls=0;
  const toolNames:Record<string,number>={};
  let first:number|undefined,last:number|undefined;
  for(const line of text.split('\n')){
    if(!line.trim())continue;
    let j:any;try{j=JSON.parse(line);}catch{continue;}
    const ts=Date.parse(j.timestamp??'');if(Number.isFinite(ts)){first??=ts;last=ts;}
    const u=j.message?.usage;
    if(u){turns++;input+=u.input_tokens??0;output+=u.output_tokens??0;cacheRead+=u.cache_read_input_tokens??0;cacheWrite+=u.cache_creation_input_tokens??0;}
    for(const c of j.message?.content??[])if(c?.type==='tool_use'){toolCalls++;toolNames[c.name]=(toolNames[c.name]??0)+1;}
  }
  console.log(JSON.stringify({label,turns,toolCalls,toolNames,
    tokens:{input,output,cacheRead,cacheWrite,total:input+output+cacheRead+cacheWrite,billedEquivalent:input+cacheWrite+output},
    minutes:first!==undefined&&last!==undefined?Math.round((last-first)/600)/100:null}));
}
