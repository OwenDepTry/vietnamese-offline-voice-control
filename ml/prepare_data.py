"""Assign whole speakers to splits; never overwrite original manifest."""
import argparse
import csv
from pathlib import Path
import numpy as np
from ml.dataset import read_manifest, FIELDS
from app.common import LABELS

def split_manifest(source, output, seed=42):
    if Path(output).exists():
        raise ValueError('Output already exists; choose a new manifest path')
    rows = read_manifest(source, require_splits=False)
    people = sorted({r['speaker_id'] for r in rows})
    if len(people) < 3:
        raise ValueError('Need at least 3 speakers; prefer 10+ for a pilot')
    np.random.default_rng(seed).shuffle(people)
    n = max(1, round(len(people)*0.2))
    mapping = {p: ('test' if i<n else 'validation' if i<2*n else 'train') for i,p in enumerate(people)}
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    import os
    for row in rows:
        row['split'] = mapping[row['speaker_id']]
        row['path'] = os.path.relpath(row['_file'], output.parent)
    # Fail explicitly instead of silently evaluating missing labels.
    for split in ['train','validation','test']:
        missing = set(LABELS)-{r['label'] for r in rows if r['split']==split}
        if missing:
            raise ValueError(f'{split} missing {sorted(missing)}. Collect all labels for every speaker.')
    with output.open('x', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader(); writer.writerows({k:r[k] for k in FIELDS} for r in rows)
    read_manifest(output)
    return mapping

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', default='data/manifest.csv')
    p.add_argument('--output', default='data/manifest_split.csv')
    p.add_argument('--seed',type=int,default=42)
    a=p.parse_args(); print(split_manifest(a.manifest,a.output,a.seed))
if __name__=='__main__': main()
