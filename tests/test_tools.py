"""Tests for data tools, virtual firmware, model options, reports and trial logging.

Synthetic tones check plumbing only, NOT Vietnamese recognition quality.
"""
import builtins
import csv
import importlib.util
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock
import numpy as np
from app.common import LABELS, RATE
from app.recorder import save_recording
from app import recorder
from app.fake_device import FakeDevice, FakeTransport
from app.serial_client import SerialClient, ProtocolError, open_backend, device_state
from app.controller import Controller
from app.trials import append_trial, set_last_physical, FIELDS as TRIAL_FIELDS
from ml.quality import analyze, issues
from ml.check_data import check, drop_flagged
from ml.merge_manifest import merge
from ml.dataset import read_manifest
from ml.features import FeatureConfig, extract
from ml.prepare_data import split_manifest
from ml.train_baseline import train, augment_audio
from ml.compare import compare
from ml.learning_curve import curve
from ml.evaluate import evaluate
from ml.predict import Predictor
from ml.trial_report import summarize_trials, summarize_events

HAS_MPL = importlib.util.find_spec('matplotlib') is not None
T = np.arange(2 * RATE) / RATE


def word(start=0.5, length=0.6, freq=300.0, amp=0.4, noise=0.002, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.normal(0, noise, len(T))
    s, e = int(start * RATE), int((start + length) * RATE)
    x[s:e] += amp * np.sin(2 * np.pi * freq * T[s:e])
    return x


def dataset(base, units, reps=3):
    manifest = Path(base) / 'manifest.csv'
    for n, (speaker, session) in enumerate(units):
        for k, label in enumerate(LABELS):
            for rep in range(reps):
                audio = (word(0.4 + 0.1 * rep, freq=180 + 200 * k + n, seed=rep + 10 * n)
                         if label != 'silence' else np.random.default_rng(100 + rep + 10 * n).normal(0, 0.003, len(T)))
                save_recording(audio, manifest, speaker, session, label)
    return manifest


class QualityTests(unittest.TestCase):
    def test_flags(self):
        self.assertEqual(issues(analyze(word()), 'LIGHT_ON'), [])
        self.assertIn('too_quiet', issues(analyze(word(amp=0.05)), 'LIGHT_ON'))
        self.assertIn('cut_end', issues(analyze(word(start=1.6, length=0.4)), 'FAN_ON'))
        self.assertIn('clipped', issues(analyze(np.clip(word(amp=2), -1, 1)), 'FAN_ON'))
        self.assertIn('no_speech', issues(analyze(word(amp=0)), 'unknown'))
        self.assertEqual(issues(analyze(word(amp=0)), 'silence'), [])
        self.assertIn('not_silent', issues(analyze(word()), 'silence'))

    def test_check_and_drop(self):
        with tempfile.TemporaryDirectory() as tmp:
            m = Path(tmp) / 'data' / 'manifest.csv'
            save_recording(word(), m, 'p01', 's01', 'LIGHT_ON')
            save_recording(word(amp=0.05), m, 'p01', 's01', 'LIGHT_ON')
            results, counts, sessions, missing = check(m)
            self.assertEqual(sum(bool(r['issues']) for r in results), 1)
            self.assertIn(('p01', 's01'), missing)
            out = Path(tmp) / 'clean' / 'manifest.csv'
            self.assertEqual(drop_flagged(results, out), 1)
            self.assertEqual(len(read_manifest(out, require_splits=False)), 1)
            with self.assertRaises(ValueError): drop_flagged(results, out)

    def test_recorder_redo_and_play(self):
        takes = iter([word(amp=0.05), word(), word(seed=3)])
        answers = iter(['', 'r', '', 'p', '', '', ''])
        with tempfile.TemporaryDirectory() as tmp:
            m = Path(tmp) / 'manifest.csv'
            argv = ['rec', '--speaker', 'p01', '--label', 'LIGHT_ON', '--count', '2', '--manifest', str(m), '--consent']
            with mock.patch.object(recorder, 'record', lambda device=None: next(takes)), \
                 mock.patch.object(recorder, 'play') as play, \
                 mock.patch.object(builtins, 'input', lambda *_: next(answers)), \
                 mock.patch('sys.argv', argv), mock.patch('builtins.print'):
                recorder.main()
            self.assertEqual(len(read_manifest(m, require_splits=False)), 2)
            play.assert_called_once()


class MergeTests(unittest.TestCase):
    def test_merge_rename_and_guards(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / 'data' / 'manifest.csv'; inc = Path(tmp) / 'other' / 'manifest.csv'
            save_recording(word(), base, 'p01', 's01', 'LIGHT_ON')
            save_recording(word(seed=5), inc, 'p01', 's01', 'FAN_ON')
            with self.assertRaises(ValueError): merge(base, inc)                 # same speaker/session id
            with self.assertRaises(ValueError): merge(base, inc, ['bad'])
            self.assertEqual(merge(base, inc, ['p01=p02'], dry_run=True), {'p02/s01': 1})
            self.assertEqual(len(read_manifest(base, require_splits=False)), 1)
            self.assertEqual(merge(base, inc, ['p01=p02']), {'p02/s01': 1})
            rows = read_manifest(base, require_splits=False)
            self.assertEqual(sorted(r['speaker_id'] for r in rows), ['p01', 'p02'])
            self.assertTrue(all(Path(r['_file']).is_relative_to(base.parent) for r in rows))
            self.assertEqual(len(list(base.parent.glob('manifest.csv.bak-*'))), 1)
            with self.assertRaises(ValueError): merge(base, inc, ['p01=p03'])    # same audio twice


class FakeDeviceTests(unittest.TestCase):
    def test_protocol(self):
        d = FakeDevice()
        self.assertEqual(d.boot(), ['READY,1'])
        self.assertEqual(d.feed(b'CMD,1,LIGHT_ON\n'), ['ACK,1,LIGHT_ON'])
        self.assertTrue(d.state['light'])
        self.assertEqual(d.feed(b'CMD,2,FAN_ON\r\n'), ['ACK,2,FAN_ON'])
        cases = {b'CMD,3,TOGGLE\n': 'ERR,3,UNKNOWN_COMMAND', b'CMD,x,FAN_ON\n': 'ERR,0,BAD_FORMAT',
                 b'CMD,0,FAN_ON\n': 'ERR,0,BAD_FORMAT', b'CMD,2147483648,FAN_ON\n': 'ERR,0,BAD_FORMAT',
                 b'HELLO\n': 'ERR,0,BAD_FORMAT', b'CMD,4,FAN_OFF,1\n': 'ERR,0,BAD_FORMAT'}
        for packet, reply in cases.items():
            with self.subTest(packet=packet): self.assertEqual(d.feed(packet), [reply])
        self.assertTrue(d.state['fan'])                                       # bad lines change nothing
        self.assertEqual(d.feed(b'C' * 63 + b'\n'), ['ERR,0,BAD_FORMAT'])      # 64 bytes incl LF: parsed
        self.assertEqual(d.feed(b'C' * 64 + b'\n'), ['ERR,0,BAD_FORMAT'])      # too long: dropped
        self.assertEqual(d.feed(b'CMD,5,FAN_OFF\n'), ['ACK,5,FAN_OFF'])        # recovers after LF
        self.assertEqual(d.feed(b'CMD,6,'), []); self.assertEqual(d.feed(b'LIGHT_OFF\n'), ['ACK,6,LIGHT_OFF'])

    def test_serial_client_against_virtual_firmware(self):
        client = open_backend('fake')
        self.assertTrue(client.send('FAN_ON')['ack'])
        self.assertEqual(device_state(client), {'light': False, 'fan': True})
        for fault, err in [('error', ProtocolError), ('reset', ProtocolError), ('mismatch', ProtocolError)]:
            with self.subTest(fault=fault):
                c = SerialClient(transport=FakeTransport(FakeDevice(fault)))
                with self.assertRaises(err): c.send('LIGHT_ON')
                with self.assertRaises(ProtocolError): c.send('LIGHT_ON')
        c = SerialClient(transport=FakeTransport(FakeDevice('timeout')), timeout=0.05)
        with self.assertRaises(TimeoutError): c.send('LIGHT_ON')

    def test_partial_fault_rate(self):
        c = SerialClient(transport=FakeTransport(FakeDevice('error', fault_rate=0.0)))
        self.assertTrue(c.send('LIGHT_ON')['ack'])


class ModelOptionTests(unittest.TestCase):
    def test_align_reduces_timing_differences(self):
        early, late = word(start=0.2, seed=1), word(start=1.0, seed=1)
        plain = np.linalg.norm(extract(early) - extract(late))
        aligned = np.linalg.norm(extract(early, FeatureConfig(align=True)) - extract(late, FeatureConfig(align=True)))
        self.assertLess(aligned, plain / 3)
        silence = np.random.default_rng(0).normal(0, 0.003, len(T))
        self.assertTrue(np.allclose(extract(silence), extract(silence, FeatureConfig(align=True))))

    def test_augment(self):
        rng = np.random.default_rng(0)
        y = augment_audio(word().astype(np.float32), rng, [np.random.default_rng(1).normal(0, .01, len(T))])
        self.assertEqual(y.shape, (len(T),)); self.assertTrue(np.isfinite(y).all()); self.assertLessEqual(np.abs(y).max(), 1)

    def test_classifiers_compare_curve_evaluate(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            manifest = dataset(base, [('p01', 's01'), ('p01', 's02'), ('p01', 's03')])
            split = base / 'split.csv'
            split_manifest(manifest, split, validation=['p01/s02'], test=['p01/s03'])
            table = compare(split, augments=(0, 1))
            self.assertEqual(len(table), 12)
            self.assertTrue(all(0 <= r['validation_macro_f1'] <= 1 for r in table))
            for clf in ['svm', 'mlp']:
                model = base / f'{clf}.joblib'
                report = train(split, model, classifier=clf, align=True, augment=1)
                self.assertEqual(report['train_samples_with_augmentation'], 2 * report['train_samples'])
                self.assertEqual(Predictor(model).config.align, True)
                metrics = evaluate(split, model, base / f'eval_{clf}')
                self.assertEqual(metrics['samples'], len(LABELS) * 3)
            points = curve(split, [0.34, 1.0], repeats=2)
            self.assertEqual([p['train_clips'] for p in points], [len(LABELS), len(LABELS) * 3])
            if HAS_MPL:
                from ml.report import report as make_report
                outputs = make_report(base / 'eval_svm')
                self.assertTrue(all(p.exists() and p.stat().st_size > 0 for p in outputs))
                with self.assertRaises(ValueError): make_report(base / 'eval_svm')


@unittest.skipUnless(HAS_MPL, 'matplotlib not installed')
class VizTests(unittest.TestCase):
    def test_figures(self):
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from ml import viz
        with tempfile.TemporaryDirectory() as tmp:
            rows = read_manifest(dataset(tmp, [('p01', 's01')], reps=2), require_splits=False)
            stats = [{'label': r['label'], **analyze(word())} for r in rows]
            figs = [viz.examples(rows), viz.speech_timing(stats), viz.feature_map(rows),
                    viz.threshold_curve({'threshold_search': [{'threshold': 0.0, 'macro_f1': 0.5}, {'threshold': 1.0, 'macro_f1': 0.2}],
                                         'selected': {'threshold': 0.0, 'macro_f1': 0.5}}),
                    viz.compare_bars([{'classifier': 'logreg', 'align': False, 'augment': 0, 'validation_macro_f1': 0.8}]),
                    viz.learning_curve([{'train_clips': 6, 'val_macro_f1_mean': 0.5, 'val_macro_f1_std': 0.1},
                                        {'train_clips': 12, 'val_macro_f1_mean': 0.7, 'val_macro_f1_std': 0.0}]),
                    viz.latency_hist([5.0, 6.0, 7.5])]
            self.assertTrue(all(f.axes for f in figs))
            plt.close('all')


class TrialTests(unittest.TestCase):
    def test_trial_logging_and_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'measurements.csv'
            path.write_text(','.join(TRIAL_FIELDS) + '\n', encoding='utf-8')     # repo ships header only

            class Fixed:
                def __init__(self, label): self.label = label
                def predict(self, audio):
                    from ml.predict import Prediction
                    return Prediction(self.label, self.label, 0.9, self.label in ('FAN_ON', 'LIGHT_ON'))
            log = Path(tmp) / 'events.jsonl'
            for intended, heard in [('FAN_ON', 'FAN_ON'), ('LIGHT_ON', 'unknown'), ('unknown', 'LIGHT_ON'), ('silence', 'silence')]:
                event = Controller(open_backend('fake'), Fixed(heard), log).voice(np.zeros(10))
                append_trial(path, event, intended, 'p01', 'quiet', commit='abc')
            append_trial(path, {'error': 'Device error'}, 'FAN_ON', 'p01', 'noisy', commit='abc')
            set_last_physical(path, 'no'); set_last_physical(path, 'yes', trial_id=1)
            with path.open(encoding='utf-8') as f: rows = list(csv.DictReader(f))
            self.assertEqual([r['trial_id'] for r in rows], ['1', '2', '3', '4', '5'])
            self.assertEqual([r['ack_received'] for r in rows], ['yes', 'not_sent', 'yes', 'not_sent', 'error'])
            s = summarize_trials(path)
            self.assertEqual(s['ALL']['trials'], 5)
            self.assertAlmostEqual(s['quiet']['correct_action'], 0.5)
            self.assertAlmostEqual(s['quiet']['false_activation'], 0.5)
            self.assertAlmostEqual(s['ALL']['physical_success'], 0.5)
            e = summarize_events(log)
            self.assertEqual(e['voice_events'], 4); self.assertIsNotNone(e['voice_latency_p95_ms'])
            with self.assertRaises(ValueError): append_trial(path, {}, 'NOT_A_LABEL')


@unittest.skipUnless(importlib.util.find_spec('tkinter'), 'tkinter not installed')
class GuiTextTests(unittest.TestCase):
    def test_describe_event(self):
        from app.gui import describe_event
        voice = {'source': 'voice', 'post_record_ms': 12.0, 'result': {'ack': True},
                 'prediction': {'label': 'FAN_ON', 'raw_label': 'FAN_ON', 'score': 0.9, 'accepted': True}}
        self.assertIn('bật quạt', describe_event(True, voice)[1])
        rejected = dict(voice, prediction={'label': 'unknown', 'raw_label': 'FAN_ON', 'score': 0.4, 'accepted': False})
        self.assertIn('Chưa chắc chắn', describe_event(True, rejected)[1])
        self.assertIn('LỖI', describe_event(False, 'boom')[0])


if __name__ == '__main__':
    unittest.main()
