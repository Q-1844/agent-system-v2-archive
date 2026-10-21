// 雨灯归航 — 13 镜 production binding（REST shot-bindings）
const http=require('http');
const P='/api/project/'+encodeURIComponent('雨灯归航');
function req(method, path, body){return new Promise((res,rej)=>{
  const data=body?JSON.stringify(body):null;
  const r=http.request({host:'localhost',port:8000,path,method,headers:{'Content-Type':'application/json'},timeout:120000},x=>{let d='';x.on('data',c=>d+=c);x.on('end',()=>{try{res(JSON.parse(d))}catch(e){res(d)}})});
  r.on('error',rej); if(data)r.write(data); r.end();});}

const LOOK='look_295fc0cd2345', COMP='comp_1894770b967f', PROP='prop_fb1bd0b18fb1';
const SIV={s01:'sciv_a0d0b69a2761',s02:'sciv_8c9742b8016b',s03:'sciv_2a95c7419f28'};
// location_view_id = base view（系统据 instance+view 解析 SIV）
const VIEW={s01:'view_cd8f12307b70',s02:'view_12503eb06cff',s03:'view_24c55d041058'};
const INST={s01:'scin_e2bdadb3beca',s02:'scin_6f1e453d5a32',s03:'scin_f3effc02c359'};

const SHOTS=['s01_c01','s01_c02','s01_c03','s01_c04','s01_c05','s01_c06','s02_c01','s02_c02','s02_c03','s03_c01','s03_c02','s03_c03','s03_c04'];
(async()=>{
 for (const sid of SHOTS) {
   const sc=sid.slice(0,3);
   const body={shot_id:sid, scene_id:sc,
     scene_binding:{scene_instance_id:INST[sc], location_view_id:VIEW[sc]},
     character_bindings:[{character_name:'阿獭', look_id:LOOK}],
     prop_bindings:[], production_notes:''};
   if (sid!=='s03_c04') {
     body.character_bindings[0].composition_id=COMP;   // 道具关系由 composition 内声明承载
     body.prop_bindings=[];
   }
   const r=await req('POST',P+'/shot-bindings',body);
   console.log(sid, r.ok===true?'BOUND':JSON.stringify(r).slice(0,180));
 }
 // validity 抽查
 for (const sid of ['s01_c01','s01_c04','s02_c02','s03_c01','s03_c04']) {
   const v=await req('GET',P+'/shot-bindings/'+sid+'/validity');
   console.log('validity',sid,v.readiness, JSON.stringify((v.issues||[]).map(i=>i.reason).slice(0,3)));
 }
})().catch(e=>{console.error('FAIL',e.message);process.exit(1)});