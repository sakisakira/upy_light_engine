# Cardputer-Adv オーディオ (ES8311) 技術仕様と実装ガイド

## 1. ハードウェア構成
M5Stack Cardputer-Adv のオーディオ出力は、以下の2つのチップを組み合わせて構成されています。
1. **ES8311**: I2C制御・I2S入力のオーディオコーデック（DAC）チップ
2. **NS4150B**: ES8311のアナログ出力を増幅し、内蔵スピーカーを駆動するD級アンプチップ

**注意点**: アンプ（NS4150B）の電源を直接制御するGPIOピン（`AMP_EN`）は存在しません。音声の出力オン・オフは、ES8311のI2Cレジスタ経由で行われます。

## 2. ピンアサイン
| 機能 | ESP32-S3 GPIO | 備考 |
| :--- | :--- | :--- |
| **I2S BCLK (SCK)** | GPIO 41 | ビットクロック |
| **I2S LRCK (WS)** | GPIO 43 | ワードセレクト（L/Rクロック） |
| **I2S DATA (SD)** | GPIO 42 | オーディオデータ出力 |
| **I2C SDA** | GPIO 8 | ES8311制御用（アドレス: `0x18`） |
| **I2C SCL** | GPIO 9 | ES8311制御用 |

## 3. 必須の初期化手順
ES8311から音を鳴らすには、**I2Sのクロックが供給されている状態で**、I2C経由で特定のレジスタ初期化シーケンスを送信する必要があります。特に、MCLK（マスタークロック）をBCLKから生成するための設定が必須です。

### ES8311 レジスタ設定値（M5Unified準拠）
```python
def init_es8311(i2c):
    # アドレスは 0x18
    # 0x00: RESET / CSM POWER ON
    i2c.writeto_mem(0x18, 0x00, b'\x80')
    
    # 0x01: CLOCK_MANAGER / MCLK=BCLK (重要: MCLKピンがないためBCLKから生成)
    i2c.writeto_mem(0x18, 0x01, b'\xB5')
    
    # 0x02: CLOCK_MANAGER / MULT_PRE=3
    i2c.writeto_mem(0x18, 0x02, b'\x18')
    
    # 0x0D: SYSTEM / アナログ回路のパワーアップ
    i2c.writeto_mem(0x18, 0x0D, b'\x01')
    
    # 0x12: SYSTEM / DACのパワーアップ
    i2c.writeto_mem(0x18, 0x12, b'\x00')
    
    # 0x13: SYSTEM / ヘッドフォンドライブ（アンプ出力）の有効化
    i2c.writeto_mem(0x18, 0x13, b'\x10')
    
    # 0x32: DAC / DACデジタルボリューム設定 (0xBF = 0dB 最大)
    i2c.writeto_mem(0x18, 0x32, b'\xBF')
    
    # 0x37: DAC / DACイコライザーのバイパス
    i2c.writeto_mem(0x18, 0x37, b'\x08')
```

## 4. MicroPython実装例 (Bare I2S)
ファームウェアに依存せず、標準の MicroPython (`machine.I2S`, `machine.I2C`) だけで音を鳴らす最小コードです。

```python
import machine
import time
import struct
import math

# 1. I2Cの初期化
i2c = machine.I2C(1, sda=machine.Pin(8), scl=machine.Pin(9), freq=100000)

# 2. ES8311の初期化 (前述の init_es8311 関数を使用)
init_es8311(i2c)

# 3. I2Sの初期化
audio_out = machine.I2S(
    1,
    sck=machine.Pin(41),
    ws=machine.Pin(43),
    sd=machine.Pin(42),
    mode=machine.I2S.TX,
    bits=16,
    format=machine.I2S.STEREO,
    rate=44100,
    ibuf=4096
)

# 4. 音声データの生成と再生 (例: 440Hzサイン波)
samples = bytearray()
for i in range(100):
    val = int(8000 * math.sin(2 * math.pi * i / 100))
    samples += struct.pack("<hh", val, val) # 16bit Stereo L/R

# 2秒間再生
start = time.ticks_ms()
while time.ticks_diff(time.ticks_ms(), start) < 2000:
    audio_out.write(samples)

audio_out.deinit()
```
