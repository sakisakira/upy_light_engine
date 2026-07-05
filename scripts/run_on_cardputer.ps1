param(
    [string]$Port = ""
)

$mpremote_args = @()
if ($Port -ne "") {
    $mpremote_args += "connect"
    $mpremote_args += $Port
}

Write-Host "Running main.py on Cardputer Adv..."
$mpremote_args += "run"
$mpremote_args += "--no-follow"
$mpremote_args += "main.py"
mpremote @mpremote_args

Write-Host "Reconnecting to stream logs... (Press Ctrl+] to exit)"
Start-Sleep -Seconds 2
mpremote connect $Port
