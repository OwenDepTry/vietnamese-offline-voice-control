"""Tkinter desktop UI. Work happens off the UI thread; one request at a time."""
import argparse
import json
import queue
import threading
import tkinter as tk
from tkinter import ttk
from app.common import COMMANDS
from app.controller import Controller
from app.serial_client import Simulator, SerialClient
from app.recorder import record

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--model');parser.add_argument('--port');parser.add_argument('--device',type=int)
    a=parser.parse_args()
    predictor=None
    if a.model:
        from ml.predict import Predictor
        predictor=Predictor(a.model)
    backend=SerialClient(a.port) if a.port else Simulator()
    controller=Controller(backend,predictor)
    root=tk.Tk();root.title('Vietnamese Offline Voice Control');root.geometry('720x520')
    q=queue.Queue();busy=False;closing=False
    mode='SERIAL — ACK is not physical confirmation' if a.port else 'SIMULATION — no physical device'
    ttk.Label(root,text=mode,font=('Arial',14,'bold')).pack(pady=16)
    status=tk.StringVar(value='Ready');ttk.Label(root,textvariable=status).pack()
    state=tk.StringVar(value='Light: unknown | Fan: unknown' if a.port else 'Light: OFF | Fan: OFF')
    ttk.Label(root,textvariable=state,font=('Arial',18)).pack(pady=15)
    panel=ttk.Frame(root);panel.pack();buttons=[]
    output=tk.Text(root,height=12,wrap='word')
    def submit(action=None):
        nonlocal busy
        if busy or closing:return
        busy=True;status.set('Recording 2 seconds...' if action is None else 'Sending...')
        for b in buttons:b.configure(state='disabled')
        def work():
            try:
                event=controller.manual(action) if action else controller.voice(record(device=a.device))
                q.put((True,event))
            except Exception as exc:q.put((False,str(exc)))
        threading.Thread(target=work,daemon=True).start()
    for i,(code,text) in enumerate(COMMANDS.items()):
        b=ttk.Button(panel,text=text,command=lambda c=code:submit(c));b.grid(row=i//2,column=i%2,padx=8,pady=6);buttons.append(b)
    voice=ttk.Button(root,text='Record & recognize (2s)',command=submit);voice.pack(pady=12);buttons.append(voice)
    if not predictor: voice.configure(state='disabled')
    output.pack(fill='both',expand=True,padx=15,pady=10)
    def poll():
        nonlocal busy
        try:
            ok,event=q.get_nowait();busy=False
            status.set('Done' if ok else 'Error — reconnect after serial errors')
            if ok and 'state' in event.get('result',{}):
                s=event['result']['state'];state.set(f"Light: {'ON' if s['light'] else 'OFF'} | Fan: {'ON' if s['fan'] else 'OFF'}")
            output.delete('1.0','end');output.insert('end',json.dumps(event,ensure_ascii=False,indent=2) if ok else event)
            for b in buttons:b.configure(state='normal')
            if not predictor:voice.configure(state='disabled')
        except queue.Empty: pass
        if closing and not busy:
            backend.close();root.destroy();return
        root.after(80,poll)
    def close():
        nonlocal closing
        closing=True;status.set('Waiting for current operation before closing...')
    root.protocol('WM_DELETE_WINDOW',close);root.after(80,poll);root.mainloop()
if __name__=='__main__': main()
