# Firmware

Phần này Thái (ĐTVT) phụ trách. Chưa chốt board nên chưa có code. Sau khi chọn board (EE-01) thì thêm `src/`, cấu hình build và hướng dẫn nạp.

Nên tách 3 phần: đọc và phân tích lệnh serial, điều khiển chân ra, lưu trạng thái. Làm theo `docs/PROTOCOL.md`. Không nối quạt thẳng vào chân GPIO mà phải qua transistor/MOSFET, có diode bảo vệ. MVP chỉ dùng điện áp thấp, không đụng điện lưới.

Muốn biết firmware phải trả lời thế nào thì xem `app/fake_device.py` (lớp `FakeDevice`), đây là bản viết bằng Python đã có test. Viết xong thì kiểm tra bằng `python -m app.conformance --port COMx`.

Nếu dùng board không tự reset khi mở cổng (ví dụ STM32 qua USB CDC) thì phải gửi lại `READY,1` mỗi khi máy tính mở cổng (DTR bật), nhưng đừng gửi READY trong lúc đang xử lý lệnh.
