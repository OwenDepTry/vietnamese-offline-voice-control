# Notebooks

Notebook dùng để **nhìn, nghe và giải thích** dữ liệu và kết quả. Toàn bộ logic nằm trong `app/` và `ml/`, notebook chỉ gọi lại các hàm đó (giống các lệnh `python -m ml...`), nên kết quả hai bên luôn khớp và vẫn được unittest kiểm tra.

| Notebook | Nội dung | Cần gì |
|---|---|---|
| 01_kham_pha_du_lieu | Số mẫu theo phiên, file nên nghe lại (nghe ngay), dạng sóng/phổ tần, thời điểm bắt đầu nói, PCA đặc trưng | `data/manifest.csv` |
| 02_huan_luyen | Chia tập, so sánh cấu hình trên validation, train, đường chọn ngưỡng, learning curve, lỗi trên validation | ≥ 3 phiên đủ 6 nhãn (vd. s01, s02, s03) |
| 03_danh_gia | Chấm test **một lần**, confusion matrix, nghe mẫu sai, phân bố score, lượt thử trực tiếp và độ trễ | model từ notebook 02 |
| 04_firmware_ao | Bảng hành vi giao thức serial, lỗi thiết bị, độ trễ — dùng firmware ảo, không cần board | không cần dữ liệu |

## Cài và mở

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-notebook.txt
.\.venv\Scripts\python.exe -m jupyter lab
```

Hoặc dùng VS Code: mở file `.ipynb`, chọn kernel là `.venv`. Mở notebook từ thư mục `notebooks/` hay thư mục gốc đều được (ô đầu tiên tự chuyển về thư mục gốc repo).

Chạy theo thứ tự từ trên xuống (*Run All*). Tham số nằm ở ô thứ hai của mỗi notebook (đường dẫn manifest, phiên validation/test, tên model…).

## Quy tắc

- **Xóa output trước khi commit** (*Edit → Clear All Outputs*): output chứa âm thanh giọng nói và đường dẫn trên máy bạn. `tests/test_notebooks.py` sẽ báo lỗi nếu notebook còn output.
- Notebook 02 không đọc tập test. Notebook 03 chỉ chấm test khi thư mục `EVAL_DIR` chưa có; chạy lại thì đọc kết quả cũ, để test không bị "nhìn" nhiều lần.
- Muốn thêm phân tích mới: viết hàm trong `ml/` (có test), rồi gọi từ notebook — tránh viết logic dài trực tiếp trong ô notebook.
