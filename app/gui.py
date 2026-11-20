"""Tkinter desktop UI. Work happens off the UI thread; one request at a time.

  python -m app.gui                                   # simulation, buttons only
  python -m app.gui --model models/baseline.joblib    # + voice (Space = record 2 s)
  python -m app.gui --model models/baseline.joblib --port fake   # virtual firmware
  python -m app.gui --model models/baseline.joblib --port COM5   # real board
"""
import argparse
import json
import queue
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import ttk
from app.common import COMMANDS
from app.controller import Controller
from app.serial_client import open_backend, device_state
from app.recorder import record, review

TRIAL_LABELS = list(COMMANDS) + ['unknown', 'silence']
HISTORY_MAX = 50


def default_model():
    """When packaged as an .exe, pick up models/baseline.joblib next to it."""
    if getattr(sys, 'frozen', False):
        for base in (Path.cwd(), Path(sys.executable).parent):
            candidate = base / 'models' / 'baseline.joblib'
            if candidate.is_file():
                return str(candidate)
    return None


def describe_event(ok, event):
    """One history line + one big headline for the UI."""
    stamp = datetime.now().strftime('%H:%M:%S')
    if not ok:
        return f'{stamp}  LỖI  {event}', 'Lỗi: ' + str(event)
    if 'error' in event:
        return f"{stamp}  LỖI  {event['error']}", 'Lỗi: ' + event['error']
    result = event.get('result') or {}
    if event.get('source') == 'reconnect':
        return f'{stamp}  kết nối lại OK', 'Đã kết nối lại thiết bị'
    if event.get('source') == 'voice':
        p = event['prediction']
        heard = COMMANDS.get(p['label'], p['label'])
        if p['accepted']:
            tail = 'ACK' if result.get('ack') else 'mô phỏng' if result.get('mode') == 'simulation' else 'đã gửi'
            headline = f"Nghe: «{heard}»  {p['score']*100:.0f}%  → {tail}"
        else:
            if p['raw_label'] in COMMANDS:
                headline = (f"Chưa chắc chắn: gần nhất «{COMMANDS[p['raw_label']]}» {p['score']*100:.0f}% "
                            f"— không thực hiện")
            else:
                headline = f"Không phải lệnh ({p['label']} {p['score']*100:.0f}%) — không thực hiện"
        line = f"{stamp}  giọng  {p['label']:<9} {p['score']:.2f}  {event.get('post_record_ms', 0):.0f} ms"
    else:
        headline = f"Lệnh tay: «{COMMANDS[result.get('action')]}» → {'ACK' if result.get('ack') else 'mô phỏng'}"
        line = f"{stamp}  tay    {result.get('action')}  {event.get('transport_ms', 0):.1f} ms"
    if event.get('audio_flags'):
        headline += '  ⚠ ' + ', '.join(event['audio_flags'])
    return line, headline


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--model'); parser.add_argument('--device', type=int)
    parser.add_argument('--port', help='COM port, or "fake" for the built-in virtual firmware')
    parser.add_argument('--fault', default='none', help='Fault for --port fake: none/timeout/error/reset/mismatch')
    parser.add_argument('--log', default='results/events.jsonl')
    parser.add_argument('--trials', default='results/measurements.csv', help='Where trial mode appends rows')
    a = parser.parse_args()
    model_path = a.model or default_model()
    predictor = None
    if model_path:
        from ml.predict import Predictor
        predictor = Predictor(model_path)
    backend = open_backend(a.port, a.fault)
    controller = Controller(backend, predictor, a.log)

    root = tk.Tk(); root.title('Vietnamese Offline Voice Control'); root.geometry('780x720')
    q = queue.Queue(); busy = False; closing = False
    if not a.port:
        mode = 'MÔ PHỎNG — không có thiết bị thật'
    elif a.port.lower() == 'fake':
        mode = f'FIRMWARE ẢO (fault={a.fault}) — giao thức serial thật, thiết bị giả'
    else:
        mode = f'SERIAL {a.port} — ACK chưa phải xác nhận vật lý'
    ttk.Label(root, text=mode, font=('Arial', 13, 'bold')).pack(pady=(14, 4))
    status = tk.StringVar(value='Sẵn sàng' + ('' if predictor else ' — chưa nạp model, chỉ dùng nút bấm'))
    ttk.Label(root, textvariable=status).pack()
    state = tk.StringVar(value='Đèn: ? | Quạt: ?')
    ttk.Label(root, textvariable=state, font=('Arial', 18)).pack(pady=8)
    headline = tk.StringVar(value='Nhấn Space hoặc nút bên dưới rồi nói một lệnh' if predictor else '')
    ttk.Label(root, textvariable=headline, font=('Arial', 14), foreground='#1f4e79').pack(pady=4)

    panel = ttk.Frame(root); panel.pack(pady=4); buttons = []

    def show_state():
        s = device_state(backend)
        if s is not None:
            state.set(f"Đèn: {'BẬT' if s['light'] else 'TẮT'} | Quạt: {'BẬT' if s['fan'] else 'TẮT'}")

    # --- trial mode -------------------------------------------------------------
    trial = ttk.LabelFrame(root, text='Chế độ thử nghiệm (ghi vào measurements.csv)')
    trial.pack(fill='x', padx=15, pady=6)
    trial_on = tk.BooleanVar(value=False)
    ttk.Checkbutton(trial, text='Ghi lượt thử', variable=trial_on, takefocus=False).grid(row=0, column=0, padx=6, pady=4)
    ttk.Label(trial, text='Người nói').grid(row=0, column=1)
    speaker = tk.StringVar(value='p01'); ttk.Entry(trial, textvariable=speaker, width=7).grid(row=0, column=2, padx=4)
    ttk.Label(trial, text='Điều kiện').grid(row=0, column=3)
    condition = tk.StringVar(value='quiet'); ttk.Entry(trial, textvariable=condition, width=10).grid(row=0, column=4, padx=4)
    ttk.Label(trial, text='Định nói').grid(row=0, column=5)
    intended = tk.StringVar(value=TRIAL_LABELS[0])
    ttk.Combobox(trial, textvariable=intended, values=TRIAL_LABELS, state='readonly', width=10).grid(row=0, column=6, padx=4)
    phys_label = tk.StringVar(value='')

    def mark_physical(value):
        from app.trials import set_last_physical
        try:
            row = set_last_physical(a.trials, value)
            phys_label.set(f"Lượt {row['trial_id']}: vật lý = {value}")
        except Exception as exc:
            phys_label.set('Không ghi được: ' + str(exc))
    ttk.Label(trial, text='Thiết bị chạy thật?').grid(row=1, column=0, padx=6, pady=4, sticky='e')
    ttk.Button(trial, text='Có', width=5, takefocus=False, command=lambda: mark_physical('yes')).grid(row=1, column=1)
    ttk.Button(trial, text='Không', width=7, takefocus=False, command=lambda: mark_physical('no')).grid(row=1, column=2)
    ttk.Label(trial, textvariable=phys_label).grid(row=1, column=3, columnspan=4, sticky='w', padx=6)

    # --- history + details ------------------------------------------------------
    ttk.Label(root, text='Lịch sử').pack(anchor='w', padx=15)
    history = tk.Listbox(root, height=9, font=('Consolas', 10), takefocus=False)
    history.pack(fill='x', padx=15)
    output = tk.Text(root, height=8, wrap='word', takefocus=False)

    def submit(action=None):
        nonlocal busy
        if busy or closing: return
        if action is None and predictor is None: return
        busy = True; status.set('Đang thu 2 giây… nói ngay!' if action is None else 'Đang gửi…')
        for b in buttons: b.configure(state='disabled')
        want_trial = action is None and trial_on.get()
        trial_info = (intended.get(), speaker.get().strip(), condition.get().strip())

        def work():
            try:
                if action:
                    event = controller.manual(action)
                else:
                    audio = record(device=a.device)
                    flags = [f for f in review(audio, 'LIGHT_ON') if f in ('too_quiet', 'clipped', 'cut_end', 'no_speech')]
                    event = controller.voice(audio)
                    if flags: event['audio_flags'] = flags
                if want_trial:
                    from app.trials import append_trial
                    event['trial'] = append_trial(a.trials, event, *trial_info)
                q.put((True, event))
            except Exception as exc:
                if want_trial:
                    try:
                        from app.trials import append_trial
                        append_trial(a.trials, {'error': str(exc)}, *trial_info)
                    except Exception:
                        pass
                q.put((False, str(exc)))
        threading.Thread(target=work, daemon=True).start()

    for i, (code, text) in enumerate(COMMANDS.items()):
        b = ttk.Button(panel, text=text, takefocus=False, command=lambda c=code: submit(c))
        b.grid(row=i // 2, column=i % 2, padx=8, pady=5); buttons.append(b)
    voice = ttk.Button(root, text='🎤 Nói (Space) — 2 giây', takefocus=False, command=submit)
    voice.pack(pady=8, before=trial); buttons.append(voice)
    if not predictor: voice.configure(state='disabled')

    def reconnect():
        nonlocal backend, busy
        if busy or closing: return
        busy = True; status.set('Đang kết nối lại…')
        for b in buttons: b.configure(state='disabled')

        def work():
            nonlocal backend
            try:
                backend.close()
            except Exception:
                pass
            try:
                backend = open_backend(a.port, a.fault); controller.backend = backend
                q.put((True, {'source': 'reconnect'}))
            except Exception as exc:
                q.put((False, 'Kết nối lại thất bại: ' + str(exc)))
        threading.Thread(target=work, daemon=True).start()
    if a.port:
        rc = ttk.Button(root, text='Kết nối lại', takefocus=False, command=reconnect)
        rc.pack(before=trial); buttons.append(rc)
    output.pack(fill='both', expand=True, padx=15, pady=8)

    def on_space(event):
        # Typing in the trial fields must not trigger a recording.
        if event.widget.winfo_class() in ('TEntry', 'Entry', 'TCombobox'):
            return None
        submit(); return 'break'
    root.bind('<space>', on_space)

    def poll():
        nonlocal busy
        try:
            ok, event = q.get_nowait(); busy = False
            line, head = describe_event(ok, event)
            headline.set(head); history.insert(0, line)
            if history.size() > HISTORY_MAX: history.delete(HISTORY_MAX, 'end')
            status.set('Xong' if ok else 'Lỗi — với lỗi serial, bấm «Kết nối lại»')
            show_state()
            output.delete('1.0', 'end')
            output.insert('end', json.dumps(event, ensure_ascii=False, indent=2) if ok else event)
            if ok and event.get('trial'):
                phys_label.set(f"Đã ghi lượt {event['trial']['trial_id']} — bấm Có/Không nếu đang quan sát thiết bị")
            for b in buttons: b.configure(state='normal')
            if not predictor: voice.configure(state='disabled')
        except queue.Empty:
            pass
        if closing and not busy:
            backend.close(); root.destroy(); return
        root.after(80, poll)

    def close():
        nonlocal closing
        closing = True; status.set('Đang chờ thao tác hiện tại xong rồi đóng…')
    show_state()
    root.protocol('WM_DELETE_WINDOW', close); root.after(80, poll); root.focus_set(); root.mainloop()


if __name__ == '__main__': main()
