// 雨灯归航 — 角色三视图（sheet）→ bind → Look 候选生成 → AI 审查
const http=require('http');
const P='/api/project/'+encodeURIComponent('雨灯归航');
function req(method, path, body){return new Promise((res,rej)=>{
  const data=body?JSON.stringify(body):null;
  const r=http.request({host:'localhost',port:8000,path,method,headers:{'Content-Type':'application/json'},timeout:600000},x=>{let d='';x.on('data',c=>d+=c);x.on('end',()=>{try{res(JSON.parse(d))}catch(e){res(d)}})});
  r.on('error',rej); r.on('timeout',()=>{r.destroy(new Error('timeout'))}); if(data)r.write(data); r.end();});}
(async()=>{
 // 1. 设定图三视图
 const desc="A small otter character with rounded brown fur, wearing an orange-yellow raincoat with hood and a dark blue scarf; a small white triangular fur patch on its left cheek; cute storybook proportions; full body standing, relaxed pose";
 const sheet=await req('POST','/api/character/generate-sheet',{description:desc,style:"2D hand-drawn storybook illustration, soft watercolor-like shading, clean lines",size_tier:"1K",ratio:"3:2",project:"雨灯归航"});
 if(!sheet.success) throw new Error('sheet failed: '+JSON.stringify(sheet).slice(0,200));
 console.log('sheet ok; has segs:', ['front','side','back'].map(v=>v+':'+Boolean(sheet[v+'_seg'])).join(' '));
 // 2. bind 到项目
 const bind=await req('POST',P+'/character/bind',{name:'阿獭',
   description:'A small otter with rounded brown fur, wearing an orange-yellow raincoat and a dark blue scarf; a small white triangular fur patch on its left cheek.',
   views:{front:{raw:sheet.crops_raw.front,seg:sheet.front_seg},
          side:{raw:sheet.crops_raw.side,seg:sheet.side_seg},
          back:{raw:sheet.crops_raw.back,seg:sheet.back_seg}}});
 console.log('bind:',JSON.stringify(bind).slice(0,200));
 // 3. Look 候选生成
 const lk=await req('GET',P+'/looks/look_295fc0cd2345');
 const gen=await req('POST',P+'/looks/look_295fc0cd2345/generate',{expected_revision:lk.revision,candidate_count:3,view_purpose:'identity front reference'});
 const g=gen.detail||gen;
 console.log('look gen status:',g.status,'candidates:',JSON.stringify(g.candidate_urls||[]).slice(0,400));
 if(g.status!=='completed') { console.log('gen detail:',JSON.stringify(g).slice(0,400)); }
 // 4. AI 审查
 const rv=await req('POST',P+'/looks/look_295fc0cd2345/review',{});
 console.log('review:',JSON.stringify(rv).slice(0,900));
})().catch(e=>{console.error('FAIL',e.message||e);process.exit(1)});