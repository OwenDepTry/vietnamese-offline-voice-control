"""Merge recordings collected on another computer into this project's dataset.

The other person records with app.recorder on their machine, then sends their
data/manifest.csv together with the data/raw/<speaker>/ folder (e.g. as a zip).
Extract it anywhere, then:

  python -m ml.merge_manifest --incoming D:/from_p02/data/manifest.csv
  python -m ml.merge_manifest --incoming D:/from_p02/data/manifest.csv --rename-speaker p01=p02

WAV files are copied into data/raw/<speaker>/<session>/ and rows are appended to
data/manifest.csv. A backup of the old manifest is written first. Nothing is
changed if any check fails. Use --dry-run to only check.
"""
import argparse
import csv
import hashlib
import re
import shutil
from datetime import datetime
from pathlib import Path
from ml.dataset import read_manifest, FIELDS

ID = re.compile(r'[A-Za-z0-9_-]+')


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _renames(values):
    out = {}
    for v in values or []:
        old, sep, new = v.partition('=')
        if not sep or not ID.fullmatch(old) or not ID.fullmatch(new):
            raise ValueError(f'--rename-speaker expects old=new, got {v!r}')
        out[old] = new
    return out


def merge(base, incoming, rename=None, dry_run=False):
    base = Path(base).resolve()
    rename = _renames(rename)
    new_rows = read_manifest(incoming, require_splits=False)
    old_rows = read_manifest(base, require_splits=False) if base.exists() else []
    old_sessions = {(r['speaker_id'], r['session_id']) for r in old_rows}
    old_hashes = {_sha(r['_file']) for r in old_rows}
    plan, seen = [], set()
    for r in new_rows:
        speaker = rename.get(r['speaker_id'], r['speaker_id'])
        session = r['session_id']
        if not ID.fullmatch(speaker) or not ID.fullmatch(session):
            raise ValueError(f'Invalid speaker/session id: {speaker}/{session}')
        if (speaker, session) in old_sessions:
            raise ValueError(
                f'{speaker}/{session} already exists in {base.name}. If this is a different person, '
                f'use --rename-speaker {r["speaker_id"]}=<new id>; if it is the same person, give the '
                f'new recordings a new session id.')
        digest = _sha(r['_file'])
        if digest in old_hashes or digest in seen:
            raise ValueError('Identical recording already present: ' + r['path'])
        seen.add(digest)
        target = base.parent / 'raw' / speaker / session / Path(r['_file']).name
        if target.exists():
            raise ValueError(f'Target file exists: {target}')
        row = {k: r[k] for k in FIELDS}
        row.update(path=target.relative_to(base.parent).as_posix(), speaker_id=speaker, split='')
        plan.append((Path(r['_file']), target, row))
    summary = {}
    for _, _, row in plan:
        key = f"{row['speaker_id']}/{row['session_id']}"
        summary[key] = summary.get(key, 0) + 1
    if dry_run or not plan:
        return summary
    backup = None
    if base.exists():
        backup = base.with_name(base.name + '.bak-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
        shutil.copy2(base, backup)
    copied = []
    try:
        for src, dst, _ in plan:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst); copied.append(dst)
        new_file = not base.exists()
        with base.open('a', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            if new_file:
                w.writeheader()
            w.writerows(row for _, _, row in plan)
        read_manifest(base, require_splits=False)
    except Exception:
        # Roll back so a failed merge never leaves a half-written dataset.
        for path in copied:
            path.unlink(missing_ok=True)
        if backup:
            shutil.copy2(backup, base)
        elif base.exists():
            base.unlink()
        raise
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--base', default='data/manifest.csv')
    p.add_argument('--incoming', required=True, help="The other computer's manifest.csv")
    p.add_argument('--rename-speaker', nargs='+', metavar='OLD=NEW')
    p.add_argument('--dry-run', action='store_true')
    a = p.parse_args()
    summary = merge(a.base, a.incoming, a.rename_speaker, a.dry_run)
    verb = 'Sẽ thêm' if a.dry_run else 'Đã thêm'
    for key, n in summary.items():
        print(f'{verb} {n} bản thu của {key}')
    if not summary:
        print('Không có bản thu nào để thêm.')


if __name__ == '__main__':
    main()
