"""Compare classifier / alignment / augmentation settings on VALIDATION only.

  python -m ml.compare --manifest data/manifest_split.csv --output results/compare_01.csv

The test split is never loaded here. Pick the best row, then train it with
ml.train_baseline using the same options, and only then run ml.evaluate once.
With few validation clips, differences of a few points are within noise.
"""
import argparse
import csv
import itertools
from pathlib import Path
from ml.dataset import read_manifest
from ml.features import FeatureConfig
from ml.train_baseline import CLASSIFIERS, AudioCache, fit_select


def compare(manifest, classifiers=CLASSIFIERS, aligns=(False, True), augments=(0, 3), seed=42):
    rows = read_manifest(manifest)
    rows = [r for r in rows if r['split'] in ('train', 'validation')]   # test stays untouched
    cache = AudioCache(); results = []
    for clf, align, aug in itertools.product(classifiers, aligns, augments):
        _, best, _, _, val_rows, _ = fit_select(rows, FeatureConfig(align=align), clf, aug, seed, cache)
        results.append({'classifier': clf, 'align': align, 'augment': aug,
                        'validation_macro_f1': round(best['macro_f1'], 4), 'threshold': best['threshold'],
                        'validation_samples': len(val_rows)})
    return sorted(results, key=lambda r: -r['validation_macro_f1'])


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--manifest', default='data/manifest_split.csv')
    p.add_argument('--output', help='Optional new CSV path for the table')
    p.add_argument('--classifiers', nargs='+', choices=CLASSIFIERS, default=CLASSIFIERS)
    p.add_argument('--augments', nargs='+', type=int, default=[0, 3])
    p.add_argument('--seed', type=int, default=42)
    a = p.parse_args()
    results = compare(a.manifest, a.classifiers, (False, True), a.augments, a.seed)
    print(f"{'classifier':10} {'align':6} {'augment':7} {'val macro-F1':>12} {'threshold':>9}")
    for r in results:
        print(f"{r['classifier']:10} {str(r['align']):6} {r['augment']:7} {r['validation_macro_f1']:12.3f} {r['threshold']:9.3f}")
    best = results[0]
    cmd = f"python -m ml.train_baseline --classifier {best['classifier']}"
    cmd += ' --align' if best['align'] else ''
    cmd += f" --augment {best['augment']}" if best['augment'] else ''
    print('\nTốt nhất trên validation:', cmd, '--manifest', a.manifest, '--output models/<tên mới>.joblib')
    if a.output:
        out = Path(a.output)
        if out.exists(): raise ValueError('Output exists; choose a new path')
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open('x', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=list(results[0])); w.writeheader(); w.writerows(results)


if __name__ == '__main__':
    main()
