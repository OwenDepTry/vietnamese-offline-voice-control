# Firmware — thành viên ĐTVT phụ trách

Chưa chốt board nên chưa tạo mã GPIO hoặc cấu hình build. Sau EE-01, thêm src/, cấu hình công cụ build và hướng dẫn nạp đúng board.

Tách parser serial, điều khiển đầu ra và trạng thái. Thực hiện docs/PROTOCOL.md. Không nối quạt trực tiếp vào GPIO; chọn driver theo dòng tải và mạch bảo vệ phù hợp. MVP dùng điện áp thấp, không điều khiển điện lưới.
