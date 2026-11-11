import argparse
import json
from app.common import COMMANDS
from app.controller import Controller
from app.serial_client import Simulator, SerialClient
from app.recorder import record

def main():
    p=argparse.ArgumentParser(description='Offline voice controller; simulation is default')
    p.add_argument('--mode',choices=['simulation','serial'],default='simulation')
    p.add_argument('--port');p.add_argument('--model');p.add_argument('--device',type=int)
    p.add_argument('--log',default='results/events.jsonl');a=p.parse_args()
    if a.mode=='serial' and not a.port: p.error('--port is required in serial mode')
    predictor=None
    if a.model:
        from ml.predict import Predictor
        predictor=Predictor(a.model)
    backend=Simulator() if a.mode=='simulation' else SerialClient(a.port)
    controller=Controller(backend,predictor,a.log)
    print('MODE:',a.mode,'| commands:',', '.join(COMMANDS))
    print('Type a command, voice (record 2s), or quit. Simulation does not control physical hardware.')
    try:
        while True:
            cmd=input('> ').strip()
            if cmd.lower() in ['quit','exit']: break
            try:
                if cmd.lower()=='voice':
                    if not predictor: raise ValueError('Restart with --model models/baseline.joblib')
                    print('Recording now...');result=controller.voice(record(device=a.device))
                else: result=controller.manual(cmd.upper())
                print(json.dumps(result,ensure_ascii=False,indent=2))
            except Exception as exc: print('ERROR:',exc)
    except (KeyboardInterrupt,EOFError): pass
    finally: backend.close()
if __name__=='__main__': main()
