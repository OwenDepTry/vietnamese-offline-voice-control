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
from sklearn.metrics import f1_score
from app.common import LABELS, COMMANDS
from ml.dataset import read_manifest, matrix
from ml.features import FeatureConfig
from ml.predict import decide

def train(manifest, output, seed=42):
    output=Path(output)
    if output.exists(): raise ValueError('Model exists; use another output path to preserve experiments')
    rows=read_manifest(manifest); config=FeatureConfig()
    x,y,train_rows=matrix(rows,'train',config)
    vx,vy,val_rows=matrix(rows,'validation',config)
    for name,labels in [('train',y),('validation',vy)]:
        if set(labels)!=set(LABELS): raise ValueError(name+' must contain every command, unknown and silence')
    pipeline=make_pipeline(StandardScaler(),LogisticRegression(max_iter=2000,class_weight='balanced',random_state=seed))
    pipeline.fit(x,y)
    probs=pipeline.predict_proba(vx)
    records=[]
    for threshold in np.linspace(0,1,41):
        pred=[decide(p,pipeline.classes_,float(threshold)).label for p in probs]
        score=float(f1_score(vy,pred,labels=LABELS,average='macro',zero_division=0))
        records.append({'threshold':float(threshold),'macro_f1':score})
    # Conservative threshold on ties. Scores are not calibrated confidence guarantees.
    best=max(records,key=lambda r:(r['macro_f1'],r['threshold']))
    bundle={'schema_version':1,'pipeline':pipeline,'features':config.to_dict(),'threshold':best['threshold'],
            'seed':seed,'created_utc':datetime.now(timezone.utc).isoformat(),
            'manifest_sha256':hashlib.sha256(Path(manifest).read_bytes()).hexdigest(),
            'versions':{p:importlib.metadata.version(p) for p in ['numpy','scipy','scikit-learn','joblib']},
            'train_speakers':sorted({r['speaker_id'] for r in train_rows}),
            'validation_speakers':sorted({r['speaker_id'] for r in val_rows}),
            'seen_audio_sha256':[hashlib.sha256(Path(r['_file']).read_bytes()).hexdigest() for r in train_rows+val_rows]}
    output.parent.mkdir(parents=True,exist_ok=True);joblib.dump(bundle,output)
    report={'validation_only':True,'selection_metric':'macro_f1','selected':best,'threshold_search':records,
            'train_samples':len(y),'validation_samples':len(vy),'versions':bundle['versions']}
    output.with_suffix('.training.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report

def main():
    p=argparse.ArgumentParser(description='Train MFCC + logistic regression; tune rejection on validation only')
    p.add_argument('--manifest',default='data/manifest_split.csv');p.add_argument('--output',default='models/baseline.joblib')
    p.add_argument('--seed',type=int,default=42);a=p.parse_args()
    print(json.dumps(train(a.manifest,a.output,a.seed),indent=2))
if __name__=='__main__': main()
