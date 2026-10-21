# COLLAB_CODE 交接包：源码收集（只读复制→独立暂存目录，不改工程）
import json, os, shutil, subprocess, sys, time
from pathlib import Path

TS = time.strftime('%Y%m%d_%H%M')
BASE = Path(r'C:/Users/曹文淇/Desktop/ai工作流')
CHILD = BASE / 'animation-storyboard'
STAGE = BASE / '.claude' / '压缩包' / f'COLLAB_CODE_HANDOFF_{TS}'
WS = STAGE / 'workspace'
GIT_STATE = STAGE / 'GIT_STATE'
EVID = STAGE / 'evidence'
TEXT_EXT = {'.py', '.md', '.json', '.txt', '.yaml', '.yml', '.ts', '.vue', '.js', '.mjs', '.cjs',
            '.html', '.css', '.scss', '.sh', '.bat', '.cmd', '.cfg', '.ini', '.toml', '.csv',
            '.svg', '.gitignore', '.editorconfig', '.pen', '.d.ts'}
BIN_FIXTURE = {'.mp4'}   # 测试 fixture 白名单（tests/ 下）

def git(cwd, *a):
    return subprocess.run(['git', *a], cwd=cwd, capture_output=True, text=True,
                          encoding='utf-8', errors='replace').stdout

def is_text(p: Path):
    return p.suffix.lower() in TEXT_EXT or p.name in ('.gitignore', '.editorconfig', 'Dockerfile')

copied, skipped_bin, missing = [], [], []

def copy_file(src: Path, rel: str):
    if not src.is_file():
        missing.append(('工作区不存在', rel))
        return
    dst = WS / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    copied.append(rel)

# ============ 子仓：tracked 文本 + 测试fixture + 未跟踪源码/文档 ============
os.chdir(CHILD)
tracked = [f.strip('"') for f in git('.', 'ls-files').splitlines() if f.strip('"')]
for rel in tracked:
    p = Path(rel)
    if not p.is_file():
        missing.append(('tracked缺失', rel)); continue
    if is_text(p):
        copy_file(p, f'animation-storyboard/{rel}')
    elif p.suffix.lower() in BIN_FIXTURE and rel.startswith('tests/'):
        copy_file(p, f'animation-storyboard/{rel}')   # 测试 fixture 保留
    else:
        skipped_bin.append(rel)

un = [l[3:].strip('"') for l in git('.', 'status', '--short').splitlines() if l.startswith('??')]
n_un = 0
for rel in un:
    p = Path(rel)
    if p.is_dir():
        continue
    # 未跟踪：全部文本类（root 文档/_tmp 脚本/详细流程文件/docs 新文档等）；排除输出/媒体/日志
    if is_text(p) and not any(x in rel for x in ('projects/', 'generated-images/', 'logs/', '/output/', 'backend_p5')):
        copy_file(p, f'animation-storyboard/{rel}'); n_un += 1
    elif p.suffix.lower() in BIN_FIXTURE and rel.startswith('tests/'):
        copy_file(p, f'animation-storyboard/{rel}'); n_un += 1

# 详细流程文件（真相源，含子目录；未跟踪目录整体收文本）
for p in Path('详细流程文件').rglob('*'):
    if p.is_file() and is_text(p):
        copy_file(p, f'animation-storyboard/详细流程文件/{p.relative_to("详细流程文件")}'.replace('\\', '/')); n_un += 1

# ============ 父仓：tracked 文本（排除 reference gitlink/子仓指针/二进制） ============
os.chdir(BASE)
ptracked = [f.strip('"') for f in git('.', 'ls-files').splitlines() if f.strip('"')]
for rel in ptracked:
    p = BASE / rel
    if not p.is_file() or rel.startswith('reference/') or rel == 'animation-storyboard':
        continue
    if is_text(p):
        copy_file(p, f'_parent/{rel}')

# ============ GIT_STATE ============
GIT_STATE.mkdir(parents=True, exist_ok=True)
snap = {'collected_at': time.strftime('%Y-%m-%d %H:%M:%S %z'), 'tz': 'UTC+8', 'repos': {}}
for name, cwd in (('animation-storyboard', CHILD), ('_parent', BASE)):
    os.chdir(cwd)
    d = {'branch': git('.', 'branch', '--show-current').strip(),
         'HEAD': git('.', 'log', '-1', '--format=%H %ci %s').strip(),
         'status': git('.', 'status', '--short')}
    diff = git('.', 'diff')
    if diff.strip():
        (GIT_STATE / f'{name}_unstaged.diff').write_text(diff, encoding='utf-8')
        d['unstaged_diff_file'] = f'{name}_unstaged.diff'
    d['运行实例版本'] = ('后端(端口8000)载入=HEAD+shots.py未提交补丁（2026-10-18多次重启）'
                        if name == 'animation-storyboard' else '无运行服务')
    snap['repos'][name] = d
os.chdir(CHILD)
(GIT_STATE / 'SNAPSHOT_git.json').write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding='utf-8')

# ============ evidence（复用研究包） ============
RESEARCH = BASE / '测试5' / '测试7' / 'COLLAB_RESEARCH_EVIDENCE_20261018_1300'
for sub, files in [('reports', ['PHASE56_COLLAB_FRAMEWORK_PROPOSAL.md', 'PHASE56_A_MECHANISM_REPORT.md',
                                'PHASE56_B_CONCURRENCY_REPORT.md', 'PHASE56_C_PROJECT_COLLAB_REPORT.md',
                                'PHASE55_A_IMPLEMENTATION_REPORT.md', 'HISTORY_PHASE54_REPORT.md']),
                   ('runtime', ['RUN_INDEX.json']),
                   ('research_pack_index', ['SOURCE_MAP.md', 'CLAIM_EVIDENCE_MATRIX.md', 'MISSING.md',
                                            'README.md'])]:
    for f in files:
        p = RESEARCH / ('01_reports' if sub == 'reports' else
                        '04_runtime_evidence' if sub == 'runtime' else '') / f
        if p.exists():
            (EVID / sub).mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, EVID / sub / f)
for sub in ('04_runtime_evidence', '05_tests_existing', '06_analysis'):
    src = RESEARCH / sub
    if src.exists():
        (EVID / sub).mkdir(parents=True, exist_ok=True)
        for p in src.rglob('*'):
            if p.is_file():
                rel = p.relative_to(src)
                dst = EVID / sub / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, dst)

n_staged = len(copied)
size = sum((WS / rel).stat().st_size for rel in copied if (WS / rel).exists())
json.dump({'ts': TS, 'staged': n_staged, 'raw_mb': round(size / 1024 / 1024, 1),
           'skipped_tracked_binary': len(skipped_bin), 'untracked_added': n_un,
           'missing': missing},
          open(STAGE / '_collect_stats.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'staged {n_staged} 文件, {size/1024/1024:.1f} MB raw | 跳过tracked二进制 {len(skipped_bin)} | 未跟踪补收 {n_un} | missing {missing}')
