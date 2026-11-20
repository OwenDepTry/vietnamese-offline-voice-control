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

## Công cụ bổ sung (bản cập nhật)
- 24 tests PASS trên Linux, Python 3.13, scikit-learn 1.9 và matplotlib 3.11.2 (requirements ghim scikit-learn 1.8.0; CI chạy Python 3.12). 1 test GUI bị bỏ qua vì môi trường không có tkinter.
- ml.check_data chạy trên 90 bản thu thật p01/s01: gắn cờ đúng 5 file đã phát hiện khi nghe/kiểm tra thủ công (1 quá nhỏ, 4 bị cắt cuối), không gắn cờ file silence nào.
- Luồng GUI (thu, nhận diện, lệnh tay, ghi lượt thử, đánh dấu vật lý, lỗi serial, kết nối lại) được chạy với tkinter giả lập và firmware ảo; chưa mở cửa sổ Tkinter thật.
- Firmware ảo qua `--port fake` được kiểm tra với SerialClient thật. Chế độ cổng COM ảo (com0com, pySerial) và script đóng gói exe chưa được chạy trên Windows.
- Các con số từ dữ liệu thật trong quá trình phát triển chỉ là smoke test trên cùng một phiên thu, không dùng làm kết quả dự án.

## Notebooks
- 4 notebook được chạy toàn bộ các ô code bằng trình chạy mô phỏng kernel (không có Jupyter trong môi trường kiểm thử): 01 trên 90 bản thu thật; 02 và 03 trên phiên giả tách từ s01 (chỉ để kiểm tra luồng); 04 với firmware ảo. Chạy lại lần hai (model/đánh giá đã có) và trường hợp chưa đủ phiên đều cho thông báo đúng. Chưa mở trong JupyterLab/VS Code thật.
- Tổng cộng 28 tests PASS (1 test GUI bỏ qua do không có tkinter). tests/test_notebooks.py kiểm tra JSON hợp lệ, đã xóa output, cú pháp từng ô và các hàm import từ app/ml còn tồn tại.
