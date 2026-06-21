# ST7789 SPIディスプレイ出力の実装

記録日時: 2026-06-21 09:36

Cardputer ADVのLCD（ST7789・240x135）に、`framebuffer`（RAM）の内容を実際に表示するためのドライバを実装します。

## 背景と調査結果
実機で `help('modules')` を確認した結果、C言語で書かれた専用の `st7789` モジュールは組み込まれていませんでした（標準のMicroPythonファームウェアが焼かれているため）。
そのため、**純粋なPython（pure Python）でSPI通信を行う、超軽量・高速な専用ドライバ** を新しく作成します。

## Open Questions / User Review Required
1. **ピン配置の確認**: 以下のピン配置（Cardputer標準）で実装を進めようと思いますが、Cardputer ADVでの変更や間違いはないでしょうか？
   - MOSI: 35, SCLK: 36
   - CS: 37, DC: 34, RST: 33, BL(バックライト): 38
   - MISO: なし（送信専用）

## Proposed Changes

### [NEW] `hal/st7789.py`
ST7789の初期化マジックコマンド群と、全画面バッファをSPIで一括転送する `show()` メソッドを持つドライバクラスを作成します。
* **転送方式の最適化**: 1ピクセルずつ送るのではなく、`spi.write(buffer)` を用いて64KBのバイト配列を一気にCレベルでDMA/SPI転送させることで、Pythonのループオーバーヘッドをゼロにし、60FPSを目指します。

### [MODIFY] `hal/framebuffer_micropython.py`
`run()` 関数内でこの `st7789` ドライバを初期化し、現在コメントアウトされている「画面転送」の部分で `display.show(screen.buffer)` を呼び出します。

```python
    import hal.st7789 as st7789
    display = st7789.ST7789()
    
    while True:
        # ... update(), draw()
        display.show(screen.buffer)
```

## Verification Plan
1. 修正後、実機に `hal/st7789.py` などをコピーして `main.py` を実行する。
2. Cardputerの画面に、ついにテストスプライトやテキストが表示されることを確認する。
