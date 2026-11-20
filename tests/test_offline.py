"""The whole pipeline must work with networking disabled (TEST_PLAN: "Tắt Internet").

Every socket connect / DNS lookup raises during the test, so any hidden network
call (download, telemetry, API) would fail it. Complements the manual Wi-Fi-off demo.
"""
import socket
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import numpy as np
from app.common import LABELS, RATE
from app.controller import Controller
from app.recorder import save_recording
from app.serial_client import open_backend, device_state
from app.trials import append_trial
from ml.evaluate import evaluate
from ml.features import load_wav
from ml.predict import Predictor
from ml.prepare_data import split_manifest
from ml.train_baseline import train


class NetworkUsed(AssertionError):
    pass


def _blocked(*args, **kwargs):
    raise NetworkUsed(f'network access attempted: {args[:2]}')


class OfflineTests(unittest.TestCase):
    def test_pipeline_without_network(self):
        patches = [mock.patch.object(socket.socket, 'connect', _blocked),
                   mock.patch.object(socket.socket, 'connect_ex', _blocked),
                   mock.patch.object(socket, 'create_connection', _blocked),
                   mock.patch.object(socket, 'getaddrinfo', _blocked)]
        for p in patches:
            p.start()
        self.addCleanup(lambda: [p.stop() for p in patches])
        with self.assertRaises(NetworkUsed):          # the guard itself works
            socket.create_connection(('example.com', 80))
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); manifest = base / 'manifest.csv'
            t = np.arange(2 * RATE) / RATE; rng = np.random.default_rng(0)
            for n, session in enumerate(['s01', 's02', 's03']):
                for k, label in enumerate(LABELS):
                    for rep in range(2):
                        audio = (0.3 * np.sin(2 * np.pi * (200 + 180 * k + 7 * rep + n) * t) * (t > 0.5) * (t < 1.1)
                                 if label != 'silence' else np.zeros_like(t)) + rng.normal(0, 0.003, len(t))
                        save_recording(audio, manifest, 'p01', session, label)
            split = base / 'split.csv'
            split_manifest(manifest, split, validation=['p01/s02'], test=['p01/s03'])
            model = base / 'model.joblib'
            train(split, model, classifier='mlp', align=True, augment=1)
            evaluate(split, model, base / 'eval')
            predictor = Predictor(model)
            controller = Controller(open_backend('fake'), predictor, base / 'events.jsonl')
            fan_on = next(p for p in sorted((base / 'raw' / 'p01' / 's03').glob('FAN_ON_*.wav')))
            event = controller.voice(load_wav(fan_on))
            append_trial(base / 'measurements.csv', event, 'FAN_ON', 'p01', 'offline-test', commit='test')
            controller.manual('LIGHT_ON')
            self.assertTrue(device_state(controller.backend)['light'])


if __name__ == '__main__':
    unittest.main()
