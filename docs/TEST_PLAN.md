# Kế hoạch kiểm thử

## Về chức năng

- Gõ lệnh nào thì đúng thiết bị đó bật/tắt, ACK trả về đúng id.
- Lệnh sai, dòng quá dài, hoặc nói unknown/silence thì thiết bị không đổi trạng thái.
- Mỗi lần bấm nói chỉ tạo ra tối đa một hành động.
- Lúc khởi động, khi timeout, khi rút/cắm lại USB hay reset board thì app phản ứng đúng như giao thức.
- Tắt Internet vẫn nhận lệnh và điều khiển được.

## Về đánh giá

Báo cáo phải ghi rõ: số mẫu, số người nói, micro dùng để thu, môi trường và khoảng cách.

Các số cần đo:
- Macro-F1 và confusion matrix, cố gắng đo trên người nói chưa có trong train.
- Tỉ lệ bỏ sót lệnh (nói lệnh nhưng model từ chối).
- Tỉ lệ kích hoạt nhầm (nói câu khác hoặc im lặng mà lại thành lệnh). Vì đang làm kiểu bấm để nói nên tính theo số lượt thử; nếu sau này nghe liên tục thì mới tính theo giờ.
- Độ trễ từ lúc thu xong tới lúc có ACK, ghi median và p95, kèm cấu hình laptop.
- Tỉ lệ thiết bị chạy đúng phải nhìn bằng mắt (hoặc cảm biến), không tính theo ACK.

Chỉ đặt mục tiêu con số sau khi có kết quả baseline và trước khi chấm test cuối. Ghi lại tất cả các lượt thử, kể cả lượt sai, vào `results/measurements.csv`. Cách đo chi tiết ở `docs/MEASUREMENTS.md`.
