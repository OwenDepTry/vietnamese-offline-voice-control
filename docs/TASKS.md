# Phân công hai người

Phần code CNTT cho MVP đã có; xem IMPLEMENTATION.md. Các ô dưới đây theo dõi việc nhóm chạy và kiểm chứng bằng dữ liệu/phần cứng thật, chưa được đánh dấu hoàn thành. CNN và triển khai MCU để sau MVP. Tên thành viên ĐTVT sẽ bổ sung sau.

## Đạt — CNTT
- [ ] IT-01: Chốt nhãn từ configs/commands.json và viết công cụ ghi âm WAV mono 16 kHz PCM16. Hoàn thành khi nghe lại được và metadata đúng.
- [ ] IT-02: Tạo manifest gồm path,speaker_id,session_id,label,split,noise_condition,distance_m; lưu thông tin đồng ý thu âm riêng, không công khai danh tính.
- [ ] IT-03: Chia train/validation/test theo người nói trước augmentation; kiểm tra không trùng người và bản ghi giữa các tập.
- [ ] IT-04: Tiền xử lý nhất quán; chốt chiều dài cửa sổ, padding/cropping, chuẩn hóa và mel/MFCC. Mọi tham số học từ dữ liệu chỉ fit trên train.
- [ ] IT-05: Baseline đơn giản (MFCC + bộ phân loại) rồi CNN nhỏ; so sánh cùng tập đánh giá. Không bắt buộc DL tốt hơn mới chấp nhận kết quả.
- [ ] IT-06: Tối ưu ngưỡng từ chối trên validation; kiểm thử unknown/silence. Không mặc định softmax cao là chắc chắn đúng.
- [ ] IT-07: App nhấn để nói, suy luận offline, gửi lệnh và hiển thị ACK/ERR/timeout. Có chế độ gõ lệnh để tích hợp trước AI.
- [ ] IT-08: Viết hướng dẫn môi trường và khóa phiên bản thư viện sau khi baseline chạy được.

## Thành viên 2 — Điện tử Viễn thông
- [ ] EE-01: Chốt board, nguồn, LED, quạt DC và linh kiện điều khiển; điền hardware/BOM.csv. Kiểm tra điện áp và dòng định mức.
- [ ] EE-02: Vẽ sơ đồ nối dây, xác định GPIO và trạng thái đầu ra lúc khởi động; giữ thiết bị tắt khi khởi động.
- [ ] EE-03: Firmware điều khiển LED/quạt bằng lệnh gõ tay qua serial, không chờ AI.
- [ ] EE-04: Parser theo docs/PROTOCOL.md; từ chối lệnh sai, giới hạn buffer và phản hồi theo request id.
- [ ] EE-05: Kiểm tra mạch driver, nguồn, nhiễu từ quạt, chạy liên tục và khởi động lại.
- [ ] EE-06: Ghi ảnh mạch, sơ đồ chân, hướng dẫn nạp firmware và bảng kết quả đo.
- [ ] EE-07 (sau MVP): Micro gắn thiết bị, I2S và bộ đệm; chỉ triển khai khi thống nhất kiến trúc chuyển AI xuống thiết bị.

## Cả hai
- [ ] BOTH-01: Chốt giao thức, nhãn, phần cứng và tiêu chí chấp nhận trước khi viết hai phần độc lập.
- [ ] BOTH-02: Chạy chuỗi gõ lệnh → serial → thiết bị → phản hồi.
- [ ] BOTH-03: Thu dữ liệu có sự đồng ý của người nói; đa dạng người, phiên thu và môi trường.
- [ ] BOTH-04: Ghép nhận diện với điều khiển, kiểm tra lời ngoài tập và lỗi kết nối.
- [ ] BOTH-05: Đánh giá người nói mới, khoảng cách, tiếng ồn và độ trễ end-to-end.
- [ ] BOTH-06: Hoàn thiện README, báo cáo, video demo offline; ghi rõ đóng góp mỗi người.

## Thứ tự phụ thuộc
IT-01/02 và EE-01/02 có thể làm đồng thời. BOTH-01 phải xong trước IT-07 và EE-04. BOTH-02 không phụ thuộc mô hình. BOTH-04 cần IT-05/06/07 và EE-03/04. BOTH-05 chỉ bắt đầu sau khi đóng băng cấu hình đánh giá.
