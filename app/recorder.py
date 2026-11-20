import argparse
import csv
import re
import uuid
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from app.common import RATE, LABELS
from ml.dataset import FIELDS

def record(seconds=2.0,device=None):
    if not 0<seconds<=2.0: raise ValueError('Recording length must be in (0,2] seconds')
    import sounddevice as sd
    audio=sd.rec(round(seconds*RATE),samplerate=RATE,channels=1,dtype='float32',device=device)
    status=sd.wait()
    if status: raise RuntimeError('Audio overflow/underflow: '+str(status))
    return audio[:,0].copy()

def save_recording(audio,manifest,speaker,session,label,noise='quiet',distance='1'):
    if not all(re.fullmatch(r'[A-Za-z0-9_-]+',v) for v in [speaker,session]):
        raise ValueError('Use anonymous speaker/session ids: letters, digits, _ or -')
    if label not in LABELS: raise ValueError('Invalid label')
    if not np.isfinite(float(distance)) or float(distance)<=0: raise ValueError('Distance must be positive')
    audio=np.asarray(audio)
    if audio.ndim!=1 or not 0<len(audio)<=2*RATE or not np.isfinite(audio).all(): raise ValueError('Invalid audio')
    manifest=Path(manifest).resolve();manifest.parent.mkdir(parents=True,exist_ok=True)
    if manifest.exists():
        with manifest.open(encoding='utf-8',newline='') as f:
            if next(csv.reader(f),[])!=FIELDS: raise ValueError('Manifest header differs from expected schema')
    relative=Path('raw')/speaker/session/(label+'_'+uuid.uuid4().hex+'.wav')
    path=manifest.parent/relative;path.parent.mkdir(parents=True,exist_ok=True)
    wavfile.write(path,RATE,(np.clip(audio,-1,1)*32767).astype(np.int16))
    new=not manifest.exists()
    with manifest.open('a',encoding='utf-8',newline='') as f:
        writer=csv.writer(f)
        if new: writer.writerow(FIELDS)
        writer.writerow([relative.as_posix(),speaker,session,label,'',noise,distance])
    return path

def play(audio,device=None):
    import sounddevice as sd
    sd.play(audio,RATE,device=device);sd.wait()

def review(audio,label):
    """Return quality flags for a fresh recording (empty list = looks fine)."""
    from ml.quality import analyze, issues
    return issues(analyze(audio,RATE),label)

def main():
    p=argparse.ArgumentParser(description='Collect 2-second recordings; press Enter for each sample')
    p.add_argument('--speaker',required=True);p.add_argument('--session',default='s01')
    p.add_argument('--label',choices=LABELS,required=True);p.add_argument('--count',type=int,default=15)
    p.add_argument('--manifest',default='data/manifest.csv');p.add_argument('--device',type=int)
    p.add_argument('--output-device',type=int,help='Speaker/headphone device for playback (p)')
    p.add_argument('--noise',default='quiet');p.add_argument('--distance',default='1')
    p.add_argument('--no-review',action='store_true',help='Save every take immediately (old behaviour)')
    p.add_argument('--consent',action='store_true',help='Confirm speaker agreed to recording and intended use')
    a=p.parse_args()
    if not a.consent: p.error('Obtain permission then pass --consent; do not publish private audio')
    if a.count<1: p.error('--count must be positive')
    from ml.quality import describe
    saved=0
    while saved<a.count:
        input(f'{saved+1}/{a.count} {a.label}: Enter to record 2 seconds...')
        audio=record(device=a.device)
        if not a.no_review:
            flags=review(audio,a.label)
            while True:
                hint=('CẢNH BÁO: '+describe(flags)) if flags else 'Nghe ổn.'
                choice=input(f'  {hint}  [Enter]=lưu  r=thu lại  p=nghe lại: ').strip().lower()
                if choice=='p':
                    try: play(audio,a.output_device)
                    except Exception as exc: print('  Không phát được:',exc)
                    continue
                break
            if choice=='r':
                print('  Đã bỏ bản thu này.');continue
        elif np.max(np.abs(audio))>=0.99: print('Warning: audio may be clipped; check microphone gain.')
        path=save_recording(audio,a.manifest,a.speaker,a.session,a.label,a.noise,a.distance)
        saved+=1;print('Saved:',path)
if __name__=='__main__': main()
