// 雨灯归航 — 场景系统：3 location → view → generate → review；instance → SIV → generate → review
const http=require('http');
const P='/api/project/'+encodeURIComponent('雨灯归航');
function req(method, path, body){return new Promise((res,rej)=>{
  const data=body?JSON.stringify(body):null;
  const r=http.request({host:'localhost',port:8000,path,method,headers:{'Content-Type':'application/json'},timeout:600000},x=>{let d='';x.on('data',c=>d+=c);x.on('end',()=>{try{res(JSON.parse(d))}catch(e){res(d)}})});
  r.on('error',rej); r.on('timeout',()=>{r.destroy(new Error('timeout'))}); if(data)r.write(data); r.end();});}
function pick(r,...keys){for(const k of keys){if(r&&r[k]!==undefined&&r[k]!==null)return r[k]}if(r&&r.after&&r.after.id)return r.after.id;if(r&&r.target)return r.target;return undefined}
async function docRev(){const o=await req('GET',P+'/scene-system/overview');return o.document_revision||o.revision}
const LOC=[
 {name:'雨后河岸与栈桥',description:'A riverbank after heavy rain: silvery overcast sky with clouds parting, a wide river with gentle ripples reflecting light, an old wooden pier/boardwalk extending from the bank into the river, wet wooden planks glistening, grassy bank with reeds. Distant low hills. 2D hand-drawn storybook style, soft watercolor textures, muted silver-blue palette.',
  identity_description:'Old weathered wooden pier with wooden posts and simple railings extending into a wide river; grassy riverbank with reeds; low hills across the water; silver-grey after-rain sky.'},
 {name:'夜间修理间',description:'A cozy repair workshop at night: warm yellow desk lamp glow, sturdy wooden workbench with tools, small drawers and shelves on the stone wall, a heavy wooden door leading outside; rain streaks on a small window. 2D hand-drawn storybook style, warm amber light against deep blue night shadows.',
  identity_description:'Small stone-and-timber workshop interior; central wooden workbench; warm hanging desk lamp; heavy wooden door; small window with rain streaks; tools and jars on shelves.'},
 {name:'灯塔门厅与灯室',description:'Interior of an old lighthouse at night: ground-floor hall with a spiral stone staircase winding upward, rough stone walls; at the top a lamp room with a large empty lamp seat and window openings facing the river. 2D hand-drawn storybook style, cool blue night tones with warm lantern glow.',
  identity_description:'Round stone lighthouse interior; spiral stone staircase with wooden handrail winding counterclockwise upward; top lamp room with glazing panels, a large brass lamp seat, and window openings overlooking the river.'},
];
(async()=>{
 const created={};
 for (const L of LOC) {
  const rev=await docRev();
  const loc=await req('POST',P+'/scene-system/locations',{name:L.name,description:L.description,identity_description:L.identity_description,style_notes:'2D hand-drawn storybook, soft watercolor',expected_document_revision:rev});
  const lid=pick(loc); console.log('location:',L.name,'->',lid, loc.ok===false?('ERR '+JSON.stringify(loc).slice(0,200)):'');
  if(!lid) throw new Error('location create failed');
  const rev2=await docRev();
  const view=await req('POST',P+'/scene-system/views',{location_id:lid,label:'main establishing view',camera_zone:'general',look_direction:'toward the river/pier or interior focus',expected_document_revision:rev2});
  const vid=pick(view); console.log('  view ->',vid);
  const vread=await req('GET',P+'/scene-system/views/'+vid);
  const vrev=vread.revision;
  const gen=await req('POST',P+'/scene-system/views/'+vid+'/generate',{expected_revision:vrev,candidate_count:2,size_tier:'1K',ratio:'16:9'});
  const g=gen.detail||gen; console.log('  view gen:',g.status,JSON.stringify(g.candidate_urls||[]).slice(0,200));
  if(g.status!=='completed') console.log('  view gen detail:',JSON.stringify(g).slice(0,300));
  const rv=await req('POST',P+'/scene-system/views/'+vid+'/review',{});
  console.log('  view review:',JSON.stringify(rv).slice(0,350));
  created[L.name]={lid,vid};
 }
 // scene instances + SIVs
 for (let i=0;i<3;i++) {
  const L=LOC[i]; const sid='s0'+(i+1);
  const rev=await docRev();
  const inst=await req('POST',P+'/scene-system/scene-instances',{story_scene_id:sid,location_id:created[L.name].lid,expected_document_revision:rev});
  const iid=pick(inst); console.log('instance',sid,'->',iid);
  const rev2=await docRev();
  const sciv=await req('POST',P+'/scene-system/scene-instance-views',{scene_instance_id:iid,location_view_id:created[L.name].vid,label:sid+' main',expected_document_revision:rev2});
  const scid=pick(sciv); console.log('  sciv ->',scid);
  const sread=await req('GET',P+'/scene-system/scene-instance-views/'+scid);
  const srev=sread.revision;
  const sgen=await req('POST',P+'/scene-system/scene-instance-views/'+scid+'/generate',{expected_revision:srev,candidate_count:2,size_tier:'1K',ratio:'16:9'});
  const sg=sgen.detail||sgen; console.log('  sciv gen:',sg.status,JSON.stringify(sg.candidate_urls||[]).slice(0,200));
  if(sg.status!=='completed') console.log('  sciv gen detail:',JSON.stringify(sg).slice(0,300));
  const srv=await req('POST',P+'/scene-system/scene-instance-views/'+scid+'/review',{});
  console.log('  sciv review:',JSON.stringify(srv).slice(0,350));
  created[L.name].iid=iid; created[L.name].scid=scid;
 }
 console.log('CREATED='+JSON.stringify(created));
})().catch(e=>{console.error('FAIL',e.message||e);process.exit(1)});