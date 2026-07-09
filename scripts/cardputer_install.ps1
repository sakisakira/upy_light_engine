<#
.SYNOPSIS
Installs the engine and game files to the Cardputer Adv.

.DESCRIPTION
Copies the engine framework, assets (fonts/images), native modules, and main.py to the device.
#>
param(
    [string]$Port = ""
)

# Cardputer Adv へエンジン単体のテストファイル群をインストールするスクリプト

$mpremote_args = @()
if ($Port -ne "") {
    $mpremote_args += "connect"
    $mpremote_args += $Port
}

Write-Host "Installing upy_light_engine files to Cardputer Adv..."

# 1. エンジンのコピー
Write-Host "Copying engine..."
if (Test-Path ".\engine\__pycache__") { Remove-Item -Recurse -Force ".\engine\__pycache__" }
if (Test-Path ".\engine\hal\__pycache__") { Remove-Item -Recurse -Force ".\engine\hal\__pycache__" }
mpremote @mpremote_args cp -r .\engine :

# 2. フォントのコピー
Write-Host "Copying fonts..."
mpremote @mpremote_args fs mkdir :assets 2> $null
mpremote @mpremote_args fs mkdir :assets/fonts 2> $null
$font_files = Get-ChildItem -Path .\assets\fonts\*.afnt | Select-Object -ExpandProperty FullName
if ($font_files) {
    mpremote @mpremote_args cp $font_files :assets/fonts/
}

# 3. 画像とパレットのコピー
Write-Host "Copying images & palette..."
mpremote @mpremote_args fs mkdir :assets/images 2> $null
$img_files = Get-ChildItem -Path .\assets\images\* -Include *.uimg,*.bin | Select-Object -ExpandProperty FullName
if ($img_files) {
    mpremote @mpremote_args cp $img_files :assets/images/
}

# 4. ネイティブモジュール(.mpy)のコピー
Write-Host "Copying native modules (.mpy)..."
$mpy_files = Get-ChildItem -Path .\*.mpy -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
if ($mpy_files) {
    mpremote @mpremote_args cp $mpy_files :
}

# 5. main.py のコピー
Write-Host "Copying main.py..."
mpremote @mpremote_args cp .\main.py :

Write-Host ""
Write-Host "Installation Complete! You can now run main.py on the device."
