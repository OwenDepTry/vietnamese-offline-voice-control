"""Heuristic audio quality checks shared by the recorder and ml.check_data.

These rules only flag recordings for a human to listen to; they do not decide
whether a clip is correct. Thresholds were set on 16 kHz laptop-mic recordings.
"""
import numpy as np

FRAME_S = 0.02
QUIET_PEAK = 0.15        # speech labels: peak below this is likely too far/quiet
SPEECH_DB_ABOVE_FLOOR = 15
MIN_SPEECH_S = 0.15
EDGE_S = 0.04            # speech touching the clip edge is probably cut off
SILENCE_MAX_PEAK = 0.2
SILENCE_LOUD_DB = -35       # frames above this (dBFS) count as loud
SILENCE_MAX_LOUD_S = 0.2

DESCRIPTIONS = {
    'clipped': 'bị rè/quá to (chạm ngưỡng ±1)',
    'too_quiet': 'nói quá nhỏ hoặc quá xa micro',
    'no_speech': 'gần như không nghe thấy tiếng nói',
    'cut_start': 'tiếng nói bắt đầu ngay đầu file (có thể mất chữ đầu)',
    'cut_end': 'tiếng nói kéo tới cuối file (có thể mất chữ cuối)',
    'not_silent': 'nhãn silence nhưng có tiếng nói/tiếng động lớn',
    'wrong_length': 'độ dài khác 2 giây',
}


def analyze(audio, rate=16000):
    """Return loudness stats and the detected speech region (seconds)."""
    x = np.asarray(audio, dtype=np.float64)
    if x.ndim != 1 or x.size == 0:
        raise ValueError('Audio must be a non-empty mono array')
    hop = max(1, int(rate * FRAME_S))
    n = max(1, len(x) // hop)
    frames = x[:n * hop].reshape(n, hop) if len(x) >= hop else x[None, :]
    db = 20 * np.log10(np.sqrt((frames ** 2).mean(axis=1)) + 1e-9)
    floor = float(np.percentile(db, 10))
    active = np.where((db > floor + SPEECH_DB_ABOVE_FLOOR) & (db > -50))[0]
    stats = {'seconds': len(x) / rate, 'peak': float(np.abs(x).max()),
             'max_db': float(db.max()), 'floor_db': floor,
             'active_s': float(len(active) * FRAME_S),
             'loud_s': float((db > SILENCE_LOUD_DB).sum() * FRAME_S),
             'speech_start': None, 'speech_end': None}
    if len(active):
        stats['speech_start'] = float(active[0] * FRAME_S)
        stats['speech_end'] = float((active[-1] + 1) * FRAME_S)
    return stats


def issues(stats, label, expected_seconds=2.0):
    found = []
    if abs(stats['seconds'] - expected_seconds) > 0.01:
        found.append('wrong_length')
    if stats['peak'] >= 0.99:
        found.append('clipped')
    if label == 'silence':
        # Relative-to-floor activity is too sensitive in a quiet room (breathing),
        # so silence uses absolute loudness.
        if stats['peak'] > SILENCE_MAX_PEAK or stats['loud_s'] > SILENCE_MAX_LOUD_S:
            found.append('not_silent')
        return found
    if stats['active_s'] < MIN_SPEECH_S:
        found.append('no_speech')
        return found
    if stats['peak'] < QUIET_PEAK:
        found.append('too_quiet')
    if stats['speech_start'] is not None and stats['speech_start'] <= EDGE_S / 2:
        found.append('cut_start')
    if stats['speech_end'] is not None and stats['speech_end'] >= stats['seconds'] - EDGE_S:
        found.append('cut_end')
    return found


def describe(codes):
    return '; '.join(DESCRIPTIONS.get(c, c) for c in codes)
