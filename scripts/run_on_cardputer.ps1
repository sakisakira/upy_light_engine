param(
    [string]$Port = ""
)

$mpremote_args = @()
if ($Port -ne "") {
    $mpremote_args += "connect"
    $mpremote_args += $Port
}

Write-Host "Running main.py on Cardputer Adv..."
mpremote @mpremote_args run main.py
