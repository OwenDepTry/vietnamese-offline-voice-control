# Cấu trúc code phần CNTT

## Các file chính

Thu âm và app:
- `app/common.py`: đọc danh sách nhãn từ `configs/commands.json`, các file khác dùng chung.
- `app/recorder.py`: thu 2 giây, lưu WAV PCM16, ghi thêm dòng vào manifest, kiểm tra nhanh chất lượng sau mỗi lần thu.
- `app/controller.py`: nhận kết quả nhận dạng, chặn unknown/silence, gửi lệnh và ghi log.
- `app/serial_client.py`: chế độ mô phỏng và serial thật (READY, ACK/ERR, timeout).
- `app/fake_device.py`: firmware ảo viết bằng Python, làm đúng theo PROTOCOL.md, có thể giả lập lỗi.
- `app/conformance.py`: chạy 19 trường hợp để kiểm tra firmware thật có đúng giao thức không.
- `app/trials.py`: ghi từng lượt thử vào `results/measurements.csv`.
- `app/main.py`: bản dòng lệnh. `app/gui.py`: giao diện Tkinter.

Học máy:
- `ml/features.py`: đọc WAV, đổi sample rate, tính MFCC (có tùy chọn dời đoạn nói vào giữa).
- `ml/quality.py`: các luật phát hiện file nói nhỏ, bị cắt, bị rè, silence có tiếng.
- `ml/dataset.py`: đọc manifest, báo lỗi nếu một phiên bị lẫn vào hai tập hoặc có file trùng.
- `ml/prepare_data.py`: chia train/validation/test (tự động theo người, hoặc chỉ định người/phiên).
- `ml/train_baseline.py`: train scaler + bộ phân loại trên tập train, chọn ngưỡng trên validation.
- `ml/compare.py`: so sánh các cấu hình, chỉ dùng validation.
- `ml/predict.py`: nạp model, trả về nhãn và score.
- `ml/evaluate.py`: chấm trên tập test, xuất JSON và CSV.
- `ml/report.py`, `ml/learning_curve.py`, `ml/trial_report.py`, `ml/viz.py`: hình và bảng cho báo cáo.
- `ml/check_data.py`, `ml/merge_manifest.py`: kiểm tra dữ liệu, gộp dữ liệu thu từ máy khác.

`notebooks/`: phân tích bằng Jupyter, chỉ gọi lại các hàm ở trên.

Nếu mới đọc code thì nên đi theo thứ tự: recorder, features, dataset, train_baseline, predict, controller, serial_client, gui.

## Đặc trưng

Mỗi clip 2 giây, 16 kHz. Frame 25 ms, bước 10 ms, FFT 512, 40 bộ lọc mel, lấy 13 hệ số MFCC. Sau đó chia clip thành 4 đoạn thời gian, mỗi đoạn lấy trung bình và độ lệch chuẩn, ra vector 104 chiều.

Chia 4 đoạn để giữ được thứ tự thời gian: "bật" và "tắt" khác nhau ở đầu câu, "đèn" và "quạt" khác ở cuối câu. Nếu lấy trung bình cả clip thì mất thông tin này.

Clip ngắn hơn 2 giây thì được đệm thêm, dài hơn thì báo lỗi chứ không tự cắt. Không chuẩn hóa theo biên độ lớn nhất vì sẽ làm tiếng nền to lên. Scaler chỉ fit trên tập train.

## File model

Mỗi file `.joblib` lưu: pipeline (scaler + bộ phân loại), cấu hình đặc trưng, ngưỡng, seed, phiên bản thư viện, danh sách người/phiên đã dùng để train và validation, mã băm SHA256 của các file đã dùng. Nhờ vậy `ml.evaluate` biết được tập test có bị trùng với dữ liệu train không.

Score của model không phải xác suất đã hiệu chỉnh, chỉ dùng để so với ngưỡng. `unknown` vừa là một lớp có dữ liệu thật, vừa là kết quả trả về khi score của lệnh thấp hơn ngưỡng.

## Hạn chế đã biết

- MFCC chia 4 đoạn có thể chưa đủ để phân biệt bật/tắt khi có tiếng ồn, phải xem confusion matrix.
- Ngưỡng đang chọn theo macro-F1, chưa ưu tiên riêng việc giảm kích hoạt nhầm. Nếu cần thì đổi tiêu chí trên validation trước khi chấm test.
- Dữ liệu ít người nên chưa nói được gì về khả năng nhận giọng người lạ.
- Chưa xử lý khác biệt giữa các loại micro.

Có code không có nghĩa là xong việc: vẫn phải thu dữ liệu, nghe lại, train bằng giọng thật, thử với board và ghi số liệu thì mới đánh dấu hoàn thành trong `docs/TASKS.md`.
