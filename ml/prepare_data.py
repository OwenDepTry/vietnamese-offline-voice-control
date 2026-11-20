"""Assign recordings to train/validation/test; never overwrite the original manifest.

Two modes:
- Automatic (default): whole speakers are shuffled into splits. Needs >= 3 speakers.
- Manual (--validation and --test): list speakers ("p02") or single sessions
  ("p01/s02"). Everything not listed goes to train. Useful for small teams, e.g.
  one speaker:  --validation p01/s02 --test p01/s03
  two speakers: --validation p01/s02 --test p02
A session (speaker + session_id) is never split across sets.
"""
import argparse
import csv
import os
from pathlib import Path
import numpy as np
from ml.dataset import read_manifest, FIELDS
from app.common import LABELS


def _parse_units(values, option):
    units = []
    for raw in values or []:
        for token in raw.split(','):
            token = token.strip()
            if not token:
                continue
            parts = token.split('/')
            if len(parts) > 2 or not all(parts):
                raise ValueError(f'{option}: use "speaker" or "speaker/session", got {token!r}')
            units.append(tuple(parts))
    return units


def _matches(unit, row):
    if len(unit) == 1:
        return row['speaker_id'] == unit[0]
    return row['speaker_id'] == unit[0] and row['session_id'] == unit[1]


def _manual_mapping(rows, validation, test):
    val_units = _parse_units(validation, '--validation')
    test_units = _parse_units(test, '--test')
    if not val_units or not test_units:
        raise ValueError('Manual split needs both --validation and --test')
    for unit in val_units + test_units:
        if not any(_matches(unit, r) for r in rows):
            raise ValueError('No recordings match ' + '/'.join(unit))
    assignment = {}
    for row in rows:
        in_val = any(_matches(u, row) for u in val_units)
        in_test = any(_matches(u, row) for u in test_units)
        if in_val and in_test:
            raise ValueError(f"{row['speaker_id']}/{row['session_id']} is listed in both validation and test")
        assignment[id(row)] = 'test' if in_test else 'validation' if in_val else 'train'
    return assignment


def _speaker_mapping(rows, seed):
    people = sorted({r['speaker_id'] for r in rows})
    if len(people) < 3:
        raise ValueError(
            'Automatic split needs at least 3 speakers (prefer 10+). With fewer, pass '
            '--validation and --test, e.g. --validation p01/s02 --test p01/s03')
    np.random.default_rng(seed).shuffle(people)
    n = max(1, round(len(people) * 0.2))
    by_person = {p: ('test' if i < n else 'validation' if i < 2 * n else 'train') for i, p in enumerate(people)}
    return {id(r): by_person[r['speaker_id']] for r in rows}


def split_manifest(source, output, seed=42, validation=None, test=None):
    if Path(output).exists():
        raise ValueError('Output already exists; choose a new manifest path')
    rows = read_manifest(source, require_splits=False)
    if validation or test:
        assignment = _manual_mapping(rows, validation, test)
    else:
        assignment = _speaker_mapping(rows, seed)
    output = Path(output).resolve()
    for row in rows:
        row['split'] = assignment[id(row)]
        row['path'] = os.path.relpath(row['_file'], output.parent)
    # Fail explicitly instead of silently evaluating missing labels.
    for split in ['train', 'validation', 'test']:
        missing = set(LABELS) - {r['label'] for r in rows if r['split'] == split}
        if missing:
            raise ValueError(f'{split} missing {sorted(missing)}. Record every label in every session.')
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader(); writer.writerows({k: r[k] for k in FIELDS} for r in rows)
    read_manifest(output)
    summary = {}
    for r in rows:
        summary.setdefault(r['split'], set()).add(f"{r['speaker_id']}/{r['session_id']}")
    return {k: sorted(v) for k, v in sorted(summary.items())}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--manifest', default='data/manifest.csv')
    p.add_argument('--output', default='data/manifest_split.csv')
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--validation', nargs='+', help='Speakers or speaker/session for validation')
    p.add_argument('--test', nargs='+', help='Speakers or speaker/session for test')
    a = p.parse_args()
    print(split_manifest(a.manifest, a.output, a.seed, a.validation, a.test))


if __name__ == '__main__': main()
