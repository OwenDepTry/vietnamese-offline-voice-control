# Tạo các issue trong docs/ISSUES.md lên GitHub.
# Cần cài GitHub CLI (https://cli.github.com) và chạy gh auth login trước.
# Chạy ở thư mục gốc repo:  powershell -ExecutionPolicy Bypass -File scripts\create_issues.ps1
# Chỉ chạy một lần, chạy lại sẽ bị trùng issue.
$ErrorActionPreference = "Stop"
$repo = "OwenDepTry/vietnamese-offline-voice-control"
foreach ($l in @("it","ee","both","data","blocked")) { gh label create $l --repo $repo --force | Out-Null }
$issues = @(
  @('IT-01: Bỏ đoạn im lặng đầu file và tắt lọc ồn micro', 'it,data', 'File nào cũng bắt đầu bằng khoảng 0,1-0,18 s toàn số 0, và tiếng nền trong file silence giảm khoảng 14 dB sau giây 1,3 (có thể do Audio enhancements của Windows). Sửa recorder hoặc ghi vào phần hạn chế; nếu sửa thì thu lại s01. Xem thêm docs/TASKS.md.'),
  @('BOTH-03: Thu p01/s02 và p01/s03', 'it,data', 'Mỗi phiên 6 nhãn x 5 mẫu, thu lúc khác hoặc chỗ khác trong phòng, câu unknown khác với s01. Thu xong chạy ml.check_data. Xem thêm docs/TASKS.md.'),
  @('IT-05/06: Kết quả baseline đầu tiên', 'it', 'Notebook 02 để chọn cấu hình, notebook 03 để chấm test một lần. Đính kèm summary.md và confusion matrix. Xem thêm docs/TASKS.md.'),
  @('BOTH-03: Thu giọng p02 từ xa', 'both,data', 'Ký giấy đồng ý, p02 thu trên máy của mình rồi gửi zip, gộp bằng ml.merge_manifest, đánh giá lại với --require-new-speaker. Xem thêm docs/TASKS.md.'),
  @('IT-07: Đo độ trễ và chạy offline', 'it', 'Làm theo docs/MEASUREMENTS.md mục 1 và 2, ghi median/p95 vào báo cáo. Xem thêm docs/TASKS.md.'),
  @('EE-01/02: Chọn linh kiện, điền BOM, vẽ sơ đồ nối dây', 'ee', 'hardware/BOM.csv và hardware/wiring.md. Đầu ra phải tắt khi khởi động. Xem thêm docs/TASKS.md.'),
  @('EE-03/04: Firmware theo PROTOCOL.md', 'ee', 'Chạy python -m app.conformance --port COMx tới khi đạt hết. Xem thêm docs/TASKS.md.'),
  @('BOTH-01: Duyệt PROTOCOL.md lên v1.0', 'both', 'Checklist trong docs/INTEGRATION.md, cả hai duyệt trong PR. Xem thêm docs/TASKS.md.'),
  @('BOTH-04: Ghép giọng nói với board thật', 'both,blocked', 'Chờ #3 và #7. GUI --port COMx, bật chế độ ghi lượt thử, bấm Có/Không theo thiết bị. Xem thêm docs/TASKS.md.'),
  @('BOTH-05/06: Đánh giá cuối, báo cáo, video', 'both,blocked', 'Theo docs/REPORT_TEMPLATE.md và docs/MEASUREMENTS.md. Xem thêm docs/TASKS.md.'),
  @('IT-05: Thử CNN nhỏ (PyTorch)', 'it', 'Làm sau #3, dùng cùng tập train/validation/test với baseline. Xem thêm docs/TASKS.md.')
)
foreach ($i in $issues) {
  gh issue create --repo $repo --title $i[0] --label $i[1] --body $i[2]
}
Write-Host "Đã tạo $($issues.Count) issue."
