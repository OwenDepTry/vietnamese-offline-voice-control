# Giao thức serial (v0.1, chờ hai đứa chốt)

Bản này là đề xuất. Những điểm cần thống nhất và cách kiểm tra firmware nằm trong `docs/INTEGRATION.md`. Muốn xem cách trả lời mẫu thì đọc `app/fake_device.py`, kiểm tra firmware thật thì chạy `python -m app.conformance --port COMx`.

## Cấu hình chung

115200 baud, 8N1, ký tự ASCII. Mỗi dòng kết thúc bằng LF (`\n`), nếu nhận CRLF thì bỏ CR. Mỗi dòng tối đa 64 byte tính cả LF. Không in log hay debug lên cổng này.

## Lệnh từ máy tính

```
CMD,<id>,<action>
```

- `id`: số nguyên từ 1 đến 2147483647
- `action`: `LIGHT_ON`, `LIGHT_OFF`, `FAN_ON`, `FAN_OFF`

Ví dụ: `CMD,1,LIGHT_ON`

## Board trả lời

```
ACK,<id>,<action>
ERR,<id>,<code>
```

Mã lỗi: `BAD_FORMAT`, `UNKNOWN_COMMAND`, `HARDWARE_ERROR`. Nếu không đọc được id thì trả id = 0. Dòng dài quá thì bỏ tới LF rồi trả `ERR,0,BAD_FORMAT`. Lệnh sai thì không được đổi trạng thái đầu ra.

ACK chỉ có nghĩa là firmware đã đặt chân ra, chưa chứng minh quạt quay thật. Muốn chắc thì phải có cảm biến hoặc nhìn bằng mắt.

## Trạng thái và lỗi

- Lúc khởi động mọi đầu ra đều tắt. Sẵn sàng thì board gửi `READY,1`.
- App chờ READY tối đa 5 giây sau khi mở cổng. Không gửi lại lệnh cũ của lần kết nối trước.
- Mỗi lúc chỉ có một lệnh đang chờ trả lời, thời gian chờ ACK là 1 giây (có thể chỉnh sau khi đo).
- Hết thời gian chờ thì báo "chưa xác nhận", không tự gửi lại.
- ON/OFF là đặt trạng thái, không có TOGGLE, để lỡ gửi lại thì cũng không bị đảo trạng thái.
- unknown và silence không gửi lệnh gì.
- Mất kết nối thì app báo lỗi và dừng gửi. Board giữ nguyên trạng thái nếu không bị reset (đây không phải watchdog).
- Mỗi lần bấm nói chỉ gửi tối đa một lệnh.
