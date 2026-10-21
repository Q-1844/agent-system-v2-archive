// 粗剪 v2：绝对路径 concat
const fs=require('fs');
const {execSync}=require('child_process');
const map=JSON.parse(fs.readFileSync('_tmp/yudeng/video_map.json','utf8'));
const order=['s01_c01','s01_c02','s01_c03','s01_c04','s01_c05','s01_c06','s02_c01','s02_c02','s02_c03','s03_c01','s03_c02','s03_c03','s03_c04'];
const base=fs.realpathSync('.');
const list=order.map(s=>{
  const p=map[s].split('\\').join('/');
  return "file '"+base+"/"+p+"'";
}).join('\n');
fs.writeFileSync('_tmp/yudeng/concat.txt',list);
execSync('ffmpeg -y -v error -f concat -safe 0 -i _tmp/yudeng/concat.txt -c copy "projects/雨灯归航/output/videos/preview/雨灯归航_roughcut_v1.mp4"');
console.log('roughcut done');