<#
.SYNOPSIS
PC C Engine DLL Build Script

.DESCRIPTION
This script builds the core_engine_win.dll for the PC (Windows) simulator using gcc.
#>
$ErrorActionPreference = "Stop"

# Ensure we are in the project root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$projectRoot = Resolve-Path (Join-Path $scriptDir "..")
Set-Location $projectRoot

# Create build directory
if (-not (Test-Path "build")) {
    New-Item -ItemType Directory -Path "build" | Out-Null
}

Write-Host "Building core_engine.dll..."
gcc -shared -o build/core_engine_win.dll -fPIC c_modules/core/engine_render.c c_modules/core/engine_types.c c_modules/core/sound_synth.c -I c_modules/core -O3 -Wall

if ($LASTEXITCODE -eq 0) {
    Write-Host "Successfully built build/core_engine.dll" -ForegroundColor Green
} else {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}
