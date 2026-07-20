param (
    [string]$Port = "COM4"
)

$ErrorActionPreference = "Stop"

Write-Host "Flashing MicroPython firmware to Cardputer on port $Port ..."
python -m esptool --chip esp32s3 -b 460800 --before default_reset --after hard_reset -p $Port write_flash --flash_mode dio --flash_size 4MB --flash_freq 80m 0x0 .\micropython\ports\esp32\build-ESP32_GENERIC_S3\bootloader\bootloader.bin 0x8000 .\micropython\ports\esp32\build-ESP32_GENERIC_S3\partition_table\partition-table.bin 0x10000 .\micropython\ports\esp32\build-ESP32_GENERIC_S3\micropython.bin

Write-Host "Done!"
