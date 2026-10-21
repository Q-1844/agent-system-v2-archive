# Phase56 取证包：脱敏扫描/JSON校验/MANIFEST/ZIP/解压自检
import gzip, hashlib, json, re, shutil, sys, time, zipfile
from pathlib import Path

out = Path(sys.argv[1])
TS = '20261018_1300'
ZIP_PATH = out.parent / f'COLLAB_RESEARCH_EVIDENCE_CORE_{TS}.zip'
SECRET_PATTERNS = [
    (re.compile(r'sk-[A-Za-z0-9]{16,}'), 'sk-key'),
    (re.compile(r'(?i)(api[_-]?key|secret|password|token|cookie)\s*[:=]\s*["\']?[A-Za-z0-9_\-]{12,}'), 'key-value'),
    (re.compile(r'(?i)bearer\s+[A-Za-z0-9_\-\.]{16,}'), 'bearer'),
    (re.compile(r'AWS[A-Za-z0-9]{16,}'), 'aws'),
    (re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'), 'private-key'),
]
URL_PAT = re.compile(r'https?://[^\s"\'<>]+\.(?:png|jpg|mp4|zip|wav)[^\s"\'<>]*')

hits = []
json_bad = []
payloads = []
for p in sorted(out.rglob('*')):
    if not p.is_file() or p.name == 'MANIFEST.json':
        continue
    rel = p.relative_to(out).as_posix()
    data = p.read_bytes()
    # JSON/JSONL 可解析校验
    if p.suffix in ('.json',):
        try:
            json.loads(data.decode('utf-8'))
        except Exception as e:
            json_bad.append((rel, str(e)[:80]))
    elif p.suffix == '.jsonl':
        for i, line in enumerate(data.decode('utf-8').splitlines()):
            try:
                json.loads(line)
            except Exception as e:
                json_bad.append((f'{rel}#L{i+1}', str(e)[:80]))
    # 密钥/签名URL扫描（文本类）
    if p.suffix in ('.py', '.md', '.json', '.jsonl', '.yaml', '.txt', '.vue', '.ts', '.diff') or p.name.endswith('.diff'):
        txt = data.decode('utf-8', errors='replace')
        for pat, tag in SECRET_PATTERNS:
            for m in pat.finditer(txt):
                hits.append((rel, tag, txt[max(0, m.start()-20):m.start()].replace('\n', ' ')))
        for m in URL_PAT.finditer(txt):
            hits.append((rel, 'media-url', m.group(0)[:80]))
    payloads.append({'path': rel, 'bytes': len(data),
                     'sha256': hashlib.sha256(data).hexdigest(),
                     'category': rel.split('/')[0],
                     'collected_at': TS,
                     'source': ('子仓 animation-storyboard@82e3050(+未提交补丁见00_snapshot)' if
                                (rel.startswith(('02_source', '05_tests')) or 'freeze_manifest' in rel or 'reference_policy' in rel)
                                else '父仓 报告/任务书' if rel.startswith('01_reports')
                                else '运行持久记录(cache/projects只读导出)' if rel.startswith('04_runtime')
                                else '取证派生' if rel.startswith(('06_analysis', '00_snapshot'))
                                else '脱敏副本' if rel.startswith('03_config')
                                else '取证文档'),
                     'redaction': ('密钥/环境脱敏' if rel.startswith('03_config') else
                                   '无（源码原样）' if rel.startswith('02_source') else
                                   'URL剥离/名称如实' if rel.startswith('04_runtime') else '无')})

# URL 命中处理：报告但不阻断——检查是否为可公开文档地址
real_media = [h for h in hits if h[1] == 'media-url' and not h[2].startswith(('https://docs.', 'https://www.'))]

manifest = {'schema': 'evidence_manifest_v1', 'created_at': TS,
            'zip_target': ZIP_PATH.name, 'payload_count': len(payloads),
            'total_bytes': sum(p['bytes'] for p in payloads),
            'json_parse_failures': json_bad,
            'secret_scan_hits_summary': {'count': len(hits), 'media_url_count': len(real_media),
                                          'note': '命中明细未打印真实值；media-url 命中需人工核对是否私有资产URL',
                                          'media_url_files': sorted({h[0] for h in real_media})},
            'payloads': payloads}
(out / 'MANIFEST.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding='utf-8')
print('payloads:', len(payloads), '| total KB:', manifest['total_bytes'] // 1024,
      '| json_bad:', json_bad, '| scan hits:', len(hits), 'media-url files:', sorted({h[0] for h in real_media}))

# ---- ZIP（包内相对路径）----
with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for p in sorted(out.rglob('*')):
        if p.is_file():
            z.write(p, p.relative_to(out).as_posix())
sha = hashlib.sha256(ZIP_PATH.read_bytes()).hexdigest()

# ---- 解压自检 ----
verify_dir = out.parent / f'_verify_{TS}'
if verify_dir.exists():
    shutil.rmtree(verify_dir)
with zipfile.ZipFile(ZIP_PATH) as z:
    bad = [n for n in z.namelist() if n.startswith('/') or '..' in n]
    assert not bad, f'zip 路径异常: {bad}'
    z.extractall(verify_dir)
v_ok, v_missing = 0, []
for p in payloads:
    vp = verify_dir / p['path']
    if vp.exists() and hashlib.sha256(vp.read_bytes()).hexdigest() == p['sha256']:
        v_ok += 1
    else:
        v_missing.append(p['path'])
shutil.rmtree(verify_dir)
print('ZIP:', ZIP_PATH.name, '| size:', ZIP_PATH.stat().st_size // 1024, 'KB | sha256:', sha[:32] + '...')
print('verify: ok', v_ok, '/ missing', v_missing)
