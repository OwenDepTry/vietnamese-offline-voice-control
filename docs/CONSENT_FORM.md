# Giấy đồng ý tham gia thu âm giọng nói

*Nhóm sửa các chỗ trong [ngoặc vuông] trước khi dùng. Nếu trường hoặc khoa có quy định riêng về thu thập dữ liệu cá nhân thì làm theo quy định đó.*

---

**Dự án:** Điều khiển thiết bị bằng giọng nói tiếng Việt chạy offline
**Học phần:** [tên học phần], [Khoa], [Trường]
**Người phụ trách dữ liệu:** [họ tên, email hoặc số điện thoại]
**Phiên bản mẫu:** 1.0

### 1. Bạn sẽ làm gì

Bạn sẽ đọc 4 câu lệnh ngắn ("bật đèn", "tắt đèn", "bật quạt", "tắt quạt"), đọc thêm vài câu ngắn bất kỳ không phải lệnh, và giữ im lặng vài giây để thu tiếng nền. Mỗi lần thu dài 2 giây, tổng cộng khoảng [15-30] phút và có thể chia ra nhiều buổi. Bạn được nghe lại, thu lại hoặc bỏ bất kỳ bản thu nào.

### 2. Nhóm thu những gì

- File âm thanh giọng nói của bạn và tiếng nền trong phòng.
- Thông tin kèm theo: mã ẩn danh (ví dụ `p02`), mã phiên thu, câu đã đọc, điều kiện thu (yên tĩnh hay có quạt), khoảng cách tới micro.

Nhóm không ghi tên, ảnh, vị trí hay thông tin cá nhân nào khác vào dữ liệu. Chỉ có sổ đồng ý (mục 5) là ghi tên bạn cạnh mã ẩn danh.

### 3. Dữ liệu dùng để làm gì

Dữ liệu chỉ dùng để train và đánh giá model nhận lệnh giọng nói của dự án, và để trình bày kết quả tổng hợp (độ chính xác, biểu đồ) trong báo cáo, buổi thuyết trình và video demo của học phần.

Nhóm không dùng dữ liệu để kinh doanh, không đưa cho người ngoài, và không dùng để nhận ra bạn là ai.

### 4. Lưu ở đâu, ai xem được

- File âm thanh lưu trên máy của thành viên nhóm [và thư mục chia sẻ riêng tư: ghi tên dịch vụ], không đưa lên GitHub hay mạng công khai. Repo của nhóm chỉ có mã nguồn.
- Chỉ thành viên nhóm [và giảng viên hướng dẫn nếu cần chấm] được xem.
- Nhóm xóa dữ liệu [trong vòng 30 ngày sau khi kết thúc học phần / vào ngày ...], trừ khi bạn đồng ý cho giữ lâu hơn ở mục 6.
- Giọng của bạn không được phát công khai (kể cả trong video demo) nếu bạn không đánh dấu ở mục 6.

### 5. Quyền của bạn

Tham gia là tự nguyện. Bạn có thể rút lại đồng ý bất cứ lúc nào mà không cần giải thích, chỉ cần báo cho người phụ trách ở trên. Khi đó nhóm sẽ xóa các bản thu mang mã của bạn, và nếu kết quả đã tính trước đó có dùng dữ liệu của bạn thì nhóm sẽ ghi chú trong báo cáo. Bạn cũng có thể xin nghe lại hoặc nhận bản sao các bản thu của mình.

### 6. Tùy chọn (đánh dấu nếu đồng ý)

- [ ] Cho phép phát bản thu giọng của tôi trong buổi thuyết trình hoặc video demo của học phần.
- [ ] Cho phép nhóm giữ dữ liệu sau khi học phần kết thúc để làm tiếp dự án (không công khai), tối đa tới ngày [...].

### 7. Xác nhận

Tôi đã đọc, đã được giải đáp thắc mắc, và đồng ý tham gia thu âm.

| | Người tham gia | Người thu (nhóm) |
|---|---|---|
| Họ tên | | |
| Mã ẩn danh | `p__` | |
| Chữ ký | | |
| Ngày | | |

---

## Ghi chú cho nhóm (không in phần này)

1. Gửi mẫu trước, trả lời thắc mắc, nhận lại bản đã ký (giấy, ảnh chụp, PDF ký tay, hoặc email ghi "Tôi đồng ý" kèm nội dung mẫu). Xong bước này mới chạy `app.recorder ... --consent`.
2. Bản ký lưu ở ngoài repo, ví dụ thư mục riêng trên máy hoặc Drive cá nhân. Nếu lỡ để trong thư mục dự án thì để trong `consent/`, thư mục này đã có trong `.gitignore`.
3. Sổ đồng ý cũng giữ riêng, không commit. Dùng mẫu `docs/consent_log.template.csv`, mỗi người một dòng: mã ẩn danh, họ tên, ngày ký, phiên bản mẫu, các tùy chọn ở mục 6, ngày rút lại (nếu có).
4. Có người rút lại thì xóa thư mục `data/raw/<mã>/`, xóa các dòng của mã đó trong `data/manifest.csv`, chia tập và train lại, ghi ngày xóa vào sổ.
5. Người thu từ xa thì ký trước khi thu, gửi file qua kênh riêng chứ không gửi vào nhóm chat chung.
6. Một người chỉ dùng một mã cho mọi phiên, để lúc chia tập theo người không bị lẫn.
