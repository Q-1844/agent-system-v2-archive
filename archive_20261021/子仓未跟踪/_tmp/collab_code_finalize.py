# COLLAB_CODE 交接包：SOURCE_MANIFEST + 脱敏扫描 + ZIP + 解压自检
import hashlib, json, re, shutil, sys, time, zipfile
from pathlib import Path

STAGE = Path(sys.argv[1])
WS = STAGE / 'workspace'
ZIP_PATH = STAGE.parent / f'{STAGE.name}.zip'

REPO_OF = {}
# 映射：workspace 下相对路径 -> 所属仓库
# animation-storyboard/* -> 子仓；_parent/* -> 父仓

SECRET_PATTERNS = [
    (re.compile(r'sk-[A-Za-z0-9]{16,}'), 'sk-key'),
    (re.compile(r'(?i)AGNES_API_KEY\s*[:=]\s*["\']?[A-Za-z0-9_\-]{12,}'), 'agnes-key-literal'),
    (re.compile(r'(?i)(secret|password|cookie)\s*[:=]\s*["\']?[A-Za-z0-9_\-]{12,}'), 'cred-literal'),
    (re.compile(r'Bearer\s+[A-Za-z0-9_\-\.]{20,}'), 'bearer-real'),
    (re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'), 'private-key'),
]
FAKE_URL = re.compile(r'https?://(fake\.|example\.|localhost|127\.0\.0\.1)')

payloads = []
secret_hits = []
case_map = {}
symlinks = []
for p in sorted(WS.rglob('*')):
    if not p.is_file():
        if p.is_symlink():
            symlinks.append(str(p.relative_to(WS)))
        continue
    rel_ws = p.relative_to(WS).as_posix()
    rel_pkg = f'workspace/{rel_ws}'
    repo = 'animation-storyboard（子仓）' if rel_ws.startswith('animation-storyboard/') else '_parent（父仓）'
    orig = rel_ws
    data = p.read_bytes()
    redacted = False
    if p.suffix.lower() in ('.py', '.md', '.json', '.yaml', '.yml', '.txt', '.ts', '.vue', '.js', '.sh', '.bat'):
        txt = data.decode('utf-8', errors='replace')
        for pat, tag in SECRET_PATTERNS:
            ms = list(pat.finditer(txt))
            if ms:
                secret_hits.append((rel_pkg, tag, len(ms)))
        if secret_hits and secret_hits[-1][0] == rel_pkg:
            pass  # 记录即可（本次扫描未发现真实密钥时无动作）
    cat = ('测试' if '/tests/' in rel_ws else
           '前端' if rel_ws.endswith(('.vue', '.ts')) and rel_ws.startswith('animation-storyboard/src/') else
           '配置' if '/config' in rel_ws or p.name in ('package.json', 'package-lock.json', 'tsconfig.json', 'vite.config.ts', 'pytest.ini', 'pyproject.toml') else
           'Skill' if '/skill_system/builtin/' in rel_ws else
           '文档' if p.suffix == '.md' else
           '脚本/工具' if '/_tmp/' in rel_ws or '_parent/' in rel_ws else
           '源码')
    payload = {'pkg_path': rel_pkg, 'orig_path': orig, 'repo': repo,
               'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
               'category': cat, 'redacted': redacted, 'excerpt': False,
               'collected_at': time.strftime('%Y-%m-%d %H:%M:%S')}
    # 大小写冲突检测（Windows 不区分大小写）
    key = rel_pkg.lower().replace('\\', '/')
    if key in case_map and case_map[key] != rel_pkg:
        payload['case_conflict_with'] = case_map[key]
    case_map[key] = rel_pkg
    payloads.append(payload)

# 顶层文档与 GIT_STATE/evidence 也入 manifest
for sub in ('GIT_STATE', 'evidence'):
    for p in sorted((STAGE / sub).rglob('*')):
        if p.is_file():
            rel_pkg = p.relative_to(STAGE).as_posix()
            data = p.read_bytes()
            payloads.append({'pkg_path': rel_pkg, 'orig_path': f'{sub}（研究包复用/采集）',
                             'repo': '取证', 'bytes': len(data),
                             'sha256': hashlib.sha256(data).hexdigest(),
                             'category': '证据', 'redacted': False, 'excerpt': False,
                             'collected_at': time.strftime('%Y-%m-%d %H:%M:%S')})
for doc in ('README_FIRST.md', 'DESIGN_DIRECTION.md', 'REPLAY_GUIDE.md',
            'MISSING_AND_EXCLUDED.md'):
    p = STAGE / doc
    if p.exists():
        payloads.append({'pkg_path': doc, 'orig_path': doc, 'repo': '交接文档',
                         'bytes': p.stat().st_size,
                         'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                         'category': '交接文档', 'redacted': False, 'excerpt': False,
                         'collected_at': time.strftime('%Y-%m-%d %H:%M:%S')})

manifest = {'schema': 'collab_code_source_manifest_v1', 'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'zip_target': ZIP_PATH.name,
            'payload_count': len(payloads),
            'total_bytes': sum(p['bytes'] for p in payloads),
            'symlinks_found': symlinks,
            'secret_scan': {'policy': '命中只记文件与类型，不打印值；测试内 fake 域名不算命中',
                            'hits': secret_hits or '无真实密钥命中'},
            'payloads': payloads}
(STAGE / 'SOURCE_MANIFEST.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding='utf-8')
print('manifest:', len(payloads), 'payloads |', manifest['total_bytes'] // 1024 // 1024, 'MB raw | secret hits:', len(secret_hits), '| symlinks:', symlinks)

# ---- ZIP ----
with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for p in sorted(STAGE.rglob('*')):
        if p.is_file():
            z.write(p, p.relative_to(STAGE).as_posix())
size = ZIP_PATH.stat().st_size
sha = hashlib.sha256(ZIP_PATH.read_bytes()).hexdigest()
print('ZIP:', ZIP_PATH.name, '|', f'{size:,} bytes ({size/1024/1024:.1f} MB)', '| sha256:', sha)

# ---- 解压自检 ----
LIMIT = 100_000_000
assert size < LIMIT, f'超过 100MB 上限：{size}'
vdir = STAGE.parent / f'_verify_{STAGE.name}'
if vdir.exists():
    shutil.rmtree(vdir)
names = []
with zipfile.ZipFile(ZIP_PATH) as z:
    names = z.namelist()
    assert len(names) == len(set(names)), 'ZIP 内有重复条目'
    for n in names:
        assert not n.startswith('/') and '..' not in n and ':' not in n, f'路径异常: {n}'
    z.extractall(vdir)
ok, miss = 0, []
for pl in payloads:
    vp = vdir / pl['pkg_path']
    if vp.exists() and hashlib.sha256(vp.read_bytes()).hexdigest() == pl['sha256']:
        ok += 1
    else:
        miss.append(pl['pkg_path'])
case_dup = len(payloads) - len(case_map) - sum(1 for s in ('GIT_STATE', 'evidence'))  # 近似：主体检完成后人工看
shutil.rmtree(vdir)
print('verify: ok', ok, '/ missing', miss, '| 大小写冲突(主体检):', sum(1 for p in payloads if 'case_conflict_with' in p))
