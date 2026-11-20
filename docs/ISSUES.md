# Việc còn lại (để tạo issue trên GitHub)

Có thể tạo tay trên GitHub hoặc chạy `scripts/create_issues.ps1` (cần cài GitHub CLI và `gh auth login` trước). Chỉ chạy script một lần, chạy lại sẽ bị trùng issue.

| # | Tiêu đề | Nhãn | Nội dung |
|---|---|---|---|
| 1 | IT-01: Bỏ đoạn im lặng đầu file và tắt lọc ồn micro | it, data | File nào cũng bắt đầu bằng khoảng 0,1-0,18 s toàn số 0, và tiếng nền trong file silence giảm khoảng 14 dB sau giây 1,3 (có thể do Audio enhancements của Windows). Sửa recorder hoặc ghi vào phần hạn chế; nếu sửa thì thu lại s01. |
| 2 | BOTH-03: Thu p01/s02 và p01/s03 | it, data | Mỗi phiên 6 nhãn x 5 mẫu, thu lúc khác hoặc chỗ khác trong phòng, câu unknown khác với s01. Thu xong chạy ml.check_data. |
| 3 | IT-05/06: Kết quả baseline đầu tiên | it | Notebook 02 để chọn cấu hình, notebook 03 để chấm test một lần. Đính kèm summary.md và confusion matrix. |
| 4 | BOTH-03: Thu giọng p02 từ xa | both, data | Hỏi ý người thu trước, p02 thu trên máy của mình rồi gửi zip, gộp bằng ml.merge_manifest, đánh giá lại với --require-new-speaker. |
| 5 | IT-07: Đo độ trễ và chạy offline | it | Làm theo docs/MEASUREMENTS.md mục 1 và 2, ghi median/p95 vào báo cáo. |
| 6 | EE-01/02: Chọn linh kiện, điền BOM, vẽ sơ đồ nối dây | ee | hardware/BOM.csv và hardware/wiring.md. Đầu ra phải tắt khi khởi động. |
| 7 | EE-03/04: Firmware theo PROTOCOL.md | ee | Chạy python -m app.conformance --port COMx tới khi đạt hết. |
| 8 | BOTH-01: Duyệt PROTOCOL.md lên v1.0 | both | Checklist trong docs/INTEGRATION.md, cả hai duyệt trong PR. |
| 9 | BOTH-04: Ghép giọng nói với board thật | both, blocked | Chờ #3 và #7. GUI --port COMx, bật chế độ ghi lượt thử, bấm Có/Không theo thiết bị. |
| 10 | BOTH-05/06: Đánh giá cuối, báo cáo, video | both, blocked | Theo docs/REPORT_TEMPLATE.md và docs/MEASUREMENTS.md. |
| 11 | IT-05: Thử CNN nhỏ (PyTorch) | it | Làm sau #3, dùng cùng tập train/validation/test với baseline. |
