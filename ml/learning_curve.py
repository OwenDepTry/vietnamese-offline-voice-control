"""Validation macro-F1 vs. amount of training data: does recording more help?

  python -m ml.learning_curve --manifest data/manifest_split.csv --output results/learning_curve_01

For each fraction, a random label-balanced subset of TRAIN clips is used (repeated
--repeats times); scoring is on VALIDATION. The test split is never loaded.
Writes learning_curve.csv and learning_curve.png (png needs matplotlib).
"""
import argparse
import csv
from pathlib import Path
import numpy as np
from app.common import LABELS
from ml.dataset import read_manifest
from ml.features import FeatureConfig
from ml.train_baseline import CLASSIFIERS, AudioCache, fit_select


def subset(train_rows, fraction, rng):
    picked = []
    for label in LABELS:
        part = [r for r in train_rows if r['label'] == label]
        k = max(1, int(round(len(part) * fraction)))
        picked += [part[i] for i in rng.choice(len(part), k, replace=False)]
    return picked


def curve(manifest, fractions, repeats=3, classifier='logreg', align=False, augment=0, seed=42):
    rows = read_manifest(manifest)
    train_rows = [r for r in rows if r['split'] == 'train']
    val_rows = [r for r in rows if r['split'] == 'validation']
    cache = AudioCache(); rng = np.random.default_rng(seed); out = []
    for fraction in fractions:
        scores, sizes = [], []
        for rep in range(1 if fraction >= 1 else repeats):
            part = subset(train_rows, fraction, rng)
            _, best, *_ = fit_select(part + val_rows, FeatureConfig(align=align), classifier, augment, seed + rep, cache)
            scores.append(best['macro_f1']); sizes.append(len(part))
        out.append({'fraction': fraction, 'train_clips': int(np.mean(sizes)),
                    'val_macro_f1_mean': round(float(np.mean(scores)), 4),
                    'val_macro_f1_std': round(float(np.std(scores)), 4), 'runs': len(scores)})
    return out


def plot(results, path, title):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    x = [r['train_clips'] for r in results]
    y = np.array([r['val_macro_f1_mean'] for r in results]); e = np.array([r['val_macro_f1_std'] for r in results])
    fig, ax = plt.subplots(figsize=(6.5, 4))
    ax.plot(x, y, marker='o', color='#4C78A8'); ax.fill_between(x, y - e, y + e, alpha=0.2, color='#4C78A8')
    ax.set_xlabel('Số bản thu train (gốc, chưa tăng cường)'); ax.set_ylabel('Macro-F1 trên validation')
    ax.set_ylim(0, 1.05); ax.set_title(title); ax.grid(alpha=0.3)
    ax.spines[['top', 'right']].set_visible(False)
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--manifest', default='data/manifest_split.csv')
    p.add_argument('--output', default='results/learning_curve_01', help='New folder')
    p.add_argument('--fractions', nargs='+', type=float, default=[0.2, 0.4, 0.6, 0.8, 1.0])
    p.add_argument('--repeats', type=int, default=3)
    p.add_argument('--classifier', choices=CLASSIFIERS, default='logreg')
    p.add_argument('--align', action='store_true'); p.add_argument('--augment', type=int, default=0)
    a = p.parse_args()
    out = Path(a.output)
    if out.exists(): raise ValueError('Output folder exists; choose a new one')
    results = curve(a.manifest, sorted(a.fractions), a.repeats, a.classifier, a.align, a.augment)
    out.mkdir(parents=True)
    with (out / 'learning_curve.csv').open('x', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(results[0])); w.writeheader(); w.writerows(results)
    for r in results:
        print(f"{r['train_clips']:5d} clips  val macro-F1 {r['val_macro_f1_mean']:.3f} ± {r['val_macro_f1_std']:.3f}")
    try:
        plot(results, out / 'learning_curve.png', f'Learning curve ({a.classifier})')
        print('Wrote', out / 'learning_curve.png')
    except ImportError:
        print('matplotlib not installed; CSV only')


if __name__ == '__main__':
    main()
