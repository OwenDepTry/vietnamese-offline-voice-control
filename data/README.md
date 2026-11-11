# Dữ liệu

Không commit audio cá nhân. Chỉ thu khi người tham gia đồng ý; lưu ánh xạ danh tính ngoài repo. Đặt file trong raw/, dữ liệu xử lý trong processed/.

Pilot đề xuất: 10 người × 4 lệnh × 15 lượt = 600 mẫu lệnh, thu nhiều phiên; thêm silence, tiếng ồn và lời nói ngoài tập. Đây chỉ là điểm bắt đầu, chưa đủ để khẳng định tổng quát hóa. Mở rộng số người sau pilot.

Chia theo speaker_id; ví dụ 6/2/2 người cho train/validation/test ở pilot. Test nhỏ chỉ là kết quả sơ bộ. Không dùng test để chọn mô hình hoặc ngưỡng. Augmentation chỉ áp dụng train và phải giữ nguồn gốc mẫu.

Dùng manifest.example.csv làm mẫu cấu trúc (hiện chỉ có header). Micro laptop/USB ở MVP; ghi lại thiết bị thu để phân tích khác biệt miền dữ liệu.
