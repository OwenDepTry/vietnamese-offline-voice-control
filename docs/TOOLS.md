# Công cụ phần mềm bổ sung

Mọi lệnh chạy từ thư mục gốc repo, trong venv. Các lệnh không ghi đè kết quả cũ: đặt tên file/thư mục mới cho mỗi lần chạy.

## 1. Kiểm tra chất lượng dữ liệu

```powershell
python -m ml.check_data
python -m ml.check_data --report results/data_check.csv
python -m ml.check_data --drop-flagged data/manifest_clean.csv
```

In bảng số mẫu theo phiên × nhãn, báo phiên thiếu nhãn (exit code 1) và liệt kê file nên nghe lại:

| Cờ | Ý nghĩa |
|---|---|
| `too_quiet` | nói quá nhỏ/xa micro (đỉnh < 0.15) |
| `cut_start`, `cut_end` | tiếng nói chạm đầu/cuối file, có thể mất chữ |
| `clipped` | quá to, bị rè |
| `no_speech` | gần như không có tiếng nói |
| `not_silent` | nhãn silence nhưng có tiếng động lớn |

Đây là luật ước lượng: **nghe lại trước khi bỏ**. `--drop-flagged` chỉ tạo manifest mới không có các file bị gắn cờ, không xóa WAV. Muốn xóa hẳn một bản thu, xóa cả WAV và dòng tương ứng trong `data/manifest.csv`.

Khi thu âm, `app.recorder` giờ tự kiểm tra từng bản: Enter = lưu, `r` = thu lại, `p` = nghe lại (chọn loa bằng `--output-device`). Dùng `--no-review` để lưu ngay như trước.

## 2. Gộp dữ liệu thu từ máy khác

Người kia clone repo, cài venv, thu với mã riêng (vd. `--speaker p02`), rồi gửi `data/manifest.csv` kèm thư mục `data/raw/p02/` (nén zip). Giải nén ở đâu cũng được, rồi:

```powershell
python -m ml.merge_manifest --incoming D:\tu_p02\data\manifest.csv --dry-run
python -m ml.merge_manifest --incoming D:\tu_p02\data\manifest.csv
```

WAV được chép vào `data/raw/<người>/<phiên>/`, dòng mới được nối vào `data/manifest.csv`, bản cũ được sao lưu thành `manifest.csv.bak-<thời gian>`. Lệnh dừng mà không đổi gì nếu: trùng mã người/phiên đã có, trùng nội dung WAV, thiếu file. Nếu người kia lỡ thu bằng `p01`: `--rename-speaker p01=p02`.

## 3. Firmware ảo (thiết bị giả bằng Python)

`app/fake_device.py` làm đúng như firmware theo `docs/PROTOCOL.md`: READY khi khởi động, ACK/ERR, giới hạn 64 byte, lệnh sai không đổi trạng thái.

Không cần cài gì thêm:
```powershell
python -m app.gui --model models/baseline.joblib --port fake
python -m app.main --mode serial --port fake
```
App đi qua đúng code `SerialClient` như với board thật; GUI hiện trạng thái đèn/quạt của thiết bị ảo.

Thử cách app xử lý sự cố: `--fault timeout|error|reset|mismatch` (vd. `--port fake --fault timeout`). Sau lỗi bấm **Kết nối lại** trong GUI.

Qua cặp cổng COM ảo (kiểm tra cả pySerial và driver): cài [com0com](https://com0com.sourceforge.net/), tạo cặp, ví dụ COM10↔COM11, rồi:
```powershell
python -m app.fake_device --port COM11          # cửa sổ 1: thiết bị
python -m app.gui --model models/baseline.joblib --port COM10   # cửa sổ 2: app
```
Thiết bị ảo gửi READY mỗi khi app mở cổng bên kia (qua tín hiệu DSR). Chế độ này chưa được kiểm chứng trên Windows thật.

Thành viên ĐTVT có thể dùng `FakeDevice.handle()` làm bản tham chiếu khi viết firmware thật.

## 4. Cải thiện mô hình

Tùy chọn mới của `ml.train_baseline`:

| Tùy chọn | Tác dụng |
|---|---|
| `--classifier logreg` / `svm` / `mlp` | hồi quy logistic (mặc định), SVM RBF, mạng nơ-ron nhỏ 1 lớp ẩn |
| `--align` | dời đoạn có tiếng nói về giữa clip trước khi tính MFCC (mỗi lần bạn bắt đầu nói ở thời điểm khác nhau) |
| `--augment N` | thêm N bản biến thể cho mỗi clip **train**: dịch thời gian, đổi âm lượng, trộn tiếng nền từ các clip silence (SNR 10–30 dB) |

So sánh các cấu hình **chỉ trên validation**, tập test không bị đụng tới:
```powershell
python -m ml.compare --manifest data/manifest_split.csv --output results/compare_01.csv
```
Lệnh in bảng xếp hạng và câu lệnh train cho cấu hình tốt nhất. Validation ít mẫu thì chênh vài điểm là nhiễu; khi ngang nhau, chọn cấu hình đơn giản hơn. Sau khi chọn xong mới chạy `ml.evaluate` trên test **một lần**.

CNN chưa được thêm vì cần PyTorch (nặng, ngoài requirements); `mlp` là mạng nơ-ron nhỏ dùng scikit-learn.

## 5. Số liệu và hình cho báo cáo

```powershell
python -m ml.report --eval results/eval_01
python -m ml.learning_curve --manifest data/manifest_split.csv --output results/learning_curve_01
python -m ml.trial_report
```

- `ml.report`: tạo `confusion_matrix.png`, `per_class_f1.png`, `summary.md` trong thư mục đánh giá.
- `ml.learning_curve`: macro-F1 trên validation khi dùng 20–100% dữ liệu train; đường còn đi lên nghĩa là thu thêm còn có ích.
- `ml.trial_report`: tổng hợp các lượt thử trong `results/measurements.csv` (đúng/bỏ sót/sai lệnh/kích hoạt nhầm, tỉ lệ thiết bị chạy thật, độ trễ median và p95 theo điều kiện) và độ trễ từ `results/events.jsonl`.

Độ trễ = từ lúc kết thúc thu 2 giây đến khi có kết quả (kèm ACK ở chế độ serial), đúng định nghĩa trong `docs/TEST_PLAN.md`.

## 6. GUI

- **Space** = thu 2 giây và nhận diện (không kích hoạt khi đang gõ trong ô nhập).
- Dòng kết quả lớn: lệnh nghe được, độ tin cậy, đã thực hiện hay bị từ chối; cảnh báo nếu bản thu quá nhỏ/bị cắt.
- **Lịch sử** 50 lượt gần nhất kèm độ trễ.
- **Chế độ thử nghiệm**: tick «Ghi lượt thử», chọn người nói, điều kiện (vd. `quiet`, `fan`, `2m`) và lệnh định nói; mỗi lần nói sẽ được nối vào `results/measurements.csv`. Khi quan sát thiết bị thật, bấm **Có/Không** để ghi `physical_success` cho lượt vừa rồi.
- **Kết nối lại** sau lỗi serial (khi chạy với `--port`).

## 7. Đóng gói .exe (Windows)

```powershell
powershell -ExecutionPolicy Bypass -File packaging\build_exe.ps1
```
Tạo `dist\VoiceControl\VoiceControl.exe`; nếu có `models\baseline.joblib` thì chép kèm và exe tự nạp. Nén cả thư mục `dist\VoiceControl` để chạy trên máy khác không cần cài Python. Script chưa được chạy thử trên Windows thật; nếu exe báo thiếu module, thêm `--hidden-import <tên module>` vào script.
