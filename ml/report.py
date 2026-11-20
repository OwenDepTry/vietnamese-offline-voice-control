"""Figures for the report from an ml.evaluate output folder.

  python -m ml.report --eval results/eval_01

Writes confusion_matrix.png, per_class_f1.png and summary.md into that folder
(refuses to overwrite). Needs matplotlib (pip install matplotlib).
"""
import argparse
import json
from pathlib import Path
from app.common import COMMANDS, LABELS


def display_name(label):
    return f'{label}\n({COMMANDS[label]})' if label in COMMANDS else label


def _plt():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    return plt


def confusion_png(metrics, path):
    plt = _plt()
    import numpy as np
    cm = np.array(metrics['confusion_matrix'], dtype=float)
    labels = metrics.get('labels', LABELS)
    rows = cm.sum(axis=1, keepdims=True)
    share = np.divide(cm, rows, out=np.zeros_like(cm), where=rows > 0)
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    im = ax.imshow(share, cmap='Blues', vmin=0, vmax=1)
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, int(cm[i, j]), ha='center', va='center',
                    color='white' if share[i, j] > 0.6 else 'black', fontsize=11)
    names = [display_name(l) for l in labels]
    ax.set_xticks(range(len(labels)), names, rotation=45, ha='right', fontsize=8)
    ax.set_yticks(range(len(labels)), names, fontsize=8)
    ax.set_xlabel('Dự đoán'); ax.set_ylabel('Nhãn thật')
    ax.set_title(f"Confusion matrix — {metrics.get('evaluation_type', '')}, n={metrics['samples']}")
    fig.colorbar(im, ax=ax, fraction=0.046, label='Tỉ lệ theo hàng')
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


def f1_png(metrics, path):
    plt = _plt()
    labels = metrics.get('labels', LABELS)
    scores = [metrics['classification'][l]['f1-score'] for l in labels]
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    bars = ax.bar(range(len(labels)), scores, color='#4C78A8')
    ax.bar_label(bars, fmt='%.2f', fontsize=9)
    ax.set_xticks(range(len(labels)), [display_name(l) for l in labels], fontsize=8)
    ax.set_ylim(0, 1.08); ax.set_ylabel('F1'); ax.set_title('F1 theo nhãn')
    ax.spines[['top', 'right']].set_visible(False)
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


def summary_md(metrics):
    c = metrics['classification']
    lines = [f"# Kết quả đánh giá", '',
             f"- Loại đánh giá: `{metrics.get('evaluation_type', 'n/a')}`"
             + (' (cùng người với train, phiên mới — chưa chứng minh nhận được người lạ)'
                if metrics.get('evaluation_type') == 'same_speaker_new_session' else ''),
             f"- Số mẫu test: {metrics['samples']}; người nói: {', '.join(metrics['speakers'])}",
             f"- Ngưỡng từ chối (chọn trên validation): {metrics['threshold']:.3f}",
             f"- Accuracy: {c['accuracy']:.3f}; macro-F1: {c['macro avg']['f1-score']:.3f}"]
    if metrics.get('false_activation_per_noncommand_trial') is not None:
        lines.append(f"- Kích hoạt nhầm trên mẫu không phải lệnh: {metrics['false_activation_per_noncommand_trial']:.3f}")
    if metrics.get('command_rejection_rate') is not None:
        lines.append(f"- Tỉ lệ bỏ sót lệnh đúng: {metrics['command_rejection_rate']:.3f}")
    lines += ['', '| Nhãn | Precision | Recall | F1 | Số mẫu |', '|---|---|---|---|---|']
    for l in metrics.get('labels', LABELS):
        r = c[l]
        lines.append(f"| {l} | {r['precision']:.2f} | {r['recall']:.2f} | {r['f1-score']:.2f} | {int(r['support'])} |")
    lines += ['', f"Phạm vi: {metrics.get('scope', '')}"]
    return '\n'.join(lines) + '\n'


def report(eval_dir):
    d = Path(eval_dir)
    metrics = json.loads((d / 'metrics.json').read_text(encoding='utf-8'))
    outputs = [d / 'confusion_matrix.png', d / 'per_class_f1.png', d / 'summary.md']
    for path in outputs:
        if path.exists():
            raise ValueError(f'{path} exists; delete it or evaluate into a new folder')
    confusion_png(metrics, outputs[0]); f1_png(metrics, outputs[1])
    outputs[2].write_text(summary_md(metrics), encoding='utf-8')
    return outputs


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--eval', default='results/eval_01', help='Folder written by ml.evaluate')
    for path in report(p.parse_args().eval):
        print('Wrote', path)


if __name__ == '__main__':
    main()
