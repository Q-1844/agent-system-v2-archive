// 雨灯归航 — 资源候选生产 A 段：Look 生成+AI 审查、铜灯道具
const http=require('http');
const P='/api/project/'+encodeURIComponent('雨灯归航');
function req(method, path, body){return new Promise((res,rej)=>{
  const data=body?JSON.stringify(body):null;
  const r=http.request({host:'localhost',port:8000,path,method,headers:{'Content-Type':'application/json'},timeout:600000},x=>{let d='';x.on('data',c=>d+=c);x.on('end',()=>{try{res(JSON.parse(d))}catch(e){res(d)}})});
  r.on('error',rej); r.on('timeout',()=>{r.destroy(new Error('timeout'))}); if(data)r.write(data); r.end();});}
(async()=>{
 // 1. Look 创建
 let res=await req('GET',P+'/resources');
 const docRev=res.document_revision||res.revision||res.doc_revision;
 console.log('resources doc rev:',docRev);
 const look=await req('POST',P+'/looks',{character_name:'阿獭',label:'default',
   appearance_description:'A small otter with rounded brown fur, wearing an orange-yellow raincoat with hood and a dark blue scarf; a small white triangular fur patch on its left cheek. Cute storybook proportions, 2D hand-drawn style, clean lines, soft watercolor-like shading.',
   expected_document_revision:docRev});
 console.log('look create:',JSON.stringify(look).slice(0,300));
 const lookId=look.look_id||look.id||look.asset_id||look.resource_id;
 const lookRev=look.revision||look.resource_revision||look.expected_revision;
 // 2. Look 候选生成（3 候选，正面身份参考）
 const gen=await req('POST',P+'/looks/'+lookId+'/generate',{expected_revision:lookRev,candidate_count:3,view_purpose:'identity front reference'});
 console.log('look generate:',JSON.stringify(gen).slice(0,400));
 // 3. AI 审查
 const rv=await req('POST',P+'/looks/'+lookId+'/review',{});
 console.log('look review:',JSON.stringify(rv).slice(0,700));
 // 4. 铜灯道具
 const res2=await req('GET',P+'/resources');
 const docRev2=res2.document_revision||res2.revision||res2.doc_revision;
 const prop=await req('POST',P+'/props',{name:'旧铜灯',
   description:'An old brass lantern with a red-painted handle (paint chipped), a brass body, and a glass chimney. In act one the glass is cracked and the lamp is muddy; after repair the glass is new and the lamp glows warm yellow when lit. 2D hand-drawn storybook style.',
   tags:['core-prop'],expected_document_revision:docRev2});
 console.log('prop create:',JSON.stringify(prop).slice(0,250));
 console.log('SUMMARY lookId='+lookId+' propId='+(prop.prop_id||prop.id));
})().catch(e=>{console.error('FAIL',e.message||e);process.exit(1)});