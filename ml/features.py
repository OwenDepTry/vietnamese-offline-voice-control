"""Deterministic MFCC + temporal pooling. No learned normalization here."""
from dataclasses import dataclass, asdict
from math import gcd
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly
from scipy.fft import dct

@dataclass(frozen=True)
class FeatureConfig:
    sample_rate: int = 16000
    seconds: float = 2.0
    n_fft: int = 512
    frame: int = 400
    hop: int = 160
    n_mels: int = 40
    n_mfcc: int = 13
    bins: int = 4

    def to_dict(self):
        return asdict(self)

def load_wav(path, target_rate=16000):
    rate, audio = wavfile.read(path)
    if rate <= 0 or audio.size == 0:
        raise ValueError(f'Empty or invalid WAV: {path}')
    if np.issubdtype(audio.dtype, np.unsignedinteger):
        midpoint = (np.iinfo(audio.dtype).max + 1) / 2
        audio = (audio.astype(np.float64) - midpoint) / midpoint
    elif np.issubdtype(audio.dtype, np.signedinteger):
        audio = audio.astype(np.float64) / (-float(np.iinfo(audio.dtype).min))
    elif np.issubdtype(audio.dtype, np.floating):
        audio = audio.astype(np.float64)
    else:
        raise ValueError('Unsupported WAV encoding')
    if audio.ndim == 2:
        audio = audio.mean(axis=1)
    if audio.ndim != 1 or not np.isfinite(audio).all():
        raise ValueError('Invalid audio samples')
    if rate != target_rate:
        divisor = gcd(rate, target_rate)
        audio = resample_poly(audio, target_rate // divisor, rate // divisor)
    return np.clip(audio, -1, 1).astype(np.float32)

def extract(audio, config=None):
    c = config or FeatureConfig()
    x = np.asarray(audio, dtype=np.float64)
    if x.ndim != 1 or x.size == 0 or not np.isfinite(x).all():
        raise ValueError('Audio must be a non-empty finite mono array')
    # Reject long clips rather than silently classify only their beginning.
    size = int(c.seconds * c.sample_rate)
    if len(x) > size:
        raise ValueError(f'Clip exceeds {c.seconds}s; record one short command')
    x = np.pad(x, (0, size-len(x)))
    emphasized = np.append(x[0], x[1:] - 0.97*x[:-1])
    frames = np.lib.stride_tricks.sliding_window_view(emphasized, c.frame)[::c.hop]
    power = np.abs(np.fft.rfft(frames*np.hamming(c.frame), n=c.n_fft))**2 / c.n_fft
    mel_max = 2595*np.log10(1+(c.sample_rate/2)/700)
    edges = 700*(10**(np.linspace(0, mel_max, c.n_mels+2)/2595)-1)
    freqs = np.fft.rfftfreq(c.n_fft, 1/c.sample_rate)
    bank = np.maximum(0, np.minimum(
        (freqs[None,:]-edges[:-2,None])/(edges[1:-1]-edges[:-2])[:,None],
        (edges[2:,None]-freqs[None,:])/(edges[2:]-edges[1:-1])[:,None]))
    mfcc = dct(np.log(np.maximum(power @ bank.T, 1e-10)), type=2, axis=1, norm='ortho')[:,:c.n_mfcc]
    # Four temporal bins retain order (e.g. bat/tat) better than global averaging.
    chunks = np.array_split(mfcc, c.bins)
    vector = np.concatenate([v for part in chunks for v in (part.mean(0), part.std(0))])
    return vector.astype(np.float32)
