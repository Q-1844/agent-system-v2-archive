// 雨灯归航 — 视频链：12 镜顺序提交+轮询（接力依赖上一镜尾帧就绪）
const http=require('http');
const fs=require('fs');
const P='/api/project/'+encodeURIComponent('雨灯归航');
function req(method, path, body){return new Promise((res,rej)=>{
  const data=body?JSON.stringify(body):null;
  const r=http.request({host:'localhost',port:8000,path,method,headers:{'Content-Type':'application/json'},timeout:120000},x=>{let d='';x.on('data',c=>d+=c);x.on('end',()=>{try{res(JSON.parse(d))}catch(e){res(d)}})});
  r.on('error',rej); if(data)r.write(data); r.end();});}
function log(s){fs.appendFileSync('_tmp/yudeng/chain_log.txt', s+'\n'); console.log(s);}

async function submitVideo(sid){
  const j=await req('POST',P+'/shot/'+sid+'/video',{});
  if(!j.job_id) throw new Error(sid+' submit failed: '+JSON.stringify(j).slice(0,150));
  return j.job_id;
}
async function poll(jobId){
  for (let i=0;i<20;i++){
    await new Promise(r=>setTimeout(r,30000));
    const j=await req('GET',P+'/jobs');
    const k=j.jobs.find(x=>x.job_id===jobId);
    if(!k) continue;
    log(`  poll ${i+1}: ${k.state} ${k.progress}% ${(k.error||'').slice(0,90)}`);
    if(k.state==='done') return true;
    if(k.state==='failed') return false;
  }
  return false;
}
async function shotInfo(sid){
  const doc=JSON.parse(fs.readFileSync('projects/雨灯归航/output/project.json','utf8'));
  for (const sc of doc.scenes) for (const s of sc.shots) if (s.shot_id===sid) {
    const vv=(s.video_versions||[]).slice(-1)[0];
    return {final:s.final_video, vv, end:(s.video_end_frame||{}).url};
  }
}
(async()=>{
 const shots=['s01_c02','s01_c03','s01_c04','s01_c05','s01_c06','s02_c01','s02_c02','s02_c03','s03_c01','s03_c02','s03_c03','s03_c04'];
 for (const sid of shots){
   log(`==== ${sid} submit`);
   let jobId; try{ jobId=await submitVideo(sid);}catch(e){ log('SUBMIT FAIL: '+e.message); break; }
   const ok=await poll(jobId);
   const info=await shotInfo(sid);
   log(`==== ${sid} ${ok?'DONE':'FAILED'} final=${info.final} tail=${(info.end||'').slice(0,70)}`);
   if(info.vv&&info.vv.input_visuals) log(`    input_visuals: ${JSON.stringify(info.vv.input_visuals).slice(0,220)}`);
   if(!ok) break;
 }
 log('CHAIN COMPLETE');
})().catch(e=>{log('CHAIN ERROR '+e.message)});