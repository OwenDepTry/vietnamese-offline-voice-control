# Firmware — thành viên ĐTVT phụ trách

Chưa chốt board nên chưa tạo mã GPIO hoặc cấu hình build. Sau EE-01, thêm src/, cấu hình công cụ build và hướng dẫn nạp đúng board.

Tách parser serial, điều khiển đầu ra và trạng thái. Thực hiện docs/PROTOCOL.md. Không nối quạt trực tiếp vào GPIO; chọn driver theo dòng tải và mạch bảo vệ phù hợp. MVP dùng điện áp thấp, không điều khiển điện lưới.

Bản tham chiếu hành vi: `app/fake_device.py` (lớp `FakeDevice`) cài đặt đúng PROTOCOL.md bằng Python và có test trong `tests/test_tools.py`. Firmware thật nên trả lời giống hệt cho cùng chuỗi byte vào. Board không tự reset khi mở cổng (vd. STM32 USB CDC) cần gửi lại `READY,1` khi máy tính mở cổng (DTR bật), nhưng không gửi READY lặp lại trong lúc đang xử lý lệnh.
