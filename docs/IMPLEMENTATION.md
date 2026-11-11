# Cấu trúc phần CNTT

| File | Trách nhiệm |
|---|---|
| app/common.py | Đọc nhãn chung từ configs/commands.json |
| app/recorder.py | Thu 2 giây, lưu PCM16, thêm metadata vào manifest |
| ml/features.py | Đọc WAV, đổi sample rate, MFCC và pooling 4 đoạn |
| ml/dataset.py | Xác thực manifest, chống lẫn người nói và trùng file giữa các tập |
| ml/prepare_data.py | Chia theo speaker; không ghi đè dữ liệu gốc |
| ml/train_baseline.py | Fit scaler và logistic regression chỉ trên train; chọn threshold bằng validation |
| ml/predict.py | Nạp bundle gồm tiền xử lý, model và threshold; trả nhãn và score |
| ml/evaluate.py | Đánh giá test chưa thấy, xuất JSON/CSV |
| app/serial_client.py | Simulator và serial thật; ACK/ERR/timeout |
| app/controller.py | Chặn unknown/silence, điều phối và ghi log |
| app/main.py | CLI |
| app/gui.py | GUI Tkinter, chạy tác vụ nền để không khóa giao diện |

## Đọc code theo thứ tự
recorder → features → dataset → train_baseline → predict → controller → serial_client → gui.

## Hợp đồng mô hình
Bundle schema_version=1 chứa pipeline, feature config, threshold, seed, phiên bản thư viện, mã người nói đã dùng, SHA256 các bản ghi đã dùng và manifest. Score của Logistic Regression không phải bảo đảm xác suất đúng đã hiệu chuẩn. Unknown là lớp có dữ liệu thật và cũng là kết quả từ chối khi score lệnh thấp.

Đặc trưng: 2 giây, 16 kHz; frame 25 ms, hop 10 ms, FFT512, 40 mel, 13 MFCC; mean/std trong 4 vùng thời gian = 104 chiều. Clip ngắn được pad; clip dài bị từ chối, không âm thầm cắt. Không peak-normalize vì sẽ làm tăng tiếng nền. Scaler fit chỉ trên train.

## Hạn chế
MFCC pooling có thể chưa phân biệt tốt bật/tắt trong môi trường nhiễu; cần kiểm tra confusion matrix. Ngưỡng tối ưu macro-F1 không tối ưu riêng chi phí kích hoạt nhầm; nhóm phải đo tỷ lệ này và có thể đổi tiêu chí trên validation trước test cuối. Dữ liệu pilot nhỏ không bảo đảm hoạt động với người lạ. Chưa hiệu chỉnh domain shift giữa các micro.

## Đã có code, nhóm vẫn phải thực hiện
Thu dữ liệu và xem lại nhãn; train bằng giọng thật; nghe thử; kiểm chứng cổng COM, board, thời gian READY và mạch; ghi số liệu; tự đọc/giải thích thuật toán khi báo cáo. Không cần viết lại khung, nhưng không đánh dấu các công việc thực nghiệm đã hoàn thành chỉ vì có code.
