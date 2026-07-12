<#
.SYNOPSIS
WASM Engine Build Script

.DESCRIPTION
This script uses emcc to compile the core C engine and sound synthesizer into WebAssembly for browser execution.
#>
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
emcc c_modules/core/engine_render.c c_modules/core/engine_types.c c_modules/core/sound_synth.c -s SIDE_MODULE=1 -O3 -o $out_file

if ($LASTEXITCODE -eq 0) {
    Write-Host "WASM core_engine.so Build successful." -ForegroundColor Green
} else {
    Write-Host "WASM core_engine.so Build failed." -ForegroundColor Red
}

$sound_out_file = Join-Path $build_dir "sound_synth.wasm"
Write-Host "Building WASM sound_synth ($sound_out_file)..."
emcc c_modules/core/sound_synth.c -O3 -s STANDALONE_WASM=1 --no-entry -s EXPORTED_FUNCTIONS="['_sound_synth_init', '_sound_synth_set_channel', '_sound_synth_stop_all', '_sound_synth_render_wasm', '_sound_synth_get_wasm_buf_l', '_sound_synth_get_wasm_buf_r']" -o $sound_out_file

if ($LASTEXITCODE -eq 0) {
    Write-Host "WASM sound_synth Build successful." -ForegroundColor Green
} else {
    Write-Host "WASM sound_synth Build failed." -ForegroundColor Red
}
