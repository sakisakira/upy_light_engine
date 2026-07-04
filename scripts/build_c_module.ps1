<#
.SYNOPSIS
MicroPython C Module Build Script

.DESCRIPTION
Uses Docker container to build C modules and firmware without polluting local env.
#>

$ErrorActionPreference = "Stop"

$IMAGE_NAME = "upy_light_engine_builder"
$WORKSPACE_DIR = $PWD

Write-Host "========== Docker Build Environment for MicroPython C Modules =========="

$imageExists = docker images -q $IMAGE_NAME
if (-not $imageExists) {
    Write-Host "[INFO] Building Docker image '$IMAGE_NAME'..."
    docker build -t $IMAGE_NAME .
    if ($LASTEXITCODE -ne 0) {
        Write-Error "[ERROR] Docker build failed."
        exit $LASTEXITCODE
    }
    Write-Host "[INFO] Docker build complete."
} else {
    Write-Host "[INFO] Using existing Docker image '$IMAGE_NAME'."
}

Write-Host "[INFO] Starting build inside container..."

$BUILD_COMMAND = @"
echo '--- mpy-cross build ---';
make -C micropython/mpy-cross;
echo '--- C module build ---';
make -C micropython/ports/esp32 BOARD=ESP32_GENERIC_S3 submodules;
make -C micropython/ports/esp32 USER_C_MODULES=/workspace/c_modules/micropython.cmake BOARD=ESP32_GENERIC_S3;
"@

docker run --rm -v "${WORKSPACE_DIR}:/workspace" -w /workspace $IMAGE_NAME bash -c $BUILD_COMMAND

if ($LASTEXITCODE -eq 0) {
    Write-Host "========== Build Completed Successfully! =========="
} else {
    Write-Host "========== [ERROR] Build Failed =========="
}

