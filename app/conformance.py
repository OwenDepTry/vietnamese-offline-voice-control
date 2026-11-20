"""Check a firmware against docs/PROTOCOL.md over a serial port.

  python -m app.conformance --port COM5
  python -m app.conformance --port COM5 --observe     # also confirm LED/fan by eye
  python -m app.conformance --port fake               # self-check with the virtual firmware

Sends a fixed list of valid and invalid lines and compares the replies with what
the protocol requires (the same behaviour as app/fake_device.py). Exit code 0 only
if every check passes. Close the GUI/serial monitor first: one app per COM port.
"""
import argparse
import sys
import time
from dataclasses import dataclass, field
from app.common import COMMANDS


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ''
    ms: float = None


@dataclass
class Session:
    transport: object
    buffer: bytearray = field(default_factory=bytearray)
    extra: list = field(default_factory=list)

    def line(self, timeout):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            b = self.transport.read(1)
            if not b:
                continue
            if b == b'\n':
                raw = bytes(self.buffer); self.buffer.clear()
                return raw.decode('ascii', 'replace').rstrip('\r')
            self.buffer.extend(b)
            if len(self.buffer) > 256:
                raw = bytes(self.buffer); self.buffer.clear()
                return raw.decode('ascii', 'replace') + ' <không có LF>'
        return None

    def send(self, data, expected, timeout=1.0, pieces=None):
        """Write data (optionally in pieces) and wait for the exact expected reply."""
        for n, chunk in enumerate(pieces or [data]):
            if n:
                time.sleep(0.05)            # second piece arrives later, like a slow UART
            self.transport.write(chunk)
        start = time.perf_counter()         # latency counted from the last byte written
        others = []
        while True:
            left = timeout - (time.perf_counter() - start)
            got = self.line(max(left, 0)) if left > 0 else None
            if got is None:
                detail = f'không nhận được {expected!r} trong {timeout:.1f} s'
                return False, detail + (f'; dòng khác: {others}' if others else ''), None
            if got == expected:
                ms = (time.perf_counter() - start) * 1000
                if others:
                    return False, f'có dòng lạ trước trả lời: {others}', ms
                return True, '', ms
            others.append(got)
            if len(others) >= 3:
                return False, f'trả lời sai: {others}', None


def run(transport, observe=False, ask=input, ready_timeout=5.0):
    s = Session(transport); checks = []
    start = time.perf_counter(); ready = s.line(ready_timeout)
    boot_lines = []
    while ready is not None and ready != 'READY,1' and time.perf_counter() - start < ready_timeout:
        boot_lines.append(ready); ready = s.line(ready_timeout - (time.perf_counter() - start))
    if ready == 'READY,1':
        checks.append(Check('Gửi READY,1 khi mở cổng', not boot_lines,
                            f'có dòng khác trước READY: {boot_lines}' if boot_lines else '',
                            (time.perf_counter() - start) * 1000))
    else:
        checks.append(Check('Gửi READY,1 khi mở cổng', False,
                            f'không thấy READY,1 trong {ready_timeout:.0f} s (nhận: {boot_lines}). Board không tự reset khi '
                            'mở cổng (vd. STM32 USB CDC) phải gửi READY khi DTR bật; kiểm tra baud 115200.'))
        return checks
    ident = 0

    def nid():
        nonlocal ident
        ident += 1
        return ident

    expected_state = {'light': False, 'fan': False}
    for action in COMMANDS:
        i = nid(); ok, detail, ms = s.send(f'CMD,{i},{action}\n'.encode(), f'ACK,{i},{action}')
        if ok and observe:
            device, value = action.split('_'); expected_state[device.lower()] = value == 'ON'
            want = f"đèn {'BẬT' if expected_state['light'] else 'TẮT'}, quạt {'BẬT' if expected_state['fan'] else 'TẮT'}"
            if ask(f'  Quan sát: {want}? [Enter = đúng, n = sai] ').strip().lower() == 'n':
                ok, detail = False, f'ACK đúng nhưng thiết bị không ở trạng thái: {want}'
        checks.append(Check(f'{action} → ACK đúng id', ok, detail, ms))
    i = nid(); j = nid()
    ok1, d1, _ = s.send(f'CMD,{i},LIGHT_ON\n'.encode(), f'ACK,{i},LIGHT_ON')
    ok2, d2, ms = s.send(f'CMD,{j},LIGHT_ON\n'.encode(), f'ACK,{j},LIGHT_ON')
    checks.append(Check('Gửi LIGHT_ON 2 lần (đặt trạng thái, không đảo)', ok1 and ok2, d1 or d2, ms))
    i = nid(); ok, d, ms = s.send(f'CMD,{i},FAN_OFF\r\n'.encode(), f'ACK,{i},FAN_OFF')
    checks.append(Check('Chấp nhận CRLF', ok, d, ms))
    i = nid(); ok, d, ms = s.send(b'', f'ACK,{i},LIGHT_OFF', pieces=[f'CMD,{i},LIG'.encode(), b'HT_OFF\n'])
    checks.append(Check('Lệnh tới thành 2 mảnh', ok, d, ms))
    i = nid(); ok, d, ms = s.send(f'CMD,{i},TOGGLE\n'.encode(), f'ERR,{i},UNKNOWN_COMMAND')
    checks.append(Check('Lệnh lạ → ERR,id,UNKNOWN_COMMAND', ok, d, ms))
    for name, packet in [('id không phải số', b'CMD,abc,FAN_ON\n'), ('id = 0', b'CMD,0,FAN_ON\n'),
                         ('id quá lớn', b'CMD,2147483648,FAN_ON\n'), ('dòng rác', b'HELLO\n'),
                         ('dòng rỗng', b'\n'), ('thừa trường', b'CMD,9,FAN_ON,1\n')]:
        ok, d, ms = s.send(packet, 'ERR,0,BAD_FORMAT')
        checks.append(Check(f'{name} → ERR,0,BAD_FORMAT', ok, d, ms))
    ok, d, ms = s.send(b'X' * 70 + b'\n', 'ERR,0,BAD_FORMAT')
    checks.append(Check('Dòng > 64 byte → ERR,0,BAD_FORMAT', ok, d, ms))
    i = nid(); ok, d, ms = s.send(f'CMD,{i},FAN_ON\n'.encode(), f'ACK,{i},FAN_ON')
    checks.append(Check('Hoạt động lại bình thường sau dòng quá dài', ok, d, ms))
    ok, d, ms = s.send(b'CMD,2147483647,FAN_OFF\n', 'ACK,2147483647,FAN_OFF')
    checks.append(Check('id lớn nhất 2147483647', ok, d, ms))
    stray = s.line(0.5)
    checks.append(Check('Không tự gửi thêm dòng (log) trên kênh giao thức', stray is None,
                        f'nhận thêm: {stray!r}' if stray else ''))
    i = nid(); s.send(f'CMD,{i},LIGHT_OFF\n'.encode(), f'ACK,{i},LIGHT_OFF')   # leave outputs off
    return checks


def report(checks, out=print):
    width = max(len(c.name) for c in checks)
    for c in checks:
        mark = 'PASS' if c.ok else 'FAIL'
        ms = f'{c.ms:7.1f} ms' if c.ms is not None else ' ' * 10
        out(f'{mark}  {c.name.ljust(width)}  {ms}  {c.detail}')
    passed = sum(c.ok for c in checks)
    lat = sorted(c.ms for c in checks if c.ok and c.ms is not None and 'READY' not in c.name)
    out(f'\n{passed}/{len(checks)} mục đạt.' + (f' Trễ trả lời: median {lat[len(lat)//2]:.1f} ms, '
                                                f'lớn nhất {lat[-1]:.1f} ms.' if lat else ''))
    return passed == len(checks)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--port', required=True, help='COM port, or "fake" to self-check with the virtual firmware')
    p.add_argument('--observe', action='store_true', help='Ask to confirm LED/fan state after each command')
    a = p.parse_args()
    if a.port.lower() == 'fake':
        from app.fake_device import FakeTransport
        transport = FakeTransport()
    else:
        import serial
        transport = serial.Serial(a.port, 115200, timeout=0.05, write_timeout=1)
    try:
        ok = report(run(transport, a.observe))
    finally:
        transport.close()
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
