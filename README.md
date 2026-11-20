# Vietnamese Offline Voice Control

Offline Vietnamese command classification and low-voltage device control.

**Phần CNTT cho MVP đã được triển khai. Chưa có mô hình nhận tiếng Việt đã huấn luyện, dữ liệu giọng nói hoặc kết quả trên phần cứng thật.** Code có thể chạy mô phỏng ngay; nhận giọng nói cần thu dữ liệu và train.

## Chức năng
- Thu WAV 2 giây, mono 16 kHz, PCM16; manifest với mã người nói/phiên thu.
- Chia train/validation/test theo người nói (tự động, từ 3 người) hoặc chỉ định theo người/phiên thu cho nhóm nhỏ; một phiên thu không bao giờ nằm ở hai tập; kiểm tra đường dẫn trùng và WAV trùng giữa các tập.
- MFCC theo 4 đoạn thời gian + StandardScaler + Logistic Regression.
- Chọn ngưỡng từ chối bằng macro-F1 trên validation; không dùng test để chọn mô hình.
- Báo cáo classification, confusion matrix, kích hoạt nhầm và từ chối lệnh; CSV dự đoán.
- CLI và giao diện Tkinter: điều khiển gõ tay/nút bấm, ghi âm 2 giây, mô phỏng hoặc serial.
- Serial theo docs/PROTOCOL.md: READY, ACK, ERR, timeout, không tự gửi lại khi lỗi.
- Log sự kiện JSONL; không lưu âm thanh trong chế độ nhận diện trực tiếp.

## Bắt đầu (Windows / Python 3.12)
Mở terminal trong thư mục chứa README này.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m app.gui
```

Không cần activate venv nên tránh lỗi PowerShell execution policy. Trong các lệnh tiếp theo, `python` nghĩa là Python trong .venv; nếu chưa activate, thay bằng `.\.venv\Scripts\python.exe`.

Linux/macOS: `python3 -m venv .venv`, `source .venv/bin/activate`, rồi `pip install -r requirements.txt`. Linux cần Tk và PortAudio từ hệ điều hành cho GUI/micro (thường là python3-tk và libportaudio2).

## Thu dữ liệu
Xin phép người tham gia; dùng mã vô danh. Mỗi người nên thu cả 6 nhãn. `unknown`: nhiều câu không phải 4 lệnh. `silence`: nền phòng/tiếng quạt, không đọc chữ “silence”.

```powershell
python -m sounddevice
python -m app.recorder --speaker p01 --session s01 --label LIGHT_ON --count 15 --consent
```

Lặp lại với `LIGHT_OFF`, `FAN_ON`, `FAN_OFF`, `unknown`, `silence`, rồi người khác. Có thể chọn `--device 1`, `--noise fan`, `--distance 1.5`.
Nhấn Enter để bắt đầu mỗi bản thu, nói ngay và nói trọn câu trong 2 giây. Một tiến trình thu dữ liệu tại một thời điểm. Không commit bản thu cá nhân.

## Chia dữ liệu, train, đánh giá
Có hai cách chia:

- **Tự động theo người nói** (cần ít nhất 3 người; nên từ 10 người cho pilot):
  `python -m ml.prepare_data --manifest data/manifest.csv --output data/manifest_split.csv`
- **Chỉ định** bằng `--validation` và `--test`, mỗi mục là `người` (vd. `p02`) hoặc `người/phiên` (vd. `p01/s02`); phần còn lại vào train.
  - Một người, ba phiên: `--validation p01/s02 --test p01/s03`
  - Hai người: `--validation p01/s02 --test p02`

Mỗi phiên trong validation/test phải có đủ 6 nhãn. Nếu người trong test đã xuất hiện ở train/validation, `ml.evaluate` vẫn chạy nhưng ghi `evaluation_type: same_speaker_new_session`: kết quả chỉ cho biết model nhận đúng bản thu mới của giọng đã biết, chưa chứng minh nhận được người lạ. Thêm `--require-new-speaker` để bắt buộc test là người mới.

```powershell
python -m ml.prepare_data --manifest data/manifest.csv --output data/manifest_split.csv --validation p01/s02 --test p01/s03
python -m ml.train_baseline --manifest data/manifest_split.csv --output models/baseline.joblib
python -m ml.evaluate --manifest data/manifest_split.csv --model models/baseline.joblib --output results/eval_01
```

Các bước từ chối ghi đè kết quả cũ; dùng tên mới cho thí nghiệm mới. Giữ test cố định, chỉ xem sau khi chốt mô hình. Không chọn lại seed để làm đẹp test. File .joblib chỉ nạp từ nguồn tin cậy do pickle có thể thực thi mã.

## Demo giọng nói offline
```powershell
python -m app.gui --model models/baseline.joblib
python -m app.main --model models/baseline.joblib
python -m ml.predict data/raw/p01/s01/TEN_FILE.wav --model models/baseline.joblib
```

GUI không có model vẫn điều khiển mô phỏng bằng 4 nút; nút ghi âm bị khóa. CLI dùng `voice` để ghi âm, `LIGHT_ON`... để gõ lệnh, `quit` để thoát. Mô hình, đặc trưng và suy luận đều cục bộ, không gọi API mạng.

## Ghép phần cứng
```powershell
python -m app.gui --model models/baseline.joblib --port COM3
python -m app.main --mode serial --port COM3 --model models/baseline.joblib
```

Firmware phải gửi READY,1 khi kết nối/khởi động. Nếu board không reset khi mở cổng, reset thủ công trong 5 giây chờ. Chỉ một ứng dụng mở COM tại một thời điểm. Sau lỗi/timeout, bấm «Kết nối lại» trong GUI (hoặc mở lại CLI); app không tự gửi lại lệnh. Trước khi có board, thử toàn bộ chuỗi với `--port fake` (firmware ảo). ACK chỉ xác nhận đầu ra đã được đặt, không chứng minh quạt thật sự quay.

## Công cụ bổ sung
Chi tiết trong docs/TOOLS.md:

| Việc | Lệnh |
|---|---|
| Kiểm tra dữ liệu (file nhỏ, bị cắt, thiếu nhãn) | `python -m ml.check_data` |
| Gộp dữ liệu người khác thu từ xa | `python -m ml.merge_manifest --incoming <manifest.csv>` |
| Chạy app với firmware ảo, không cần board | `python -m app.gui --model models/baseline.joblib --port fake` |
| So sánh cấu hình model trên validation | `python -m ml.compare` |
| Train với tùy chọn mới | `python -m ml.train_baseline --classifier svm --align --augment 3 ...` |
| Hình confusion matrix, F1, learning curve | `python -m ml.report --eval results/eval_01`, `python -m ml.learning_curve` |
| Tổng hợp lượt thử và độ trễ | `python -m ml.trial_report` |
| Đóng gói exe | `packaging\build_exe.ps1` |
| Phân tích bằng Jupyter (nghe dữ liệu, hình, lỗi) | `pip install -r requirements-notebook.txt` rồi `jupyter lab`, xem notebooks/README.md |

Thu âm giờ có bước nghe lại: Enter = lưu, `r` = thu lại, `p` = nghe lại. GUI: Space để nói, lịch sử, chế độ ghi lượt thử, nút kết nối lại.

## Kiểm thử
```powershell
python -m unittest discover -s tests -v
```

Tests dùng tín hiệu tổng hợp và serial giả để kiểm tra phần mềm; không phải kết quả nhận diện tiếng Việt. Xem docs/VALIDATION.md về giới hạn kiểm chứng.

## Tài liệu và phân công
- docs/QUICKSTART_14_DAYS.md: lịch tích hợp 2 tuần.
- docs/IMPLEMENTATION.md: từng module và cách học code.
- docs/TASKS.md: phân công ban đầu, các ô là tiến độ thực hiện/kiểm chứng của nhóm.
- docs/PROTOCOL.md: hợp đồng với firmware.
- docs/TEST_PLAN.md: kiểm thử thực tế.
- notebooks/: 4 notebook khám phá dữ liệu, huấn luyện, đánh giá, giao thức serial (gọi lại code trong ml/ và app/).
- docs/TOOLS.md: công cụ dữ liệu, firmware ảo, so sánh model, báo cáo, GUI, đóng gói exe.
- hardware/ và firmware/: do thành viên ĐTVT triển khai, chưa có firmware hoàn chỉnh; app/fake_device.py là bản tham chiếu hành vi.

CNN, nghe liên tục, wake word và chạy mô hình trên MCU nằm ngoài MVP 14 ngày. Chưa chọn giấy phép; hai thành viên cần thống nhất trước khi cấp quyền tái sử dụng.
