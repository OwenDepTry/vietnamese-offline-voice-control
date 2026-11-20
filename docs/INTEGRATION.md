# Ghép phần mềm với phần cứng

File này để hai đứa thống nhất phần giao tiếp. Bên máy tính đã chạy được với firmware ảo, giờ cần firmware thật trả lời giống như vậy.

## 1. Chốt giao thức (BOTH-01)

Cả hai đọc `docs/PROTOCOL.md` và notebook `notebooks/04_firmware_ao.ipynb` (có bảng gửi gì thì board trả gì), rồi tick từng dòng dưới đây. Muốn đổi chỗ nào thì sửa PROTOCOL.md và `app/fake_device.py` trong cùng một PR để hai bên luôn khớp nhau.

- [ ] Cấu hình: 115200 baud, 8N1, ASCII, kết thúc bằng LF, có CR thì bỏ.
- [ ] Độ dài dòng: tối đa 64 byte tính cả LF. Dài hơn thì bỏ tới LF và trả `ERR,0,BAD_FORMAT`.
- [ ] Lệnh: `CMD,<id>,<action>`, id từ 1 tới 2147483647, action là một trong LIGHT_ON, LIGHT_OFF, FAN_ON, FAN_OFF.
- [ ] Trả lời: `ACK,<id>,<action>` hoặc `ERR,<id>,<code>`. Không đọc được id thì để id = 0.
- [ ] Mã lỗi: `BAD_FORMAT`, `UNKNOWN_COMMAND`, `HARDWARE_ERROR`. Khi nào thì trả HARDWARE_ERROR thì bên ĐTVT quyết định.
- [ ] Dòng rỗng: hiện đang trả `ERR,0,BAD_FORMAT` (công cụ kiểm tra cũng yêu cầu vậy). Nếu muốn bỏ qua dòng rỗng thì sửa luôn fake_device và conformance.
- [ ] Khởi động: đầu ra tắt, sẵn sàng thì gửi `READY,1`. Board không tự reset khi mở cổng (như STM32 qua USB CDC) thì gửi lại `READY,1` khi máy tính mở cổng (DTR bật), nhưng không gửi lại khi đang xử lý lệnh.
- [ ] Thời gian: app chờ READY 5 giây, chờ ACK 1 giây. Firmware nên trả lời dưới 50 ms.
- [ ] ON/OFF là đặt trạng thái: gửi hai lần cũng như một lần, không có TOGGLE.
- [ ] Không in log lên cổng serial này. Cần debug thì dùng LED hoặc một cổng UART khác.
- [ ] Mất kết nối: board giữ nguyên trạng thái, app báo lỗi và người dùng bấm "Kết nối lại".

Chốt xong thì đổi tiêu đề PROTOCOL.md thành v1.0, ghi ngày, và merge PR khi cả hai đã duyệt.

## 2. Gợi ý cách viết firmware (EE-03, EE-04)

```
setup():
    đặt chân LED và quạt là OUTPUT, mức LOW (tắt) trước khi làm gì khác
    Serial.begin(115200); gửi "READY,1\n"

loop():
    đọc từng byte vào bộ đệm 64 byte
    gặp '\n'  -> xử lý dòng (bỏ '\r' ở cuối nếu có), xóa bộ đệm
    bộ đệm đầy mà chưa gặp '\n' -> trả ERR,0,BAD_FORMAT, bỏ hết tới '\n'
    (STM32 USB CDC) DTR vừa bật -> gửi "READY,1\n"

xử lý dòng:
    tách theo dấu phẩy, không đủ 3 phần hoặc phần đầu không phải "CMD" -> ERR,0,BAD_FORMAT
    id không phải số, có số 0 ở đầu, hoặc ngoài khoảng 1..2147483647 -> ERR,0,BAD_FORMAT
    action lạ -> ERR,<id>,UNKNOWN_COMMAND
    hợp lệ -> digitalWrite(...) rồi trả ACK,<id>,<action>
```

Bản chạy được bằng Python là lớp `FakeDevice` trong `app/fake_device.py`, khoảng 60 dòng, có thể đọc để so.

Về linh kiện (chi tiết hơn ở `docs/TASKS.md`, mục EE-01): Nano clone CH340 dễ nhất vì logic 5V và tự reset khi mở cổng. Nếu dùng STM32F411 có sẵn thì logic là 3,3V và phải xử lý READY như ở trên. Quạt 5V khoảng 0,1-0,2 A đi qua S8050/2N2222 (điện trở base 470 Ω tới 1 kΩ) hoặc AO3400, có diode 1N4007 mắc song song quạt, và điện trở kéo xuống 10k ở chân điều khiển.

## 3. Kiểm tra firmware

Đóng hết các chương trình đang dùng cổng COM (Serial Monitor của Arduino, GUI...) rồi chạy:

```powershell
python -m app.conformance --port COM5             # tự động, 19 mục
python -m app.conformance --port COM5 --observe   # hỏi thêm đèn/quạt có đúng không sau mỗi lệnh
```

Đạt khi in ra `19/19 mục đạt`. Dòng nào FAIL sẽ ghi rõ board đã trả về gì. Muốn thử công cụ khi chưa có board thì dùng `--port fake`.

Đạt rồi thì làm tiếp:

1. Gõ lệnh tay: `python -m app.main --mode serial --port COM5`, gõ `LIGHT_ON`, `FAN_ON`... (BOTH-02).
2. Nói lệnh điều khiển board: `python -m app.gui --model models/<model>.joblib --port COM5` (BOTH-04).
3. Đo theo `docs/MEASUREMENTS.md` mục 4.
4. Thử lỗi theo `docs/TEST_PLAN.md`: rút USB khi đang chạy, bấm reset, cắm nguồn lại. App phải báo lỗi rõ ràng và bấm "Kết nối lại" được.

## 4. Chia việc

| Bước | Đạt (CNTT) | Bạn ĐTVT |
|---|---|---|
| Chốt giao thức | Duyệt, sửa fake_device/conformance nếu đổi | Duyệt, quyết định khi nào dùng HARDWARE_ERROR |
| Firmware | Hỗ trợ đọc kết quả conformance | Viết, nạp, chạy conformance tới khi đạt 19/19 |
| Ghép | GUI, model, ghi lượt thử | Mạch, nguồn, quan sát thiết bị |
| Báo cáo | Phần phần mềm và kết quả nhận dạng | Phần phần cứng, firmware, ảnh mạch, số đo điện |
