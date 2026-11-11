from dataclasses import dataclass, asdict
import joblib
import numpy as np
from ml.features import FeatureConfig, extract, load_wav
from app.common import COMMANDS

@dataclass
class Prediction:
    label: str
    raw_label: str
    score: float
    accepted: bool
    def to_dict(self): return asdict(self)

def decide(probabilities, classes, threshold):
    idx=int(np.argmax(probabilities)); raw=str(classes[idx]); score=float(probabilities[idx])
    label=raw if score>=threshold or raw not in COMMANDS else 'unknown'
    return Prediction(label,raw,score,label in COMMANDS)

class Predictor:
    def __init__(self, path):
        # joblib/pickle is executable serialization: load only your own trusted model.
        self.bundle=joblib.load(path)
        if self.bundle.get('schema_version')!=1:
            raise ValueError('Unsupported model schema')
        self.config=FeatureConfig(**self.bundle['features'])
        self.model=self.bundle['pipeline']; self.threshold=self.bundle['threshold']
        if not 0<=self.threshold<=1:
            raise ValueError('Invalid threshold')
    def predict(self,audio):
        features=extract(audio,self.config)
        return decide(self.model.predict_proba([features])[0],self.model.classes_,self.threshold)
    def predict_file(self,path):
        return self.predict(load_wav(path,self.config.sample_rate))

def main():
    import argparse, json
    p=argparse.ArgumentParser()
    p.add_argument('wav');p.add_argument('--model',default='models/baseline.joblib')
    a=p.parse_args();print(json.dumps(Predictor(a.model).predict_file(a.wav).to_dict(),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
