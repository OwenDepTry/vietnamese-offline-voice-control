"""Summarise live trials (results/measurements.csv) and latency from the event log.

  python -m ml.trial_report
  python -m ml.trial_report --trials results/measurements.csv --events results/events.jsonl

Latency = end of the 2 s recording -> recognition (+ ACK in serial mode), as
docs/TEST_PLAN.md defines it. Reports median and p95 per condition.
"""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
import numpy as np
from app.common import COMMANDS


def _pct(values, q):
    return float(np.percentile(values, q)) if values else None


def summarize_trials(path):
    with Path(path).open(encoding='utf-8', newline='') as f:
        rows = [r for r in csv.DictReader(f) if r.get('intended_command')]
    groups = defaultdict(list)
    for r in rows:
        groups['ALL'].append(r); groups[r.get('condition') or '-'].append(r)
    out = {}
    for name, part in groups.items():
        cmd = [r for r in part if r['intended_command'] in COMMANDS]
        non = [r for r in part if r['intended_command'] not in COMMANDS]
        lat = [float(r['latency_ms']) for r in part if r.get('latency_ms')]
        phys = [r for r in cmd if r.get('physical_success') in ('yes', 'no')]
        out[name] = {
            'trials': len(part),
            'correct_action': sum((r['predicted_label'] == r['intended_command']) if r['intended_command'] in COMMANDS
                                  else (r['predicted_label'] not in COMMANDS) for r in part) / len(part),
            'command_missed': (sum(r['predicted_label'] not in COMMANDS for r in cmd) / len(cmd)) if cmd else None,
            'wrong_command': (sum(r['predicted_label'] in COMMANDS and r['predicted_label'] != r['intended_command']
                                  for r in cmd) / len(cmd)) if cmd else None,
            'false_activation': (sum(r['predicted_label'] in COMMANDS for r in non) / len(non)) if non else None,
            'physical_success': (sum(r['physical_success'] == 'yes' for r in phys) / len(phys)) if phys else None,
            'latency_median_ms': _pct(lat, 50), 'latency_p95_ms': _pct(lat, 95)}
    return out


def summarize_events(path):
    voice, manual, errors = [], [], 0
    with Path(path).open(encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            e = json.loads(line)
            errors += 'error' in e
            if e.get('source') == 'voice' and 'post_record_ms' in e: voice.append(e['post_record_ms'])
            if e.get('source') == 'manual' and 'transport_ms' in e: manual.append(e['transport_ms'])
    return {'voice_events': len(voice), 'voice_latency_median_ms': _pct(voice, 50), 'voice_latency_p95_ms': _pct(voice, 95),
            'manual_events': len(manual), 'manual_transport_median_ms': _pct(manual, 50),
            'manual_transport_p95_ms': _pct(manual, 95), 'errors': errors}


def _fmt(v, pct=False):
    if v is None: return '-'
    return f'{v*100:.1f}%' if pct else f'{v:.1f}'


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--trials', default='results/measurements.csv')
    p.add_argument('--events', default='results/events.jsonl')
    a = p.parse_args()
    if Path(a.trials).exists():
        s = summarize_trials(a.trials)
        if s:
            print('Lượt thử trực tiếp (measurements.csv):')
            print(f"{'điều kiện':14}{'lượt':>6}{'đúng':>9}{'bỏ sót':>9}{'sai lệnh':>10}{'kích nhầm':>11}{'vật lý OK':>11}{'trễ median':>12}{'p95':>9}")
            for name, v in sorted(s.items(), key=lambda kv: kv[0] != 'ALL'):
                print(f"{name:14}{v['trials']:>6}{_fmt(v['correct_action'],1):>9}{_fmt(v['command_missed'],1):>9}"
                      f"{_fmt(v['wrong_command'],1):>10}{_fmt(v['false_activation'],1):>11}{_fmt(v['physical_success'],1):>11}"
                      f"{_fmt(v['latency_median_ms']):>12}{_fmt(v['latency_p95_ms']):>9}")
        else:
            print('measurements.csv chưa có lượt thử nào.')
    if Path(a.events).exists():
        e = summarize_events(a.events)
        print(f"\nEvent log: {e['voice_events']} lượt giọng nói, trễ median {_fmt(e['voice_latency_median_ms'])} ms, "
              f"p95 {_fmt(e['voice_latency_p95_ms'])} ms; {e['manual_events']} lệnh tay, truyền median "
              f"{_fmt(e['manual_transport_median_ms'])} ms; {e['errors']} lỗi.")


if __name__ == '__main__':
    main()
