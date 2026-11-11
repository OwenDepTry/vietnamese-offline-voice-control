"""Single in-flight request; bounded reads; no automatic command retries."""
import time
from app.common import COMMANDS

class ProtocolError(RuntimeError): pass

class SerialClient:
    def __init__(self,port=None,transport=None,timeout=1.0,ready_timeout=5.0):
        if timeout<=0: raise ValueError('Timeout must be positive')
        if transport is None:
            import serial
            transport=serial.Serial(port,115200,timeout=0.05,write_timeout=timeout)
        self.transport=transport;self.timeout=timeout;self.request_id=0;self.ready=False
        self.buffer=bytearray();self.dropping=False
        try: self.wait_ready(ready_timeout)
        except Exception:
            self.close();raise
    def _line(self,deadline):
        # read(1) retains partial frames across read timeouts and caps line length.
        while time.monotonic()<deadline:
            b=self.transport.read(1)
            if not b: continue
            if self.dropping:
                if b==b'\n': self.dropping=False
                continue
            self.buffer.extend(b)
            if len(self.buffer)>64:
                self.buffer.clear();self.dropping=b!=b'\n';continue
            if b==b'\n':
                raw=bytes(self.buffer);self.buffer.clear()
                try: return raw.decode('ascii').strip()
                except UnicodeDecodeError: continue
        raise TimeoutError('Device response timeout; physical state is unconfirmed')
    def wait_ready(self,seconds):
        deadline=time.monotonic()+seconds
        while time.monotonic()<deadline:
            if self._line(deadline)=='READY,1':
                self.ready=True;return
        raise TimeoutError('READY,1 not received')
    def send(self,action):
        if action not in COMMANDS: raise ValueError('Unknown action')
        if not self.ready: raise ProtocolError('Reconnect before sending another command')
        self.request_id=self.request_id%2147483647+1
        ident=str(self.request_id);packet=f'CMD,{ident},{action}\n'.encode('ascii')
        try:
            if self.transport.write(packet)!=len(packet): raise ProtocolError('Incomplete write')
            deadline=time.monotonic()+self.timeout
            while True:
                line=self._line(deadline)
                if line=='READY,1': raise ProtocolError('Device reset during request; reconnect')
                parts=line.split(',')
                if len(parts)!=3: continue
                if parts[0]=='ERR' and parts[1] in (ident,'0'):
                    raise ProtocolError('Device error: '+parts[2])
                if parts[0]=='ACK' and parts[1]==ident:
                    if parts[2]!=action: raise ProtocolError('ACK action mismatch')
                    return {'mode':'serial','action':action,'ack':True,'physical_confirmed':False}
        except Exception:
            self.ready=False
            raise
    def close(self):
        self.ready=False;self.transport.close()

class Simulator:
    def __init__(self): self.state={'light':False,'fan':False}
    def send(self,action):
        if action not in COMMANDS: raise ValueError('Unknown action')
        device,value=action.split('_')
        self.state[device.lower()]=value=='ON'
        return {'mode':'simulation','action':action,'state':dict(self.state),'physical_confirmed':False}
    def close(self): pass
