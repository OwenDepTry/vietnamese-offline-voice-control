"""Train an MFCC classifier; tune the rejection threshold on validation only.

Options (all chosen on validation, never on test):
  --classifier logreg|svm|mlp   logistic regression (default), RBF SVM, small neural net
  --align                       centre the detected speech before MFCC
  --augment N                   add N randomly shifted/gain/noise copies per TRAIN clip
Compare settings first with: python -m ml.compare
"""
import argparse
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
import importlib.metadata
import joblib
import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import f1_score
from app.common import LABELS
from ml.dataset import read_manifest
from ml.features import FeatureConfig, extract, load_wav
from ml.predict import decide

CLASSIFIERS = ['logreg', 'svm', 'mlp']


def build_classifier(name, seed=42):
    if name == 'logreg':
        clf = LogisticRegression(max_iter=2000, class_weight='balanced', random_state=seed)
    elif name == 'svm':
        # Platt-scaled probabilities via cross-validation (SVC(probability=True) is deprecated).
        clf = CalibratedClassifierCV(SVC(C=10, gamma='scale', class_weight='balanced', random_state=seed),
                                     method='sigmoid', cv=3, ensemble=False)
    elif name == 'mlp':
        clf = MLPClassifier(hidden_layer_sizes=(64,), alpha=1e-2, max_iter=3000, random_state=seed)
    else:
        raise ValueError('Unknown classifier ' + name)
    return make_pipeline(StandardScaler(), clf)


def augment_audio(audio, rng, noises, rate=16000):
    """One random variant: time shift, gain change, background noise at 10-30 dB SNR."""
    x = np.roll(audio, int(rng.uniform(-0.25, 0.25) * rate)).astype(np.float64)
    x *= 10 ** (rng.uniform(-6, 6) / 20)
    if noises:
        noise = noises[rng.integers(len(noises))].astype(np.float64)
        noise = np.resize(noise, len(x))
    else:
        noise = rng.normal(0, 1, len(x))
    signal_rms = np.sqrt(np.mean(x ** 2)) + 1e-9
    noise_rms = np.sqrt(np.mean(noise ** 2)) + 1e-9
    x += noise * (signal_rms / noise_rms) / 10 ** (rng.uniform(10, 30) / 20)
    return np.clip(x, -1, 1).astype(np.float32)


class AudioCache:
    """Load each WAV once (comparisons reuse the same clips many times)."""
    def __init__(self, rate=16000):
        self.rate = rate; self.data = {}
    def get(self, row):
        if row['_file'] not in self.data:
            self.data[row['_file']] = load_wav(row['_file'], self.rate)
        return self.data[row['_file']]


def features(rows, config, cache, augment=0, seed=42):
    rng = np.random.default_rng(seed)
    noises = [cache.get(r) for r in rows if r['label'] == 'silence'] if augment else []
    x, y = [], []
    for r in rows:
        audio = cache.get(r)
        x.append(extract(audio, config)); y.append(r['label'])
        for _ in range(augment):
            x.append(extract(augment_audio(audio, rng, noises, config.sample_rate), config)); y.append(r['label'])
    return np.stack(x), np.array(y)


def fit_select(rows, config, classifier='logreg', augment=0, seed=42, cache=None):
    """Fit on train, pick the rejection threshold by validation macro-F1."""
    cache = cache or AudioCache(config.sample_rate)
    train_rows = [r for r in rows if r['split'] == 'train']
    val_rows = [r for r in rows if r['split'] == 'validation']
    for name, part in [('train', train_rows), ('validation', val_rows)]:
        if {r['label'] for r in part} != set(LABELS):
            raise ValueError(name + ' must contain every command, unknown and silence')
    x, y = features(train_rows, config, cache, augment, seed)
    vx, vy = features(val_rows, config, cache)
    pipeline = build_classifier(classifier, seed).fit(x, y)
    probs = pipeline.predict_proba(vx)
    records = []
    for threshold in np.linspace(0, 1, 41):
        pred = [decide(p, pipeline.classes_, float(threshold)).label for p in probs]
        records.append({'threshold': float(threshold),
                        'macro_f1': float(f1_score(vy, pred, labels=LABELS, average='macro', zero_division=0))})
    # Conservative threshold on ties. Scores are not calibrated confidence guarantees.
    best = max(records, key=lambda r: (r['macro_f1'], r['threshold']))
    return pipeline, best, records, train_rows, val_rows, len(y)


def train(manifest, output, seed=42, classifier='logreg', align=False, augment=0):
    output = Path(output)
    if output.exists(): raise ValueError('Model exists; use another output path to preserve experiments')
    if augment < 0: raise ValueError('augment must be >= 0')
    rows = read_manifest(manifest); config = FeatureConfig(align=align)
    pipeline, best, records, train_rows, val_rows, n_train = fit_select(rows, config, classifier, augment, seed)
    settings = {'classifier': classifier, 'align': align, 'augment': augment}
    bundle = {'schema_version': 1, 'pipeline': pipeline, 'features': config.to_dict(), 'threshold': best['threshold'],
              'seed': seed, 'created_utc': datetime.now(timezone.utc).isoformat(), 'training': settings,
              'manifest_sha256': hashlib.sha256(Path(manifest).read_bytes()).hexdigest(),
              'versions': {p: importlib.metadata.version(p) for p in ['numpy', 'scipy', 'scikit-learn', 'joblib']},
              'train_speakers': sorted({r['speaker_id'] for r in train_rows}),
              'validation_speakers': sorted({r['speaker_id'] for r in val_rows}),
              'train_sessions': sorted({r['speaker_id'] + '/' + r['session_id'] for r in train_rows}),
              'validation_sessions': sorted({r['speaker_id'] + '/' + r['session_id'] for r in val_rows}),
              'seen_audio_sha256': [hashlib.sha256(Path(r['_file']).read_bytes()).hexdigest() for r in train_rows + val_rows]}
    output.parent.mkdir(parents=True, exist_ok=True); joblib.dump(bundle, output)
    report = {'validation_only': True, 'selection_metric': 'macro_f1', 'selected': best, 'settings': settings,
              'threshold_search': records, 'train_samples': len(train_rows), 'train_samples_with_augmentation': n_train,
              'validation_samples': len(val_rows),
              'train_sessions': bundle['train_sessions'], 'validation_sessions': bundle['validation_sessions'],
              'validation_new_speaker': not set(bundle['train_speakers']) & set(bundle['validation_speakers']),
              'versions': bundle['versions']}
    output.with_suffix('.training.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--manifest', default='data/manifest_split.csv'); p.add_argument('--output', default='models/baseline.joblib')
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--classifier', choices=CLASSIFIERS, default='logreg')
    p.add_argument('--align', action='store_true')
    p.add_argument('--augment', type=int, default=0)
    a = p.parse_args()
    report = train(a.manifest, a.output, a.seed, a.classifier, a.align, a.augment)
    print(json.dumps({k: report[k] for k in ['selected', 'settings', 'train_samples', 'train_samples_with_augmentation',
                                             'validation_samples', 'validation_new_speaker']}, indent=2))


if __name__ == '__main__': main()
