"""Plot helpers used by the notebooks (and usable from scripts).

Every function returns a matplotlib Figure and never writes files, so notebooks
show it inline and scripts can call fig.savefig(...) themselves.
"""
import numpy as np
from app.common import COMMANDS, LABELS
from ml.features import FeatureConfig, extract, load_wav
from ml.quality import analyze

COLORS = dict(zip(LABELS, ['#4C78A8', '#72B7B2', '#F58518', '#E45756', '#54A24B', '#9D755D']))


def _plt():
    import matplotlib.pyplot as plt
    return plt


def name(label):
    return f'{label} ({COMMANDS[label]})' if label in COMMANDS else label


def examples(rows, path_key='_file', rate=16000):
    """One waveform + spectrogram per label (first clip of each label)."""
    plt = _plt()
    picked = [next((r for r in rows if r['label'] == l), None) for l in LABELS]
    picked = [r for r in picked if r is not None]
    fig, axes = plt.subplots(len(picked), 2, figsize=(11, 1.9 * len(picked)), squeeze=False)
    for (wave_ax, spec_ax), row in zip(axes, picked):
        x = load_wav(row[path_key], rate); t = np.arange(len(x)) / rate
        stats = analyze(x, rate)
        wave_ax.plot(t, x, lw=0.5, color=COLORS[row['label']])
        if stats['speech_start'] is not None and row['label'] != 'silence':
            wave_ax.axvspan(stats['speech_start'], stats['speech_end'], color='gold', alpha=0.25)
        wave_ax.set_ylim(-1, 1); wave_ax.set_ylabel(name(row['label']), fontsize=8)
        spec_ax.specgram(x, NFFT=512, Fs=rate, noverlap=352, cmap='magma', vmin=-120)
        spec_ax.set_ylim(0, 6000)
    axes[0, 0].set_title('Dạng sóng (vàng = đoạn phát hiện có tiếng nói)')
    axes[0, 1].set_title('Phổ tần (0–6 kHz)')
    axes[-1, 0].set_xlabel('giây'); axes[-1, 1].set_xlabel('giây')
    fig.tight_layout()
    return fig


def speech_timing(stats_rows):
    """When speech starts/ends in each clip, per label: shows why --align can help."""
    plt = _plt()
    labels = [l for l in LABELS if l != 'silence' and any(r['label'] == l for r in stats_rows)]
    fig, ax = plt.subplots(figsize=(9, 0.6 + 0.55 * len(labels)))
    for i, label in enumerate(labels):
        part = [r for r in stats_rows if r['label'] == label and r['speech_start'] is not None]
        jitter = np.random.default_rng(i).uniform(-0.18, 0.18, len(part))
        for j, r in zip(jitter, part):
            ax.plot([r['speech_start'], r['speech_end']], [i + j, i + j], color=COLORS[label], alpha=0.6, lw=1.5)
    ax.axvline(2.0, color='red', ls='--', lw=1, label='cuối clip 2 s')
    ax.set_yticks(range(len(labels)), [name(l) for l in labels], fontsize=8)
    ax.set_xlim(0, 2.05); ax.set_xlabel('giây'); ax.set_title('Đoạn có tiếng nói trong từng bản thu')
    ax.legend(loc='lower right', fontsize=8)
    fig.tight_layout()
    return fig


def feature_map(rows, config=None, path_key='_file'):
    """2-D PCA of the MFCC feature vectors; well separated clusters = easier task."""
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    plt = _plt()
    config = config or FeatureConfig()
    x = np.stack([extract(load_wav(r[path_key], config.sample_rate), config) for r in rows])
    y = np.array([r['label'] for r in rows])
    z = PCA(2, random_state=0).fit_transform(StandardScaler().fit_transform(x))
    fig, ax = plt.subplots(figsize=(6.5, 5))
    for label in LABELS:
        m = y == label
        if m.any():
            ax.scatter(z[m, 0], z[m, 1], s=22, color=COLORS[label], label=name(label), alpha=0.8)
    ax.set_title(f"PCA đặc trưng MFCC{' (align)' if config.align else ''}")
    ax.set_xlabel('PC1'); ax.set_ylabel('PC2'); ax.legend(fontsize=7, loc='best')
    fig.tight_layout()
    return fig


def threshold_curve(training_report):
    plt = _plt()
    rec = training_report['threshold_search']
    fig, ax = plt.subplots(figsize=(6.5, 3.5))
    ax.plot([r['threshold'] for r in rec], [r['macro_f1'] for r in rec], marker='.', color='#4C78A8')
    best = training_report['selected']
    ax.axvline(best['threshold'], color='#E45756', ls='--', label=f"chọn {best['threshold']:.3f}")
    ax.set_xlabel('Ngưỡng từ chối'); ax.set_ylabel('Macro-F1 (validation)'); ax.set_ylim(0, 1.05)
    ax.set_title('Chọn ngưỡng trên validation'); ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig


def compare_bars(results):
    plt = _plt()
    names = [f"{r['classifier']}\n{'align' if r['align'] else '-'} aug{r['augment']}" for r in results]
    fig, ax = plt.subplots(figsize=(max(6, 0.75 * len(results)), 3.8))
    bars = ax.bar(range(len(results)), [r['validation_macro_f1'] for r in results],
                  color=['#E45756' if i == 0 else '#4C78A8' for i in range(len(results))])
    ax.bar_label(bars, fmt='%.2f', fontsize=8)
    ax.set_xticks(range(len(results)), names, fontsize=7); ax.set_ylim(0, 1.08)
    ax.set_ylabel('Macro-F1 (validation)'); ax.set_title('So sánh cấu hình (đỏ = tốt nhất)')
    fig.tight_layout()
    return fig


def learning_curve(points):
    plt = _plt()
    x = [p['train_clips'] for p in points]
    y = np.array([p['val_macro_f1_mean'] for p in points]); e = np.array([p['val_macro_f1_std'] for p in points])
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    ax.plot(x, y, marker='o', color='#4C78A8'); ax.fill_between(x, y - e, y + e, alpha=0.2, color='#4C78A8')
    ax.set_xlabel('Số bản thu train'); ax.set_ylabel('Macro-F1 (validation)'); ax.set_ylim(0, 1.05)
    ax.set_title('Learning curve'); ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig


def latency_hist(values_ms, title='Độ trễ'):
    plt = _plt()
    fig, ax = plt.subplots(figsize=(6.5, 3.2))
    ax.hist(values_ms, bins=20, color='#72B7B2')
    if len(values_ms):
        for q, ls in [(50, '-'), (95, '--')]:
            v = float(np.percentile(values_ms, q))
            ax.axvline(v, color='#E45756', ls=ls, label=f'p{q} = {v:.1f} ms')
        ax.legend()
    ax.set_xlabel('ms'); ax.set_ylabel('số lượt'); ax.set_title(title)
    fig.tight_layout()
    return fig
