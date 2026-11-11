# Đưa khung repo lên GitHub

Gói này không tạo repo từ xa và chưa có lịch sử Git. Giải nén, mở terminal tại thư mục chứa README.md.

Tạo repo trống tên vietnamese-offline-voice-control trong tài khoản OwenDepTry. Không thêm README, .gitignore hay license tự động vì khung đã có file tương ứng (license sẽ chọn sau).

```powershell
git init -b main
git add .
git commit -m "chore: initialize project structure and two-person roadmap"
git remote add origin https://github.com/OwenDepTry/vietnamese-offline-voice-control.git
git push -u origin main
```

Nếu tên repo đã tồn tại, không ghi đè: chọn tên khác và sửa URL. Mời cộng tác viên qua Settings → Collaborators bằng tài khoản chính xác của họ.

Đạt tạo nhánh feat/audio-recorder. Người ĐTVT clone repo rồi tạo feat/serial-control. Mỗi người làm PR nhỏ vào main; trước nhánh mới cập nhật main bằng git pull --ff-only. Không cần duy trì hai nhánh cá nhân dài hạn.

About đề xuất: Offline Vietnamese voice command recognition for low-voltage device control, integrating machine learning, embedded firmware, and serial communication.

Topics: vietnamese, speech-recognition, keyword-spotting, machine-learning, embedded-systems, offline, serial-communication.
