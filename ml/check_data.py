"""Check recordings before training: counts per session and per-file quality flags.

Examples:
  python -m ml.check_data
  python -m ml.check_data --report results/data_check.csv
  python -m ml.check_data --drop-flagged data/manifest_clean.csv

Flags are heuristics: listen to each flagged file before removing it.
--drop-flagged writes a NEW manifest without flagged rows; WAV files are kept.
"""
import argparse
import csv
import os
import sys
from collections import Counter
from pathlib import Path
from app.common import LABELS
from ml.dataset import read_manifest, FIELDS
from ml.features import load_wav
from ml.quality import analyze, issues, describe


def check(manifest):
    rows = read_manifest(manifest, require_splits=False)
    results = []
    for row in rows:
        stats = analyze(load_wav(row['_file']))
        results.append({'row': row, 'stats': stats, 'issues': issues(stats, row['label'])})
    counts = Counter((r['speaker_id'], r['session_id'], r['label']) for r in rows)
    sessions = sorted({(r['speaker_id'], r['session_id']) for r in rows})
    missing = {s: [l for l in LABELS if counts[(s[0], s[1], l)] == 0] for s in sessions}
    return results, counts, sessions, {k: v for k, v in missing.items() if v}


def write_report(results, path):
    path = Path(path)
    if path.exists():
        raise ValueError('Report exists; choose a new path')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['path', 'speaker_id', 'session_id', 'label', 'peak', 'speech_start_s',
                    'speech_end_s', 'active_s', 'issues'])
        for r in results:
            s, row = r['stats'], r['row']
            w.writerow([row['path'], row['speaker_id'], row['session_id'], row['label'],
                        round(s['peak'], 3), s['speech_start'], s['speech_end'],
                        round(s['active_s'], 2), ' '.join(r['issues'])])


def drop_flagged(results, output):
    output = Path(output).resolve()
    if output.exists():
        raise ValueError('Output exists; choose a new manifest path')
    output.parent.mkdir(parents=True, exist_ok=True)
    kept = [r['row'] for r in results if not r['issues']]
    with output.open('x', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for row in kept:
            out = {k: row[k] for k in FIELDS}
            out['path'] = Path(os.path.relpath(row['_file'], output.parent)).as_posix()
            w.writerow(out)
    return len(kept)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--manifest', default='data/manifest.csv')
    p.add_argument('--report', help='Write per-file CSV report to this new path')
    p.add_argument('--drop-flagged', metavar='NEW_MANIFEST', help='Write a manifest without flagged files')
    a = p.parse_args()
    results, counts, sessions, missing = check(a.manifest)
    print('Số mẫu theo phiên (speaker/session):')
    header = 'phiên'.ljust(14) + ''.join(l[:9].rjust(10) for l in LABELS)
    print(header)
    for s in sessions:
        print(f'{s[0]}/{s[1]}'.ljust(14) + ''.join(str(counts[(s[0], s[1], l)]).rjust(10) for l in LABELS))
    for s, labels in missing.items():
        print(f'THIẾU NHÃN: {s[0]}/{s[1]} chưa có {", ".join(labels)}')
    flagged = [r for r in results if r['issues']]
    print(f'\n{len(results)} file, {len(flagged)} file nên nghe lại:')
    for r in flagged:
        print(f"  {r['row']['path']}  [{r['row']['label']}]  {describe(r['issues'])}")
    if a.report:
        write_report(results, a.report); print('Report:', a.report)
    if a.drop_flagged:
        n = drop_flagged(results, a.drop_flagged)
        print(f'Manifest mới ({n} file, bỏ {len(flagged)}): {a.drop_flagged}')
    return 1 if missing else 0


if __name__ == '__main__':
    sys.exit(main())
