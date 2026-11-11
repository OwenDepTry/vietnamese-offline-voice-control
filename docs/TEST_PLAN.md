# Kiểm thử và tiêu chí hoàn thành

## Chức năng
- Mỗi lệnh gõ tay đúng điều khiển đúng đầu ra, ACK đúng id.
- Lệnh sai, dòng quá dài hoặc unknown/silence không làm đổi đầu ra.
- Một lần nhấn để nói chỉ tạo tối đa một hành động.
- Khởi động, timeout, rút/cắm USB và reset có hành vi theo giao thức.
- Tắt Internet vẫn nhận diện và điều khiển được.

## Đánh giá
Báo cáo số mẫu, người nói, thiết bị thu, môi trường và khoảng cách. Đo macro-F1 và confusion matrix trên người nói chưa thấy; tỷ lệ từ chối lệnh đúng; kích hoạt nhầm trên lời ngoài tập. Với MVP nhấn để nói, đo kích hoạt nhầm/lượt thử; khi mở rộng nghe liên tục mới đo kích hoạt nhầm/giờ.

Độ trễ: từ lúc kết thúc thu âm đến ACK; báo cáo median và p95, kèm cấu hình laptop. Tỷ lệ thành công end-to-end phải quan sát đầu ra vật lý, không chỉ dựa vào ACK.

Chốt mục tiêu số sau baseline pilot và trước test cuối; hiện chưa có số liệu hay cam kết độ chính xác. Lưu tất cả lần thử, kể cả thất bại, trong results/measurements.csv.
