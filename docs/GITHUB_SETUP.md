# Làm việc với GitHub

Repo: https://github.com/OwenDepTry/vietnamese-offline-voice-control

## Lần đầu (bạn ĐTVT)

1. Đạt mời vào repo qua Settings > Collaborators.
2. Clone về và cài môi trường như README.

```powershell
git clone https://github.com/OwenDepTry/vietnamese-offline-voice-control.git
```

## Mỗi lần làm việc

Làm trên nhánh riêng rồi mở Pull Request, để CI chạy test trước khi gộp vào `main`:

```powershell
git checkout main
git pull --ff-only
git checkout -b ten-nhanh            # ví dụ: firmware-parser, recorder-preroll
# ... sửa code ...
git add -A
git ls-files | Select-String "\.wav|data/manifest.csv|\.venv|\.joblib|events.jsonl"   # phải không in ra gì
git commit -m "mô tả ngắn"
git push -u origin ten-nhanh
```

Lên GitHub bấm "Compare & pull request", điền mẫu PR, đợi CI xanh thì merge. Mỗi PR nên nhỏ, làm xong một việc. Không cần giữ nhánh cá nhân lâu dài.

## Không commit

- File thu âm, `data/manifest*.csv`, giấy đồng ý (đã có trong `.gitignore`)
- `.venv`, model `.joblib`
- Notebook còn output (Clear All Outputs trước khi commit, test sẽ báo nếu quên)

## Thông tin repo

About: Offline Vietnamese voice command recognition for low-voltage device control, integrating machine learning, embedded firmware, and serial communication.

Topics: vietnamese, speech-recognition, keyword-spotting, machine-learning, embedded-systems, offline, serial-communication.
