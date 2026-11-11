import json
from pathlib import Path
from datetime import datetime, timezone
from time import perf_counter
from app.common import COMMANDS

class Controller:
    def __init__(self,backend,predictor=None,log='results/events.jsonl'):
        self.backend=backend;self.predictor=predictor;self.log=Path(log) if log else None
    def _save(self,event):
        event['utc']=datetime.now(timezone.utc).isoformat()
        if self.log:
            self.log.parent.mkdir(parents=True,exist_ok=True)
            with self.log.open('a',encoding='utf-8') as f: f.write(json.dumps(event,ensure_ascii=False)+'\n')
        return event
    def manual(self,action):
        if action not in COMMANDS: raise ValueError('Unknown action')
        return self._dispatch(action,{'source':'manual'})
    def _dispatch(self,action,event):
        start=perf_counter()
        try:
            event['result']=self.backend.send(action)
        except Exception as exc:
            event['error']=str(exc);self._save(event);raise
        event['transport_ms']=(perf_counter()-start)*1000
        return self._save(event)
    def voice(self,audio):
        if self.predictor is None: raise ValueError('Load a trained model first')
        start=perf_counter();prediction=self.predictor.predict(audio)
        event={'source':'voice','prediction':prediction.to_dict()}
        if prediction.accepted:
            try: event['result']=self.backend.send(prediction.label)
            except Exception as exc:
                event['error']=str(exc);self._save(event);raise
        else: event['result']={'action':None,'reason':'rejected_noncommand'}
        event['post_record_ms']=(perf_counter()-start)*1000
        return self._save(event)
