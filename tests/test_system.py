import csv
import tempfile
import unittest
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from app.common import LABELS, RATE
from app.recorder import save_recording
from app.serial_client import SerialClient, Simulator, ProtocolError
from app.controller import Controller
from ml.features import extract, load_wav
from ml.dataset import read_manifest
from ml.prepare_data import split_manifest
from ml.train_baseline import train
from ml.predict import Predictor, Prediction
from ml.evaluate import evaluate

class FakeSerial:
    def __init__(self,response='ack',initial=b'READY,1\n'):
        self.rx=bytearray(initial);self.response=response;self.writes=[];self.closed=False
    def read(self,n):
        if not self.rx: return b''
        out=bytes(self.rx[:n]);del self.rx[:n];return out
    def write(self,packet):
        self.writes.append(packet);_,ident,action=packet.decode().strip().split(',')
        if self.response=='ack': self.rx.extend(f'ACK,999,{action}\nACK,{ident},{action}\n'.encode())
        elif self.response=='error': self.rx.extend(f'ERR,{ident},HARDWARE_ERROR\n'.encode())
        elif self.response=='mismatch': self.rx.extend(f'ACK,{ident},OTHER\n'.encode())
        elif self.response=='reset': self.rx.extend(b'READY,1\n')
        return len(packet)
    def close(self):self.closed=True

class SerialTests(unittest.TestCase):
    def test_ack_ignores_stale_id(self):
        fake=FakeSerial();client=SerialClient(transport=fake)
        self.assertTrue(client.send('LIGHT_ON')['ack'])
        self.assertEqual(fake.writes,[b'CMD,1,LIGHT_ON\n'])
        client.close();self.assertTrue(fake.closed)
    def test_errors_disable_session(self):
        for mode in ['error','mismatch','reset','timeout']:
            with self.subTest(mode=mode):
                fake=FakeSerial(mode);client=SerialClient(transport=fake,timeout=.002)
                with self.assertRaises((ProtocolError,TimeoutError)):client.send('FAN_ON')
                with self.assertRaises(ProtocolError):client.send('FAN_OFF')
                self.assertEqual(len(fake.writes),1)
    def test_ready_timeout_closes(self):
        fake=FakeSerial(initial=b'')
        with self.assertRaises(TimeoutError):SerialClient(transport=fake,ready_timeout=.002)
        self.assertTrue(fake.closed)
    def test_long_line_recovery(self):
        fake=FakeSerial(initial=b'x'*100+b'\nREADY,1\n')
        client=SerialClient(transport=fake)
        self.assertTrue(client.send('FAN_OFF')['ack'])
    def test_simulation_and_rejection(self):
        sim=Simulator();sim.send('LIGHT_ON');sim.send('LIGHT_ON')
        self.assertTrue(sim.state['light'])
        class Reject:
            def predict(self,audio):return Prediction('unknown','LIGHT_OFF',.4,False)
        controller=Controller(sim,Reject(),log=None)
        self.assertIsNone(controller.voice(np.zeros(10))['result']['action'])
        self.assertTrue(sim.state['light'])

class PipelineTests(unittest.TestCase):
    def test_audio_validation(self):
        self.assertEqual(extract(np.zeros(32000)).shape,(104,))
        self.assertTrue(np.isfinite(extract(np.zeros(32000))).all())
        for x in [np.array([]),np.array([np.nan]),np.zeros(32001)]:
            with self.assertRaises(ValueError):extract(x)
    def test_unsigned_stereo_resample(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'a.wav';wavfile.write(p,8000,np.full((8000,2),128,dtype=np.uint8))
            x=load_wav(p);self.assertEqual(len(x),16000);self.assertTrue(np.allclose(x,0))
    def test_end_to_end_synthetic_only(self):
        # These tones validate plumbing, NOT Vietnamese recognition quality.
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);manifest=base/'manifest.csv'
            rng=np.random.default_rng(9);t=np.arange(32000)/RATE
            for person in range(5):
                for k,label in enumerate(LABELS):
                    audio=.15*np.sin(2*np.pi*(180+200*k+person)*t)+rng.normal(0,.002,len(t))
                    save_recording(audio,manifest,f'p{person}','s1',label)
            split=base/'split.csv';split_manifest(manifest,split)
            rows=read_manifest(split)
            groups=[{r['speaker_id'] for r in rows if r['split']==s} for s in ['train','validation','test']]
            self.assertFalse(groups[0]&groups[1] or groups[0]&groups[2] or groups[1]&groups[2])
            model=base/'model.joblib';report=train(split,model)
            self.assertTrue(report['validation_only'])
            prediction=Predictor(model).predict_file(rows[0]['_file'])
            self.assertIn(prediction.label,LABELS)
            metrics=evaluate(split,model,base/'evaluation')
            self.assertEqual(metrics['samples'],6)
            self.assertTrue((base/'evaluation/predictions.csv').exists())
            # An edited split that leaks a speaker must fail.
            with split.open(newline='',encoding='utf-8') as f: data=list(csv.DictReader(f))
            data[0]['split']='test' if data[1]['split']!='test' else 'train'
            with split.open('w',newline='',encoding='utf-8') as f:
                w=csv.DictWriter(f,fieldnames=data[0].keys());w.writeheader();w.writerows(data)
            with self.assertRaises(ValueError):read_manifest(split)
    def _synthetic(self,base,units):
        manifest=base/'manifest.csv';rng=np.random.default_rng(3);t=np.arange(32000)/RATE
        for n,(speaker,session) in enumerate(units):
            for k,label in enumerate(LABELS):
                for rep in range(2):
                    audio=.15*np.sin(2*np.pi*(180+200*k+n+rep)*t)+rng.normal(0,.002,len(t))
                    save_recording(audio,manifest,speaker,session,label)
        return manifest
    def test_single_speaker_session_split(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);manifest=self._synthetic(base,[('p01','s01'),('p01','s02'),('p01','s03')])
            with self.assertRaises(ValueError):split_manifest(manifest,base/'auto.csv')
            split=base/'split.csv'
            summary=split_manifest(manifest,split,validation=['p01/s02'],test=['p01/s03'])
            self.assertEqual(summary,{'test':['p01/s03'],'train':['p01/s01'],'validation':['p01/s02']})
            model=base/'m.joblib';report=train(split,model)
            self.assertFalse(report['validation_new_speaker'])
            metrics=evaluate(split,model,base/'eval')
            self.assertEqual(metrics['evaluation_type'],'same_speaker_new_session')
            with self.assertRaises(ValueError):evaluate(split,model,base/'eval2',require_new_speaker=True)
    def test_two_speaker_manual_split(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);manifest=self._synthetic(base,[('p01','s01'),('p01','s02'),('p02','s01')])
            split=base/'split.csv'
            split_manifest(manifest,split,validation=['p01/s02'],test=['p02'])
            model=base/'m.joblib';train(split,model)
            metrics=evaluate(split,model,base/'eval',require_new_speaker=True)
            self.assertEqual(metrics['evaluation_type'],'new_speaker')
    def test_manual_split_rejects_bad_units(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);manifest=self._synthetic(base,[('p01','s01'),('p01','s02'),('p01','s03')])
            cases=[dict(validation=['p01/s02']),dict(validation=['p01/s09'],test=['p01/s03']),
                   dict(validation=['p01/s02'],test=['p01']),dict(validation=['p01/s02'],test=['a/b/c'])]
            for i,kw in enumerate(cases):
                with self.subTest(kw=kw),self.assertRaises(ValueError):split_manifest(manifest,base/f'o{i}.csv',**kw)
            # Missing labels in a session are reported before anything is written.
            only_two=self._synthetic(base/'b',[('p01','s01'),('p01','s02')])
            with self.assertRaises(ValueError):split_manifest(only_two,base/'b/o.csv',validation=['p01/s02'],test=['p01/s02'])
    def test_recording_path_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):save_recording(np.zeros(10),Path(tmp)/'m.csv','../bad','s1','LIGHT_ON')

if __name__=='__main__':unittest.main()
