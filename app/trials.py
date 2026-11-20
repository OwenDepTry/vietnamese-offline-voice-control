"""Append one live trial to results/measurements.csv (schema from the repo)."""
import csv
import subprocess
from pathlib import Path
from app.common import ROOT, COMMANDS

FIELDS = ['trial_id', 'commit', 'speaker_id', 'condition', 'intended_command', 'predicted_label',
          'ack_received', 'physical_success', 'latency_ms', 'notes']


def current_commit():
    try:
        return subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT, capture_output=True,
                              text=True, timeout=3).stdout.strip()
    except Exception:
        return ''


def next_trial_id(path):
    path = Path(path)
    if not path.exists():
        return 1
    with path.open(encoding='utf-8', newline='') as f:
        ids = [int(r['trial_id']) for r in csv.DictReader(f) if (r.get('trial_id') or '').isdigit()]
    return max(ids, default=0) + 1


def append_trial(path, event, intended, speaker='', condition='', physical_success='', notes='', commit=None):
    """event is a Controller.voice() result (or {'error': ...} on failure)."""
    path = Path(path)
    if intended not in list(COMMANDS) + ['unknown', 'silence']:
        raise ValueError('intended must be a command, unknown or silence')
    if path.exists():
        with path.open(encoding='utf-8', newline='') as f:
            if next(csv.reader(f), []) != FIELDS:
                raise ValueError(f'{path} header differs from expected schema')
    prediction = event.get('prediction') or {}
    result = event.get('result') or {}
    if 'error' in event:
        ack = 'error'
    elif result.get('ack') is True:
        ack = 'yes'
    elif prediction.get('accepted'):
        ack = 'n/a' if result.get('mode') == 'simulation' else 'no'
    else:
        ack = 'not_sent'
    latency = event.get('post_record_ms')
    row = {'trial_id': next_trial_id(path), 'commit': current_commit() if commit is None else commit,
           'speaker_id': speaker, 'condition': condition, 'intended_command': intended,
           'predicted_label': prediction.get('label', ''), 'ack_received': ack,
           'physical_success': physical_success,
           'latency_ms': f'{latency:.1f}' if isinstance(latency, (int, float)) else '',
           'notes': (notes + ' ' + event.get('error', '')).strip()}
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists() or path.stat().st_size == 0
    with path.open('a', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new: w.writeheader()
        w.writerow(row)
    return row


def set_last_physical(path, value, trial_id=None):
    """Fill physical_success ('yes'/'no') for the given (default: last) trial."""
    if value not in ('yes', 'no', ''):
        raise ValueError('value must be yes, no or empty')
    path = Path(path)
    with path.open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError('No trials recorded yet')
    target = rows[-1] if trial_id is None else next((r for r in rows if r['trial_id'] == str(trial_id)), None)
    if target is None:
        raise ValueError(f'Trial {trial_id} not found')
    target['physical_success'] = value
    tmp = path.with_suffix(path.suffix + '.tmp')
    with tmp.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
    tmp.replace(path)
    return target
