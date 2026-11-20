# Cách đo thực nghiệm

Mỗi lượt thử được ghi vào `results/measurements.csv` (khi bật chế độ thử nghiệm trong GUI) và `results/events.jsonl` (app tự ghi). Tổng hợp bằng `python -m ml.trial_report`. Ghi hết mọi lượt, kể cả lượt sai và lượt bị lỗi, không xóa bớt.

## Đặt tên điều kiện

Ô "Điều kiện" trong GUI ghi theo dạng `thiết bị-mạng-môi trường-khoảng cách`:

- thiết bị: `fake` (firmware ảo), `board` (board thật), `sim` (mô phỏng)
- mạng: `online` hoặc `offline` (đã tắt Wi-Fi và rút dây mạng)
- môi trường: `quiet`, `fan` (có quạt chạy gần micro), `talk` (có người nói chuyện)
- khoảng cách: `1m`, `2m`

Ví dụ `fake-offline-quiet-1m`. `ml.trial_report` sẽ tách số liệu theo đúng tên này nên nhớ ghi thống nhất.

## 1. Độ trễ phần mềm

Cái này làm được ngay khi có model, chưa cần board.

1. Mở GUI với firmware ảo:
   ```powershell
   python -m app.gui --model models/<tên model>.joblib --port fake
   ```
2. Tick "Ghi lượt thử", người nói `p01`, điều kiện `fake-online-quiet-1m`.
3. Nói 30 lượt: mỗi lệnh 5 lượt, unknown 5 lượt, silence 5 lượt. Trước mỗi lượt chọn đúng ô "Định nói" rồi mới bấm Space. Nên đảo thứ tự, đừng nói một lệnh 5 lần liền.
4. Chạy `python -m ml.trial_report`, lấy cột trễ median và p95.

Firmware ảo trả lời sau khoảng 5 ms, nên con số đo được chủ yếu là thời gian tính đặc trưng và phân loại. Nhớ ghi cấu hình máy (CPU, RAM, Windows, Python) vào báo cáo.

## 2. Chạy offline

1. Tắt Wi-Fi, rút dây mạng, mở thử trình duyệt cho chắc là không vào được mạng.
2. Làm lại mục 1 với điều kiện `fake-offline-quiet-1m` (khoảng 12 lượt là đủ).
3. Quay màn hình (Win + G hoặc OBS) lúc biểu tượng mạng đang tắt, nói lệnh và GUI vẫn nhận được. Đoạn này dùng cho video demo luôn.

Ngoài ra `tests/test_offline.py` chạy cả chuỗi từ chia tập, train, đánh giá tới nhận lệnh và gửi lệnh trong khi chặn hết kết nối mạng.

## 3. Thử với môi trường khác

Sau khi có baseline, làm lại mục 1 (30 lượt mỗi điều kiện) với `fake-offline-fan-1m`, `fake-offline-quiet-2m`, `fake-offline-talk-1m`. So sánh các cột đúng, bỏ sót, kích hoạt nhầm giữa các điều kiện. Lưu ý nếu người nói vẫn là mình thì đây là giọng đã có trong train.

## 4. Với board thật

1. Board phải chạy `python -m app.conformance --port COMx` đạt hết trước (xem `docs/INTEGRATION.md`).
2. Mở GUI với `--port COMx`, điều kiện bắt đầu bằng `board-`.
3. Sau mỗi lượt nhìn đèn/quạt rồi bấm Có (thiết bị làm đúng, hoặc đứng yên khi nói unknown/silence) hoặc Không. Cột "vật lý OK" lấy từ chỗ này, không tính theo ACK.
4. Thử thêm mấy tình huống lỗi trong `docs/TEST_PLAN.md`: rút USB lúc đang chạy, bấm reset board, nói khi board chưa sẵn sàng. Ghi kết quả vào cột ghi chú.

## Đưa vào báo cáo

- Bảng thử trực tiếp và độ trễ median/p95: lấy từ `python -m ml.trial_report`, theo từng điều kiện.
- Bằng chứng chạy offline: video ở mục 2 và `tests/test_offline.py`.
- Tỉ lệ thiết bị chạy đúng: cột "vật lý OK", chỉ tính các điều kiện `board-`.
