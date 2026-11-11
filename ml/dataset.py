import csv
import hashlib
from pathlib import Path
import numpy as np
from app.common import LABELS
from ml.features import load_wav, extract

FIELDS = ['path','speaker_id','session_id','label','split','noise_condition','distance_m']

def read_manifest(path, require_splits=True):
    path = Path(path).resolve()
    with path.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        if not set(FIELDS).issubset(reader.fieldnames or []):
            raise ValueError('Manifest missing required columns: ' + ','.join(FIELDS))
        rows = list(reader)
    if not rows:
        raise ValueError('Manifest has no recordings')
    speakers, paths, hashes = {}, set(), {}
    for row in rows:
        if row['label'] not in LABELS or not row['speaker_id'].strip() or not row['session_id'].strip():
            raise ValueError('Invalid label/speaker/session in manifest')
        if row['split'] not in (['train','validation','test'] if require_splits else ['', 'train','validation','test']):
            raise ValueError('Run split first; invalid split column')
        p = (path.parent / row['path']).resolve()
        if p in paths:
            raise ValueError('Duplicate recording path: ' + str(p))
        paths.add(p)
        if not p.is_file():
            raise ValueError('Missing recording: ' + str(p))
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        if digest in hashes and hashes[digest] != row['split']:
            raise ValueError('Identical WAV bytes occur across splits')
        hashes[digest] = row['split']
        if require_splits:
            old = speakers.setdefault(row['speaker_id'], row['split'])
            if old != row['split']:
                raise ValueError('Speaker leakage: ' + row['speaker_id'])
        row['_file'] = str(p)
    return rows

def matrix(rows, split, config):
    selected = [r for r in rows if r['split']==split]
    if not selected:
        raise ValueError('No samples for split ' + split)
    return (np.stack([extract(load_wav(r['_file'], config.sample_rate), config) for r in selected]),
            np.array([r['label'] for r in selected]), selected)
