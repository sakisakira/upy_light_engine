param(
    [string]$EmsdkDir = ".\emsdk"
)

Write-Host "Installing Emscripten SDK..."

if (-not (Test-Path $EmsdkDir)) {
    Write-Host "Cloning emsdk repository..."
    git clone https://github.com/emscripten-core/emsdk.git $EmsdkDir
} else {
    Write-Host "emsdk directory already exists, pulling latest..."
    cd $EmsdkDir
    git pull
    cd ..
}

cd $EmsdkDir

Write-Host "Installing latest emsdk tools (this may take several minutes)..."
.\emsdk.bat install latest

Write-Host "Activating latest emsdk tools..."
.\emsdk.bat activate latest

Write-Host "Emscripten installation complete!"
Write-Host "Note: To use emcc in your PowerShell session, you must run '.\emsdk\emsdk_env.bat'"
cd ..
