# Giao thức serial v0.1 — đề xuất để hai người chốt

115200 baud, 8N1; ASCII; mỗi thông điệp kết thúc bằng LF. Tối đa 64 byte mỗi dòng kể cả LF; bỏ CR nếu nhận CRLF. Không đưa log tự do vào kênh giao thức.

## Request
CMD,<id>,<action>\n

id: số nguyên 1..2147483647. action: LIGHT_ON, LIGHT_OFF, FAN_ON, FAN_OFF. Ví dụ CMD,1,LIGHT_ON.

## Response
ACK,<id>,<action>\n
ERR,<id>,<code>\n

Code: BAD_FORMAT, UNKNOWN_COMMAND, HARDWARE_ERROR. Dùng id=0 nếu không đọc được id request. Dòng quá dài: bỏ đến LF, trả ERR,0,BAD_FORMAT. Lệnh sai không thay đổi đầu ra.
ACK xác nhận firmware đã đặt đầu ra, chưa chứng minh quạt thật sự quay. Cần cảm biến nếu muốn xác nhận vật lý.

## Trạng thái và lỗi
- Đầu ra OFF khi boot; firmware gửi READY,1 khi sẵn sàng.
- App chờ READY tối đa 5 giây sau kết nối, có thể kết nối lại khi timeout; không gửi lệnh tồn từ phiên trước.
- Một request đang chờ tại một thời điểm; timeout ACK ban đầu 1 giây (điều chỉnh theo đo đạc).
- Timeout: hiển thị chưa xác nhận, không tự động lặp lệnh ở MVP.
- ON/OFF là đặt trạng thái, không dùng TOGGLE để tránh đảo trạng thái khi gửi lại.
- unknown/silence không gửi CMD.
- Mất kết nối: app báo lỗi và dừng gửi; bản MVP giữ đầu ra hiện tại nếu MCU không reset. Đây không phải cơ chế watchdog.
- Nhấn để nói: tối đa một hành động cho mỗi lượt ghi âm.
