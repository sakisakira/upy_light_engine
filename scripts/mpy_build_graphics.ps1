<#
.SYNOPSIS
Builds the graphics_engine.mpy dynamic native module using Docker.
#>
$ErrorActionPreference = "Stop"
$IMAGE_NAME = "upy_light_engine_builder"
$WORKSPACE_DIR = $PWD

Write-Host "========== Building graphics_engine.mpy =========="

$BUILD_COMMAND = @"
echo '--- mpy-cross build ---';
make -C micropython/mpy-cross;
echo '--- graphics_engine.mpy build ---';
make -C c_modules/graphics_engine;
cp c_modules/graphics_engine/graphics_engine.mpy ./;
"@

docker run --rm -v "${WORKSPACE_DIR}:/workspace" -w /workspace $IMAGE_NAME bash -c $BUILD_COMMAND

if ($LASTEXITCODE -eq 0) {
    Write-Host "========== Build Completed Successfully! =========="
} else {
    Write-Host "========== [ERROR] Build Failed =========="
}
