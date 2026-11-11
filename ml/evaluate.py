import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix
from app.common import LABELS, COMMANDS
from ml.dataset import read_manifest, matrix
from ml.predict import Predictor, decide

def evaluate(manifest,model,output):
    out=Path(output)
    if out.exists(): raise ValueError('Evaluation directory exists; use a new output directory')
    rows=read_manifest(manifest); predictor=Predictor(model)
    x,y,selected=matrix(rows,'test',predictor.config)
    seen=set(predictor.bundle['train_speakers']+predictor.bundle['validation_speakers'])
    if seen & {r['speaker_id'] for r in selected}: raise ValueError('Test speaker was used for model selection/training')
    seen_audio=set(predictor.bundle['seen_audio_sha256'])
    if any(hashlib.sha256(Path(r['_file']).read_bytes()).hexdigest() in seen_audio for r in selected):
        raise ValueError('Test recording was used in training/validation')
    predictions=[decide(p,predictor.model.classes_,predictor.threshold) for p in predictor.model.predict_proba(x)]
    yp=np.array([p.label for p in predictions]);non=np.array([label not in COMMANDS for label in y])
    report={'scope':'held-out WAV classification, NOT physical device success',
            'model_sha256':hashlib.sha256(Path(model).read_bytes()).hexdigest(),
            'manifest_sha256':hashlib.sha256(Path(manifest).read_bytes()).hexdigest(),
            'samples':len(y),'speakers':sorted({r['speaker_id'] for r in selected}),
            'threshold':predictor.threshold,'labels':LABELS,
            'classification':classification_report(y,yp,labels=LABELS,output_dict=True,zero_division=0),
            'confusion_matrix':confusion_matrix(y,yp,labels=LABELS).tolist(),
            'false_activation_per_noncommand_trial':float(np.mean([p in COMMANDS for p in yp[non]])) if non.any() else None,
            'command_rejection_rate':float(np.mean([p not in COMMANDS for p in yp[~non]])) if (~non).any() else None}
    out.mkdir(parents=True)
    (out/'metrics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    with (out/'predictions.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.writer(f);writer.writerow(['path','speaker_id','expected','predicted','raw_label','score'])
        for row,p in zip(selected,predictions): writer.writerow([row['path'],row['speaker_id'],row['label'],p.label,p.raw_label,p.score])
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',default='data/manifest_split.csv')
    p.add_argument('--model',default='models/baseline.joblib');p.add_argument('--output',default='results/eval_01')
    a=p.parse_args();print(json.dumps(evaluate(a.manifest,a.model,a.output),indent=2))
if __name__=='__main__': main()
