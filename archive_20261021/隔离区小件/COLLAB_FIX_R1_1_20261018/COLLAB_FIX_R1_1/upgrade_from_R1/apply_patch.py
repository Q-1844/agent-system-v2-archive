"""Apply/restore only the shipped source files, with hash checks and backups.

Python 3.11+. Default is a dry run. Stop the backend before --apply/--rollback.
Does not touch projects, media, job state, credentials or installed dependencies.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sys
import tempfile
import uuid


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def safe_path(root, name):
    rel = PurePosixPath(name)
    if not name or rel.is_absolute() or ".." in rel.parts or "\\" in name or ":" in name:
        raise ValueError(f"unsafe relative path: {name}")
    target = root.joinpath(*rel.parts)
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"path escapes project: {name}")
    current = root
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"symlink in target path: {name}")
    return target


def atomic_bytes(target, data, mode=None):
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".collab-patch-", dir=target.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if mode is not None:
            os.chmod(temporary, mode)
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()


def read_manifest(package):
    manifest = json.loads((package / "PATCH_MANIFEST.json").read_text(encoding="utf-8"))
    if manifest.get("format_version") != 1 or not manifest.get("files"):
        raise ValueError("unsupported or empty manifest")
    seen = set()
    for entry in manifest["files"]:
        name = entry["path"]
        folded = name.casefold()
        if folded in seen:
            raise ValueError(f"duplicate target: {name}")
        seen.add(folded)
        payload = safe_path(package / "changed_files", name)
        if digest(payload) != entry["after_sha256"]:
            raise ValueError(f"payload checksum mismatch: {name}")
    return manifest


def restore(root, backup):
    state = json.loads((backup / "BACKUP.json").read_text(encoding="utf-8"))
    if Path(state["project_root"]).resolve() != root:
        raise ValueError("backup belongs to another project root")
    changes = []
    for entry in state["files"]:
        target = safe_path(root, entry["path"])
        current = digest(target)
        if current == entry["before_sha256"]:
            continue
        if current != entry["after_sha256"]:
            raise ValueError(f"rollback conflict; local file changed: {entry['path']}")
        old = safe_path(backup / "before", entry["path"])
        if entry["before_sha256"] is not None and digest(old) != entry["before_sha256"]:
            raise ValueError(f"backup checksum mismatch: {entry['path']}")
        changes.append((entry, target, old))
    for entry, target, old in changes:
        if entry["before_sha256"] is None:
            target.unlink()
        else:
            atomic_bytes(target, old.read_bytes(), entry.get("mode"))
    state["status"] = "rolled_back"
    atomic_bytes(backup / "BACKUP.json", json.dumps(state, ensure_ascii=False, indent=2).encode())
    return {"status": "rolled_back", "restored_files": len(changes), "backup": str(backup)}


def execute(args):
    root = Path(args.project_root).resolve()
    package = Path(__file__).resolve().parent
    if not (root / "api_server.py").is_file() or not (root / "src").is_dir():
        raise ValueError("--project-root must be the animation-storyboard source directory")
    if args.rollback:
        backup = Path(args.rollback).resolve()
        if not backup.is_relative_to(root / ".collab_patch_backups"):
            raise ValueError("rollback directory must be under this project's .collab_patch_backups")
        return restore(root, backup)
    manifest = read_manifest(package)
    pending = []
    already = []
    conflicts = []
    for entry in manifest["files"]:
        target = safe_path(root, entry["path"])
        if target.exists() and not target.is_file():
            conflicts.append(entry["path"])
            continue
        current = digest(target)
        if current == entry["after_sha256"]:
            already.append(entry["path"])
        elif current == entry["before_sha256"]:
            pending.append(entry)
        else:
            conflicts.append(entry["path"])
    if conflicts:
        raise ValueError("base mismatch; no files written: " + ", ".join(conflicts))
    if not args.apply:
        return {"status": "dry_run_ok", "pending": [e["path"] for e in pending],
                "already_applied": already}
    if not pending:
        return {"status": "already_applied", "files": len(already)}
    token = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8]
    backup = root / ".collab_patch_backups" / token
    backup.mkdir(parents=True)
    entries = []
    for entry in pending:
        target = safe_path(root, entry["path"])
        item = dict(entry)
        item["mode"] = (target.stat().st_mode & 0o777) if target.exists() else 0o644
        if entry["before_sha256"] is not None:
            old = safe_path(backup / "before", entry["path"])
            old.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, old)
            if digest(old) != entry["before_sha256"]:
                raise ValueError(f"file changed during backup: {entry['path']}")
        entries.append(item)
    state = {"project_root": str(root), "patch_id": manifest["patch_id"],
             "status": "prepared", "files": entries}
    atomic_bytes(backup / "BACKUP.json", json.dumps(state, ensure_ascii=False, indent=2).encode())
    try:
        for entry in entries:
            target = safe_path(root, entry["path"])
            if digest(target) != entry["before_sha256"]:
                raise ValueError(f"file changed before replacement: {entry['path']}")
            payload = safe_path(package / "changed_files", entry["path"])
            atomic_bytes(target, payload.read_bytes(), entry["mode"])
            if digest(target) != entry["after_sha256"]:
                raise ValueError(f"replacement verification failed: {entry['path']}")
    except Exception as exc:
        try:
            restore(root, backup)
        except Exception as restore_error:
            raise RuntimeError(f"apply failed ({exc}); rollback needs attention ({restore_error}); backup={backup}") from exc
        raise RuntimeError(f"apply failed and source restored: {exc}; backup={backup}") from exc
    state["status"] = "applied"
    atomic_bytes(backup / "BACKUP.json", json.dumps(state, ensure_ascii=False, indent=2).encode())
    return {"status": "applied", "files": len(entries), "backup": str(backup),
            "next": "Run the offline checks in README before restarting the backend."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--apply", action="store_true")
    action.add_argument("--rollback")
    try:
        print(json.dumps(execute(parser.parse_args()), ensure_ascii=False, indent=2))
    except Exception as exc:
        print(json.dumps({"status": "refused", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
