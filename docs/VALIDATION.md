# Kiểm chứng bản bàn giao

- 9 tests unittest đã PASS trên Python runtime Linux với NumPy 2.3.5, SciPy 1.17.0, scikit-learn 1.8.0 và joblib 1.5.3.
- Luồng đầu-cuối dùng sóng tổng hợp để kiểm tra lưu WAV/manifest, chia speaker, huấn luyện, lưu/nạp model, đánh giá và xuất báo cáo; không phải dữ liệu tiếng Việt.
- Serial dùng transport giả: ACK đúng/sai, stale id, ERR, reset, timeout và dòng quá dài; không kiểm chứng board thật.
- Chưa có micro và phần cứng ở môi trường kiểm thử, nên thu âm thật và USB/UART thật cần kiểm chứng tại máy của nhóm.
- Tkinter đã import được, nhưng môi trường không có display; chưa chạy hoặc đánh giá trực quan GUI. CLI mô phỏng được kiểm tra riêng.
- Không đóng gói model tổng hợp hoặc số liệu giả làm kết quả dự án.

## Tài liệu API tham chiếu
- https://scikit-learn.org/stable/modules/generated/sklearn.pipeline.Pipeline.html
- https://python-sounddevice.readthedocs.io/en/latest/usage.html
- https://pyserial.readthedocs.io/en/latest/pyserial_api.html

## Kiểm tra bổ sung
- CLI mô phỏng LIGHT_ON → FAN_ON → LIGHT_OFF chạy đúng và tạo log.
- pySerial 3.5 được kiểm tra với pseudo-terminal Linux: mở cổng, nhận READY, gửi CMD, nhận ACK thành công. Đây vẫn chưa phải board thật.
- sounddevice 0.5.3 cài được nhưng import không chạy ở môi trường này vì thiếu thư viện hệ thống PortAudio. Thu âm thật chưa được kiểm chứng.
