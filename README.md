# Vietnamese Offline Voice Control

Đồ án liên ngành CNTT + Điện tử Viễn thông: nhận lệnh giọng nói tiếng Việt ngay trên máy (không cần Internet) để bật/tắt đèn và quạt 5V qua vi điều khiển.

Hiện tại phần mềm đã chạy được ở chế độ mô phỏng và với firmware ảo. Nhóm đang thu thêm dữ liệu giọng nói để train model thật; phần cứng và firmware đang làm.

## Hệ thống làm gì

Người dùng bấm nút (hoặc Space) rồi nói một câu trong 2 giây. Máy tính trích đặc trưng MFCC, phân loại thành một trong 6 nhãn:

- 4 lệnh: `bật đèn`, `tắt đèn`, `bật quạt`, `tắt quạt`
- `unknown`: câu nói khác, không phải lệnh
- `silence`: không ai nói

Nếu là lệnh và đủ chắc chắn thì app gửi qua cổng serial cho vi điều khiển (`CMD,id,LIGHT_ON`), board bật/tắt chân ra và trả `ACK`. Nếu là unknown/silence hoặc model không chắc thì không gửi gì.

## Cài đặt (Windows, Python 3.12)

Mở terminal ở thư mục repo:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m app.gui
```

Mình gọi thẳng `.\.venv\Scripts\python.exe` thay vì activate để khỏi bị lỗi execution policy của PowerShell. Các lệnh bên dưới ghi tắt là `python`, hiểu là python trong `.venv`.

Linux/macOS thì tạo venv bằng `python3 -m venv .venv`, activate rồi `pip install -r requirements.txt`. Trên Linux cần cài thêm `python3-tk` và `libportaudio2`.

## Thu dữ liệu

Người tham gia ký giấy đồng ý trước (mẫu ở `docs/CONSENT_FORM.md`), mỗi người dùng một mã ẩn danh như `p01`, `p02`. Mỗi phiên thu đủ 6 nhãn.

```powershell
python -m sounddevice        # xem số thứ tự micro
python -m app.recorder --speaker p01 --session s01 --label LIGHT_ON --count 15 --device 1 --consent
```

Làm lại với `LIGHT_OFF`, `FAN_ON`, `FAN_OFF`, `unknown`, `silence`. Bấm Enter rồi nói ngay, gọn trong 2 giây. Thu xong mỗi mẫu, app tự kiểm tra (nói nhỏ quá, bị cắt chữ...) và cho chọn: Enter để lưu, `r` để thu lại, `p` để nghe lại.

Với `unknown` thì mỗi lần nói một câu ngắn khác nhau ("xin chào", "mấy giờ rồi"...). Với `silence` thì im lặng để thu tiếng nền. File âm thanh không đưa lên GitHub (đã có trong `.gitignore`).

Kiểm tra lại dữ liệu sau khi thu:

```powershell
python -m ml.check_data
```

## Train và đánh giá

Có hai cách chia dữ liệu:

- Đủ từ 3 người trở lên: chia tự động theo người nói.
- Ít người: tự chỉ định. Ví dụ một người thu 3 phiên thì dùng `--validation p01/s02 --test p01/s03`. Hai người thì dùng `--validation p01/s02 --test p02`.

```powershell
python -m ml.prepare_data --manifest data/manifest.csv --output data/manifest_split.csv --validation p01/s02 --test p01/s03
python -m ml.compare --manifest data/manifest_split.csv
python -m ml.train_baseline --manifest data/manifest_split.csv --output models/baseline.joblib
python -m ml.evaluate --manifest data/manifest_split.csv --model models/baseline.joblib --output results/eval_01
python -m ml.report --eval results/eval_01
```

Một vài nguyên tắc nhóm tự đặt ra:

- Một phiên thu chỉ nằm trong một tập, code sẽ báo lỗi nếu bị lẫn.
- Chọn model và ngưỡng chỉ dựa trên validation. Tập test chỉ chạy một lần khi đã chốt.
- Nếu người trong test cũng có trong train, kết quả sẽ ghi `same_speaker_new_session`, nghĩa là mới chứng minh nhận được giọng quen chứ chưa chứng minh nhận được người lạ.
- Các lệnh không ghi đè kết quả cũ, mỗi lần chạy đặt tên mới.
- File `.joblib` chỉ nạp model do nhóm tự train (pickle có thể chạy code lạ).

Ngoài logistic regression còn có thể thử `--classifier svm` hoặc `mlp`, `--align` (dời đoạn nói vào giữa) và `--augment 3` (thêm dữ liệu biến thể). `ml.compare` so sánh hết các tổ hợp này trên validation.

## Chạy demo

```powershell
python -m app.gui --model models/baseline.joblib                  # mô phỏng
python -m app.gui --model models/baseline.joblib --port fake      # qua firmware ảo
python -m app.gui --model models/baseline.joblib --port COM5      # board thật
python -m app.main --model models/baseline.joblib                 # bản dòng lệnh
```

Trong GUI: bấm Space để nói, có lịch sử các lần nhận lệnh, có chế độ ghi lượt thử vào `results/measurements.csv`, và nút "Kết nối lại" khi serial bị lỗi. Không có model thì GUI vẫn bấm 4 nút điều khiển được.

`--port fake` là một thiết bị giả viết bằng Python, trả lời đúng theo giao thức, nên có thể test cả chuỗi khi chưa có board. Khi có board thì chạy `python -m app.conformance --port COM5` để kiểm tra firmware có đúng giao thức không (19 mục).

Lưu ý: ACK chỉ có nghĩa là firmware đã nhận lệnh và đặt chân ra, chưa chắc quạt đã quay. Lúc đo phải nhìn thiết bị thật.

## Notebook

Thư mục `notebooks/` có 4 notebook để xem dữ liệu, nghe thử, train và phân tích lỗi. Notebook chỉ gọi lại các hàm trong `ml/` và `app/`.

```powershell
python -m pip install -r requirements-notebook.txt
python -m jupyter lab
```

Nhớ "Clear All Outputs" trước khi commit vì output có chứa âm thanh giọng nói.

## Test

```powershell
python -m unittest discover -s tests -v
```

Test dùng âm thanh tổng hợp và serial giả, nên chỉ kiểm tra là code chạy đúng, không nói lên độ chính xác với tiếng Việt thật.

## Tài liệu khác

- `docs/TASKS.md`: phân công và tiến độ từng việc
- `docs/PROTOCOL.md`: giao thức serial giữa máy tính và board
- `docs/INTEGRATION.md`: những điểm cần chốt và cách kiểm tra firmware
- `docs/TOOLS.md`: hướng dẫn chi tiết các công cụ
- `docs/MEASUREMENTS.md`: cách đo độ trễ, chạy offline, đo với board
- `docs/TEST_PLAN.md`: tiêu chí kiểm thử
- `docs/IMPLEMENTATION.md`: mô tả từng file code
- `docs/REPORT_TEMPLATE.md`: khung báo cáo
- `docs/CONSENT_FORM.md`: mẫu giấy đồng ý thu âm
- `hardware/`, `firmware/`: phần của Thái (ĐTVT)

Ngoài phạm vi 14 ngày: CNN, nghe liên tục, wake word, chạy model trên vi điều khiển. Repo chưa chọn license.
