<#
.SYNOPSIS
Cleans up the Cardputer Adv filesystem.

.DESCRIPTION
Connects via mpremote and deletes all user files and directories recursively.
#>
param(
    [string]$Port = ""
)

# Cardputer Adv のファイルシステム内をクリーンアップするスクリプト

$mpremote_args = @()
if ($Port -ne "") {
    $mpremote_args += "connect"
    $mpremote_args += $Port
}

Write-Host "Cleaning up Cardputer Adv filesystem..."

# デバイス上の再帰削除スクリプト（Python）をワンライナーで実行します
# フラッシュ上のすべてのファイルとディレクトリを削除します（システムに必要な隠し領域を除く）
$clean_script = @"
import os
def rm(d):
    try:
        for f in os.ilistdir(d):
            p = d + '/' + f[0] if d else f[0]
            if f[1] == 0x4000: # Directory
                rm(p)
                try: os.rmdir(p)
                except: pass
            else:
                try: os.remove(p)
                except: pass
    except: pass
rm('')
"@

mpremote @mpremote_args exec $clean_script

Write-Host "Cleanup complete! The device is now empty."
