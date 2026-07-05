param ()

$script_dir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$project_root = Split-Path -Parent $script_dir

$emsdk_env = Join-Path $project_root "emsdk\emsdk_env.ps1"
if (Test-Path $emsdk_env) {
    & $emsdk_env
} else {
    Write-Host "Warning: emsdk not found at $emsdk_env. Assuming emcc is in PATH."
}

$build_dir = Join-Path $project_root "build"
if (-Not (Test-Path $build_dir)) {
    New-Item -ItemType Directory -Path $build_dir | Out-Null
}

# Compile as a side module so Pyodide can load it via ctypes
$out_file = Join-Path $build_dir "core_engine.so"

Write-Host "Building WASM side module ($out_file)..."
emcc c_modules/core/engine_render.c c_modules/core/engine_types.c -s SIDE_MODULE=1 -O3 -o $out_file

if ($LASTEXITCODE -eq 0) {
    Write-Host "WASM Build successful." -ForegroundColor Green
} else {
    Write-Host "WASM Build failed." -ForegroundColor Red
}
