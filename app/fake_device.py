"""Virtual firmware: a Python device that speaks docs/PROTOCOL.md v0.1.

Uses:
1. In-process (no extra software): run the app with --port fake
     python -m app.gui --model models/baseline.joblib --port fake
   The app talks to this device through the real SerialClient code path.
2. Over a virtual COM pair (Windows: com0com, e.g. COM10<->COM11):
     python -m app.fake_device --port COM11
     python -m app.gui --port COM10
   This also exercises pySerial and the OS serial driver.
3. Reference for the EE teammate: the firmware should behave like FakeDevice.

Fault injection (--fault) lets you check how the app handles device problems.
"""
import argparse
import random
import threading
import time
from collections import deque
from app.common import COMMANDS

MAX_LINE = 64           # bytes including LF
MAX_ID = 2147483647
FAULTS = ['none', 'timeout', 'error', 'reset', 'mismatch']


class FakeDevice:
    """Protocol logic only: bytes in, response lines out. No I/O, no timing."""

    def __init__(self, fault='none', fault_rate=1.0, seed=None):
        if fault not in FAULTS:
            raise ValueError('Unknown fault ' + fault)
        self.fault = fault; self.fault_rate = fault_rate
        self.rng = random.Random(seed)
        self.reset()

    def reset(self):
        # Outputs are OFF at boot (PROTOCOL.md: "Đầu ra OFF khi boot").
        self.state = {'light': False, 'fan': False}
        self.buffer = bytearray(); self.dropping = False

    def boot(self):
        self.reset()
        return ['READY,1']

    def feed(self, data):
        """Accept raw bytes; return the list of response lines (without LF)."""
        out = []
        for b in data:
            byte = bytes([b])
            if self.dropping:
                if byte == b'\n':
                    self.dropping = False
                continue
            if byte == b'\n':
                line = bytes(self.buffer); self.buffer.clear()
                out.extend(self.handle(line))
                continue
            self.buffer.extend(byte)
            if len(self.buffer) >= MAX_LINE:     # no room left for LF
                self.buffer.clear(); self.dropping = True
                out.append('ERR,0,BAD_FORMAT')
        return out

    def handle(self, line):
        if line.endswith(b'\r'):
            line = line[:-1]
        try:
            text = line.decode('ascii')
        except UnicodeDecodeError:
            return ['ERR,0,BAD_FORMAT']
        parts = text.split(',')
        if len(parts) != 3 or parts[0] != 'CMD':
            return ['ERR,0,BAD_FORMAT']
        ident, action = parts[1], parts[2]
        if not ident.isdigit() or not 1 <= int(ident) <= MAX_ID or ident != str(int(ident)):
            return ['ERR,0,BAD_FORMAT']
        if action not in COMMANDS:
            return [f'ERR,{ident},UNKNOWN_COMMAND']
        if self.fault != 'none' and self.rng.random() < self.fault_rate:
            if self.fault == 'timeout':
                return []
            if self.fault == 'error':
                return [f'ERR,{ident},HARDWARE_ERROR']
            if self.fault == 'reset':
                return self.boot()
            if self.fault == 'mismatch':
                return [f'ACK,{ident},LIGHT_ON' if action != 'LIGHT_ON' else f'ACK,{ident},LIGHT_OFF']
        device, value = action.split('_')
        self.state[device.lower()] = value == 'ON'
        return [f'ACK,{ident},{action}']


class FakeTransport:
    """Looks like a pySerial port to SerialClient, backed by a FakeDevice."""

    def __init__(self, device=None, latency_ms=5.0, read_timeout=0.05):
        self.device = device or FakeDevice()
        self.latency = latency_ms / 1000; self.read_timeout = read_timeout
        self.rx = deque(); self.lock = threading.Condition(); self.closed = False
        self._queue(self.device.boot(), delay=0)

    def _queue(self, lines, delay):
        due = time.monotonic() + delay
        with self.lock:
            for line in lines:
                self.rx.append((due, (line + '\n').encode('ascii')))
            self.lock.notify_all()

    def write(self, data):
        if self.closed:
            raise OSError('Port closed')
        self._queue(self.device.feed(bytes(data)), self.latency)
        return len(data)

    def read(self, n=1):
        deadline = time.monotonic() + self.read_timeout
        with self.lock:
            while True:
                now = time.monotonic()
                if self.rx and self.rx[0][0] <= now:
                    due, chunk = self.rx.popleft()
                    out, rest = chunk[:n], chunk[n:]
                    if rest:
                        self.rx.appendleft((due, rest))
                    return out
                if now >= deadline or self.closed:
                    return b''
                wait = deadline - now
                if self.rx:
                    wait = min(wait, max(0.0, self.rx[0][0] - now))
                self.lock.wait(wait)

    @property
    def state(self):
        return dict(self.device.state)

    def close(self):
        with self.lock:
            self.closed = True; self.lock.notify_all()


def serve(port, device, latency_ms=5.0, verbose=True):
    """Run the device on a real/virtual serial port until Ctrl+C."""
    import serial
    ser = serial.Serial(port, 115200, timeout=0.05)
    log = print if verbose else (lambda *a: None)

    def send(lines):
        for line in lines:
            ser.write((line + '\n').encode('ascii')); log('->', line)

    peer = None
    log(f'Fake device on {port}. Waiting for the app to open the other end (Ctrl+C to stop).')
    try:
        while True:
            try:
                # com0com wires the peer's DTR to our DSR: announce READY whenever
                # the app (re)opens its side, like a board that resets on connect.
                now_peer = ser.dsr
            except OSError:
                now_peer = True
            if now_peer and not peer:
                send(device.boot())
            peer = now_peer
            data = ser.read(64)
            if data:
                log('<-', data.decode('ascii', 'replace').strip())
                lines = device.feed(data)
                if lines:
                    time.sleep(latency_ms / 1000)
                    send(lines)
                    log('   state:', device.state)
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--port', required=True, help='Device side of a virtual COM pair, e.g. COM11')
    p.add_argument('--fault', choices=FAULTS, default='none')
    p.add_argument('--fault-rate', type=float, default=1.0, help='Probability a valid command hits the fault')
    p.add_argument('--latency-ms', type=float, default=5.0)
    a = p.parse_args()
    serve(a.port, FakeDevice(a.fault, a.fault_rate), a.latency_ms)


if __name__ == '__main__':
    main()
