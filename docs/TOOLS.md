# Hướng dẫn các công cụ

Chạy mọi lệnh ở thư mục gốc repo, bằng python trong `.venv`. Các lệnh đều không ghi đè kết quả cũ, nên mỗi lần chạy đặt tên file hoặc thư mục mới.

## Kiểm tra dữ liệu

```powershell
python -m ml.check_data
python -m ml.check_data --report results/data_check.csv
python -m ml.check_data --drop-flagged data/manifest_clean.csv
```

Lệnh in bảng số mẫu theo từng phiên và nhãn, báo phiên nào còn thiếu nhãn, và liệt kê các file nên nghe lại:

- `too_quiet`: nói nhỏ quá hoặc xa micro
- `cut_start`, `cut_end`: tiếng nói chạm đầu/cuối file, có thể bị mất chữ
- `clipped`: to quá, bị rè
- `no_speech`: gần như không có tiếng nói
- `not_silent`: file silence nhưng có tiếng động lớn

Đây chỉ là luật ước lượng nên nghe lại trước rồi mới bỏ. `--drop-flagged` chỉ tạo một manifest mới không có các file bị gắn cờ, không xóa file WAV. Muốn xóa hẳn thì xóa cả file WAV lẫn dòng của nó trong `data/manifest.csv`.

Lúc thu, `app.recorder` cũng tự kiểm tra từng bản: Enter để lưu, `r` để thu lại, `p` để nghe lại (chọn loa bằng `--output-device`). Thêm `--no-review` nếu muốn lưu luôn như cách cũ.

## Gộp dữ liệu từ máy khác

Bạn kia clone repo, cài môi trường, thu bằng mã riêng (ví dụ `--speaker p02`), rồi gửi file `data/manifest.csv` kèm thư mục `data/raw/p02/` (nén zip). Giải nén ở đâu cũng được, sau đó:

```powershell
python -m ml.merge_manifest --incoming D:\tu_p02\data\manifest.csv --dry-run
python -m ml.merge_manifest --incoming D:\tu_p02\data\manifest.csv
```

File WAV sẽ được chép vào `data/raw/<người>/<phiên>/`, các dòng mới được thêm vào `data/manifest.csv`, file cũ được sao lưu thành `manifest.csv.bak-<thời gian>`. Nếu trùng mã người/phiên, trùng file, hoặc thiếu file thì lệnh dừng và không đổi gì. Nếu bạn kia lỡ thu bằng mã `p01` thì thêm `--rename-speaker p01=p02`.

## Firmware ảo

`app/fake_device.py` là một thiết bị giả trả lời đúng theo `docs/PROTOCOL.md`: gửi READY khi khởi động, trả ACK/ERR, giới hạn 64 byte mỗi dòng, lệnh sai thì không đổi trạng thái.

Cách nhanh nhất, không cần cài gì thêm:

```powershell
python -m app.gui --model models/baseline.joblib --port fake
python -m app.main --mode serial --port fake
```

App vẫn đi qua đúng phần code serial như khi nối board thật, và GUI hiện trạng thái đèn/quạt của thiết bị giả.

Muốn thử app xử lý lỗi thế nào thì thêm `--fault timeout` (hoặc `error`, `reset`, `mismatch`). Sau khi bị lỗi thì bấm "Kết nối lại" trong GUI.

Nếu muốn thử cả pySerial và driver cổng COM thì cài [com0com](https://com0com.sourceforge.net/), tạo một cặp cổng ảo (ví dụ COM10 và COM11) rồi mở hai cửa sổ:

```powershell
python -m app.fake_device --port COM11                              # cửa sổ 1: thiết bị
python -m app.gui --model models/baseline.joblib --port COM10       # cửa sổ 2: app
```

Cách này nhóm chưa thử trên Windows.

## Cải thiện model

`ml.train_baseline` có thêm mấy tùy chọn:

- `--classifier logreg`, `svm` hoặc `mlp`: hồi quy logistic (mặc định), SVM, hoặc mạng nơ-ron nhỏ một lớp ẩn.
- `--align`: dời đoạn có tiếng nói vào giữa clip trước khi tính MFCC, vì mỗi lần mình bắt đầu nói ở thời điểm hơi khác nhau.
- `--augment N`: mỗi file train tạo thêm N bản biến thể (dịch thời gian, đổi âm lượng, trộn tiếng nền lấy từ các file silence).

Để so sánh các cấu hình thì chạy (chỉ dùng validation, không đụng test):

```powershell
python -m ml.compare --manifest data/manifest_split.csv --output results/compare_01.csv
```

Lệnh in bảng xếp hạng và câu lệnh train cho cấu hình tốt nhất. Validation ít mẫu thì chênh vài điểm cũng có thể chỉ là ngẫu nhiên, nếu ngang nhau thì chọn cấu hình đơn giản hơn. Chốt xong mới chạy `ml.evaluate` trên test, và chỉ chạy một lần.

CNN chưa có vì cần cài PyTorch khá nặng. `mlp` là mạng nơ-ron nhỏ của scikit-learn.

## Hình và số liệu cho báo cáo

```powershell
python -m ml.report --eval results/eval_01
python -m ml.learning_curve --manifest data/manifest_split.csv --output results/learning_curve_01
python -m ml.trial_report
```

- `ml.report` tạo `confusion_matrix.png`, `per_class_f1.png` và `summary.md` trong thư mục kết quả.
- `ml.learning_curve` vẽ macro-F1 trên validation khi dùng 20% tới 100% dữ liệu train. Nếu đường vẫn còn đi lên thì thu thêm dữ liệu vẫn có ích.
- `ml.trial_report` tổng hợp các lượt thử trong `results/measurements.csv` (đúng, bỏ sót, sai lệnh, kích hoạt nhầm, thiết bị chạy thật, độ trễ median và p95) và độ trễ trong `results/events.jsonl`.

Độ trễ ở đây tính từ lúc thu xong 2 giây tới lúc có kết quả (ở chế độ serial thì tới lúc có ACK).

## GUI

- Bấm Space để thu 2 giây và nhận lệnh. Đang gõ trong ô nhập thì Space không kích hoạt.
- Dòng chữ lớn hiện lệnh nghe được, độ tin cậy, có thực hiện hay không. Nếu bản thu nhỏ quá hoặc bị cắt thì có cảnh báo.
- Phần lịch sử hiện 50 lần gần nhất kèm độ trễ.
- Chế độ thử nghiệm: tick "Ghi lượt thử", điền người nói, điều kiện (ví dụ `quiet`, `fan`, `2m`) và lệnh định nói. Mỗi lần nói sẽ được ghi vào `results/measurements.csv`. Nếu đang nhìn thiết bị thật thì bấm Có/Không để ghi thiết bị có chạy đúng không.
- Nút "Kết nối lại" dùng khi serial bị lỗi (chỉ hiện khi chạy với `--port`).

## Đóng gói exe

```powershell
powershell -ExecutionPolicy Bypass -File packaging\build_exe.ps1
```

Kết quả là `dist\VoiceControl\VoiceControl.exe`. Nếu đã có `models\baseline.joblib` thì script chép theo và exe tự nạp model đó. Nén cả thư mục `dist\VoiceControl` là chạy được trên máy khác không cần cài Python. Script này nhóm chưa chạy thử, nếu exe báo thiếu module thì thêm `--hidden-import <tên module>` vào script.
