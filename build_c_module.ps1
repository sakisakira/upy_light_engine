<#
.SYNOPSIS
MicroPython Cモジュール ビルドスクリプト

.DESCRIPTION
Dockerコンテナを利用して、ローカル環境を汚さずにCモジュールやファームウェアをビルドします。
事前に Docker Desktop などが起動している必要があります。
#>

$ErrorActionPreference = "Stop"

$IMAGE_NAME = "upy_light_engine_builder"
$WORKSPACE_DIR = $PWD

Write-Host "========== Docker Build Environment for MicroPython C Modules =========="

# 1. Dockerイメージの存在確認とビルド
$imageExists = docker images -q $IMAGE_NAME
if (-not $imageExists) {
    Write-Host "[INFO] Dockerイメージ '$IMAGE_NAME' が見つかりません。新しくビルドします..."
    docker build -t $IMAGE_NAME .
    if ($LASTEXITCODE -ne 0) {
        Write-Error "[ERROR] Dockerイメージのビルドに失敗しました。"
        exit $LASTEXITCODE
    }
    Write-Host "[INFO] Dockerイメージのビルドが完了しました。"
} else {
    Write-Host "[INFO] 既存のDockerイメージ '$IMAGE_NAME' を使用します。"
}

# 2. コンテナ内でビルドを実行
Write-Host "[INFO] コンテナ内でビルド処理を開始します..."

# 実行するコマンド（mpy-crossのビルドなど、必要に応じて書き換えてください）
$BUILD_COMMAND = @"
echo '--- mpy-cross のビルド ---';
make -C micropython/mpy-cross;
echo '--- Cモジュールのビルド ---';
make -C micropython/ports/esp32 BOARD=ESP32_GENERIC_S3 submodules;
make -C micropython/ports/esp32 USER_C_MODULES=/workspace/c_modules/sound_engine/micropython.cmake BOARD=ESP32_GENERIC_S3;
"@

docker run --rm -v "${WORKSPACE_DIR}:/workspace" -w /workspace $IMAGE_NAME bash -c $BUILD_COMMAND

if ($LASTEXITCODE -eq 0) {
    Write-Host "========== ビルドが正常に完了しました！ =========="
} else {
    Write-Host "========== [ERROR] ビルド中にエラーが発生しました =========="
}
