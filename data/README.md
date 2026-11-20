# Dữ liệu

Thư mục này không đưa file âm thanh lên GitHub. Chỉ thu giọng người khác khi họ đồng ý, và không đưa file của họ lên mạng. Ai ứng với mã nào thì tự ghi nhớ hoặc ghi ở ngoài repo. File gốc nằm trong `raw/<người>/<phiên>/`, dữ liệu đã xử lý (nếu có) để trong `processed/`.

`manifest.example.csv` là mẫu các cột của manifest. File `manifest.csv` thật do `app.recorder` tự tạo.

Mục tiêu pilot ban đầu là khoảng 10 người, mỗi người 4 lệnh x 15 lượt, thu nhiều phiên, cộng thêm silence, tiếng ồn và câu ngoài tập. Số này chỉ để bắt đầu, chưa đủ để kết luận model nhận được người lạ.

Khi đủ người thì chia theo người nói, ví dụ 6/2/2 người cho train/validation/test. Nhóm ít người thì chia theo phiên (xem README), nhưng một phiên không được nằm ở hai tập. Không dùng test để chọn model hay ngưỡng. Augmentation chỉ áp dụng cho train.

Nên ghi lại micro dùng để thu, vì đổi micro có thể làm kết quả khác đi nhiều.
