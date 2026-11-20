"""The conformance checker passes the reference virtual firmware and catches common firmware bugs."""
import unittest
from app.conformance import run, report
from app.fake_device import FakeDevice, FakeTransport


class Chatty(FakeDevice):
    """Prints debug text on the protocol channel."""
    def handle(self, line):
        return ['debug: got line'] + super().handle(line)


class AcceptsAnything(FakeDevice):
    """Treats unknown actions as OK (no validation)."""
    def handle(self, line):
        parts = line.decode('ascii', 'replace').strip().split(',')
        if len(parts) == 3 and parts[0] == 'CMD' and parts[1].isdigit() and parts[2] == 'TOGGLE':
            return [f'ACK,{parts[1]},TOGGLE']
        return super().handle(line)


class Silent(FakeDevice):
    def boot(self):
        self.reset(); return []


def failed(device, **kw):
    checks = run(FakeTransport(device), ready_timeout=0.3, **kw)
    return [c.name for c in checks if not c.ok]


class ConformanceTests(unittest.TestCase):
    def test_reference_passes(self):
        checks = run(FakeTransport(FakeDevice()))
        self.assertTrue(report(checks, out=lambda *_: None), [c for c in checks if not c.ok])
        self.assertGreaterEqual(len(checks), 19)

    def test_detects_bugs(self):
        self.assertTrue(any('ACK đúng id' in n for n in failed(Chatty())))
        self.assertEqual(failed(AcceptsAnything()), ['Lệnh lạ → ERR,id,UNKNOWN_COMMAND'])
        self.assertEqual(failed(Silent()), ['Gửi READY,1 khi mở cổng'])

    def test_observe_mode(self):
        answers = iter(['', 'n', '', ''])
        names = failed(FakeDevice(), observe=True, ask=lambda *_: next(answers))
        self.assertEqual(names, ['LIGHT_OFF → ACK đúng id'])


if __name__ == '__main__':
    unittest.main()
