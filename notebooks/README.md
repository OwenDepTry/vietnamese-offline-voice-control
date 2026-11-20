# Notebooks

Mấy notebook này dùng để xem, nghe và giải thích dữ liệu với kết quả. Phần xử lý vẫn nằm trong `app/` và `ml/`, notebook chỉ gọi lại, nên kết quả giống hệt khi chạy lệnh `python -m ml...`.

- `01_kham_pha_du_lieu`: số mẫu theo phiên, các file nên nghe lại (nghe luôn trong notebook), dạng sóng và phổ tần, thời điểm bắt đầu nói, PCA của đặc trưng. Chỉ cần có `data/manifest.csv`.
- `02_huan_luyen`: chia tập, so sánh cấu hình trên validation, train, chọn ngưỡng, learning curve, xem các mẫu đoán sai trên validation. Cần ít nhất 3 phiên đủ 6 nhãn.
- `03_danh_gia`: chấm test một lần, confusion matrix, nghe các mẫu sai, phân bố score, các lượt thử trực tiếp và độ trễ. Cần model từ notebook 02.
- `04_firmware_ao`: giao thức serial với firmware ảo (gửi gì thì nhận gì, khi lỗi thì sao, độ trễ). Không cần dữ liệu, có thể gửi cho bạn ĐTVT xem.

## Cài và mở

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-notebook.txt
.\.venv\Scripts\python.exe -m jupyter lab
```

Hoặc mở file `.ipynb` bằng VS Code và chọn kernel `.venv`. Mở từ thư mục `notebooks/` hay thư mục gốc đều được, ô đầu tiên sẽ tự chuyển về thư mục gốc của repo.

Chạy lần lượt từ trên xuống (Run All). Các tham số như đường dẫn manifest, phiên validation/test, tên model nằm ở ô thứ hai.

## Lưu ý

- Trước khi commit nhớ Clear All Outputs, vì output có chứa âm thanh giọng nói và đường dẫn trên máy. Nếu quên thì `tests/test_notebooks.py` sẽ báo lỗi.
- Notebook 02 không đọc tập test. Notebook 03 chỉ chấm test khi chưa có thư mục kết quả, chạy lại thì chỉ đọc kết quả cũ.
- Muốn thêm phân tích mới thì viết hàm trong `ml/` (có test) rồi gọi từ notebook, đừng viết logic dài trong ô notebook.
