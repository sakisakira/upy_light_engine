# MicroPythonサブモジュールへのパッチ適用スクリプト

$patchFile = "..\patches\micropython_esp32_build_fixes.patch"
$submoduleDir = "micropython"

Write-Host "Applying ESP32 build fixes to micropython submodule..."

if (-not (Test-Path $submoduleDir)) {
    Write-Host "Error: Submodule directory '$submoduleDir' not found."
    exit 1
}

if (-not (Test-Path "patches\micropython_esp32_build_fixes.patch")) {
    Write-Host "Error: Patch file not found."
    exit 1
}

# Apply the patch using git apply
cd $submoduleDir
git apply --check $patchFile
if ($LASTEXITCODE -eq 0) {
    git apply $patchFile
    Write-Host "Patch applied successfully!"
} else {
    Write-Host "Patch could not be applied. It may already be applied or the submodule is in a conflicting state."
}
cd ..
