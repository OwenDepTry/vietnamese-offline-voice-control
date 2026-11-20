# Build a Windows folder app: dist\VoiceControl\VoiceControl.exe
# Run from the repository root:  powershell -ExecutionPolicy Bypass -File packaging\build_exe.ps1
# Chưa kiểm chứng trên Windows thật: nếu thiếu module khi chạy exe, thêm --hidden-import tương ứng.
$ErrorActionPreference = "Stop"
$py = ".\.venv\Scripts\python.exe"
& $py -m pip install "pyinstaller>=6,<7"
& $py -m PyInstaller --noconfirm --clean --onedir --name VoiceControl `
    --paths . `
    --add-data "configs;configs" `
    --hidden-import sklearn.linear_model `
    --hidden-import sklearn.svm `
    --hidden-import sklearn.calibration `
    --hidden-import sklearn.neural_network `
    --hidden-import sklearn.preprocessing `
    --hidden-import sklearn.pipeline `
    --collect-all sounddevice `
    packaging\launch_gui.py
if (Test-Path models\baseline.joblib) {
    New-Item -ItemType Directory -Force dist\VoiceControl\models | Out-Null
    Copy-Item models\baseline.joblib dist\VoiceControl\models\
    Write-Host "Copied models\baseline.joblib (exe loads it automatically)."
} else {
    Write-Host "No models\baseline.joblib yet: the exe will start in button-only mode."
}
Write-Host "Done: dist\VoiceControl\VoiceControl.exe  (zip the whole dist\VoiceControl folder to share)"
