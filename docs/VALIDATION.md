# Đã kiểm tra những gì

Ghi lại phần nào đã thử thật, phần nào mới chỉ có test tự động, để lúc viết báo cáo không ghi quá lên.

## Test tự động

Chạy `python -m unittest discover -s tests -v` (hiện có 32 test, CI trên GitHub cũng chạy lại mỗi lần push). Test dùng âm thanh tổng hợp và cổng serial giả, nên chỉ chứng minh code chạy đúng logic, không nói gì về độ chính xác với giọng tiếng Việt. Các phần được test:

- Thu và lưu WAV, ghi manifest, chặn mã người nói không hợp lệ.
- Chia tập theo người/phiên, báo lỗi khi một phiên bị lẫn vào hai tập hoặc có file trùng.
- Train, lưu/nạp model, chọn ngưỡng, đánh giá, các tùy chọn svm/mlp/align/augment.
- Serial: ACK đúng/sai id, ERR, reset giữa chừng, timeout, dòng quá dài. Sau lỗi thì app không tự gửi lại.
- Firmware ảo đúng giao thức, và công cụ `app.conformance` bắt được các lỗi firmware hay gặp.
- Toàn bộ luồng từ chia tập tới gửi lệnh vẫn chạy khi chặn hết kết nối mạng (`tests/test_offline.py`).
- Kiểm tra chất lượng file, gộp dữ liệu, ghi lượt thử, notebook (đã xóa output, import đúng).

## Dữ liệu thật

- Đã thu 90 mẫu p01/s01 (6 nhãn x 15). `ml.check_data` gắn cờ 5 file: 1 file nói quá nhỏ, 4 file tiếng nói chạm cuối file. Khớp với lúc nghe lại bằng tai.
- Khi xem phổ tần thì thấy: đầu file nào cũng có khoảng 0,1-0,18 s toàn số 0 (micro mở chậm), và tiếng nền trong file silence giảm khoảng 14 dB sau giây 1,3. Có thể do chế độ lọc ồn của Windows. Chưa xử lý.
- Chưa có kết quả nhận dạng thật vì mới có một phiên. Mấy con số thử trong lúc viết code (tách s01 ra làm nhiều phần) không dùng làm kết quả.

## Chưa thử

- Board thật, firmware thật, `app.conformance` với cổng COM thật.
- Cặp cổng COM ảo bằng com0com.
- Đóng gói exe (`packaging/build_exe.ps1`) và script tạo issue.
- GUI: cần thử lại đầy đủ các chức năng mới trên máy (Space, chế độ ghi lượt thử, nút Có/Không, kết nối lại).
- Notebook 02 và 03 với dữ liệu thật (đang chờ s02, s03).

## Tài liệu tham khảo

- scikit-learn Pipeline: https://scikit-learn.org/stable/modules/generated/sklearn.pipeline.Pipeline.html
- python-sounddevice: https://python-sounddevice.readthedocs.io/en/latest/usage.html
- pySerial API: https://pyserial.readthedocs.io/en/latest/pyserial_api.html
