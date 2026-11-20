# Phân công và tiến độ

Cập nhật ngày 21/11/2026. Nhóm gồm Đạt (CNTT) và Thái (ĐTVT).

Cách ghi trạng thái:
- Xong: đã có và đã thử với dữ liệu hoặc phần cứng thật.
- Có code: phần mềm đã viết, có test tự động, nhưng chưa thử với dữ liệu đủ phiên hoặc board thật.
- Chưa làm
- Đang chờ: phải đợi việc khác xong trước.

Chỉ ghi "Xong" khi có bằng chứng (kết quả trong `results/`, ảnh, video, số đo trong `measurements.csv`).

## Đạt (CNTT)

| Mã | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| IT-01 | Chốt nhãn, công cụ thu WAV 16 kHz mono | Có code | Đã thu 90 mẫu p01/s01. Còn: xử lý khoảng 0,15 s im lặng ở đầu mỗi file, tắt lọc ồn của Windows, nghe lại 5 file bị gắn cờ |
| IT-02 | Manifest, mã ẩn danh cho người nói | Có code | Manifest đủ cột, recorder bắt xác nhận `--consent` trước khi thu |
| IT-03 | Chia tập theo người/phiên, chống trùng | Có code | Chờ có s02, s03 để chạy thật |
| IT-04 | Tiền xử lý thống nhất | Có code | Chốt cấu hình sau khi chạy `ml.compare` với dữ liệu thật |
| IT-05 | Baseline, sau đó CNN nhỏ | Có code | Đã có logreg/svm/mlp. CNN làm sau khi có kết quả baseline |
| IT-06 | Ngưỡng từ chối, thử unknown/silence | Có code | Cần số liệu thật |
| IT-07 | App nhấn để nói, gửi lệnh, xử lý ACK/ERR/timeout | Có code | GUI, CLI, firmware ảo, test chặn mạng. Còn đo độ trễ và thử với board |
| IT-08 | Hướng dẫn cài đặt, khóa phiên bản thư viện | Xong | `requirements.txt`, README, CI |

## Thái (ĐTVT)

| Mã | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| EE-01 | Chọn board, nguồn, LED, quạt, mạch lái; điền `hardware/BOM.csv` | Chưa làm | Gợi ý: Nano clone CH340 hoặc STM32F411 có sẵn, quạt 5V nhỏ, S8050/2N2222 hoặc AO3400, diode 1N4007 |
| EE-02 | Sơ đồ nối dây, chân GPIO, đầu ra tắt khi khởi động | Chưa làm | Thêm điện trở kéo xuống 10k ở chân điều khiển |
| EE-03 | Firmware bật/tắt bằng lệnh gõ tay | Chưa làm | Thử bằng `python -m app.main --mode serial --port COMx` |
| EE-04 | Parser theo PROTOCOL.md | Chưa làm | Kiểm tra bằng `python -m app.conformance --port COMx`, tham khảo `app/fake_device.py` |
| EE-05 | Kiểm tra mạch lái, nguồn, nhiễu quạt, chạy lâu, reset | Chưa làm | |
| EE-06 | Ảnh mạch, sơ đồ chân, hướng dẫn nạp, bảng đo | Chưa làm | |
| EE-07 | (Sau MVP) micro I2S trên board | Chưa làm | Chỉ làm nếu chuyển model xuống vi điều khiển |

## Cả hai

| Mã | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| BOTH-01 | Chốt giao thức, nhãn, phần cứng, tiêu chí | Có code | Nhãn đã chốt. PROTOCOL v0.1 cần hai đứa duyệt, checklist trong `docs/INTEGRATION.md` |
| BOTH-02 | Gõ lệnh, gửi serial, thiết bị phản hồi | Có code | Đã chạy với firmware ảo, đang chờ firmware thật (EE-03) |
| BOTH-03 | Thu dữ liệu (hỏi ý người thu), nhiều người/phiên/môi trường | Có code | Xong p01/s01. Còn s02, s03, p02, điều kiện ồn và xa |
| BOTH-04 | Ghép nhận dạng với điều khiển | Đang chờ | Cần IT-05/06 có kết quả và EE-03/04 |
| BOTH-05 | Đánh giá người mới, khoảng cách, ồn, độ trễ | Đang chờ | Sau khi chốt model, làm theo `docs/MEASUREMENTS.md` |
| BOTH-06 | README, báo cáo, video, ghi rõ ai làm gì | Có code | Đã có khung `docs/REPORT_TEMPLATE.md` |

## Thứ tự

IT-01/02 và EE-01/02 làm song song được. BOTH-01 phải xong trước EE-04. BOTH-02 không cần model. BOTH-04 cần IT-05/06/07 và EE-03/04. BOTH-05 chỉ làm khi đã chốt model.

Danh sách việc còn lại dạng issue: `docs/ISSUES.md`.
