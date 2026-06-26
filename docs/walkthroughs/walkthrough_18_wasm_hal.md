# Web (WASM) HAL 実装完了

TODOにありました「Web (WASM) 対応」が完了しました！
これにより、PCやデバイス向けに書かれた `main.py` などのゲームコードを一切変更することなく、そのままブラウザ上で動作させることができるようになりました。

## 変更内容サマリー

* **`engine/hal/framebuffer_wasm.py`**:
  * ブラウザの `<canvas>` を利用した描画バックエンドを作成しました。
  * Python側での重いピクセル処理を避けるため、16bit（RGB565）から32bit（RGBA）への変換とCanvasへの転送は、JS関数側に処理を委譲して高速化しています。
  * `while True:` ループの代わりに `window.requestAnimationFrame` を使ってゲームループを非同期化し、ブラウザがフリーズしない仕組みになっています。
* **`engine/hal/input_wasm.py`**:
  * ブラウザの `keydown` / `keyup` イベントをフックし、矢印キーやZ/X/C/VキーをCardputerのボタン入力としてマップしています。
* **`engine/hal/sound_wasm.py`**:
  * ブラウザの **Web Audio API** (`AudioContext`) を利用したサウンド再生バックエンドを作成しました。
  * MMLで定義された音符を、JSの `OscillatorNode`（矩形波）に変換して鳴らします。ポップノイズ（ぷつっという音）を防ぐための微小なフェード処理も入れています。
* **`scripts/web/index.html`**:
  * **PyScript** を利用してブラウザ内でPython環境（Pyodide）を立ち上げ、仮想ファイルシステム上にゲームアセットやエンジンコードを展開して `main.py` を実行するWebページ（ランナー）を作成しました。

---

## 🚀 ブラウザでのテスト方法

お手元のPCでローカルサーバーを立ち上げるだけで、すぐにブラウザからゲームを遊べます！

1. ターミナルで、プロジェクトのルートディレクトリ（`upy_light_engine`）に移動します。
2. 以下のコマンドを実行して、ローカルHTTPサーバーを起動します。
   ```powershell
   python -m http.server 8000
   ```
3. Webブラウザ（ChromeやEdgeなど）を開き、以下のURLにアクセスします。
   **http://localhost:8000/scripts/web/index.html**
4. 初回は「Loading Game Engine (WASM)...」と表示され、PyScriptのランタイムがダウンロードされます（数秒〜十数秒かかります）。
5. 起動すると黒い画面（Canvas）が表示されます！
   * 画面をクリックしてフォーカスを当ててください。
   * **Zキー** (Button A) を押すと画面が赤くなり、**Xキー** (Button B) を押すと青くなります。
   * BGM（MMLのスーパーマリオテーマ）が鳴るはずです！（※Web Audio APIの仕様上、ブラウザによっては画面をクリックするまで音が鳴らない場合があります）

---

## 🐛 WASM環境特有のデバッグと修正履歴

開発過程で、ブラウザおよびPyodide環境特有のいくつかの問題が発生しましたが、すべて修正済みです。

1. **`__name__ == "__main__"` が呼ばれない問題**
   * **原因**: `index.html` 内で `<py-script>` から `import main` として実行しようとしたところ、Pythonの仕様上メインモジュールとして認識されず、ゲームループが開始しませんでした。
   * **解決策**: `import runpy; runpy.run_module("main", run_name="__main__")` を使用することで解決しました。
2. **描画メソッド (`rect`, `blt` など) の欠落**
   * **原因**: `framebuffer_wasm.py` 実装時に一部の描画メソッドを実装し忘れたため、`AttributeError` が発生しました。
   * **解決策**: PC版 (`framebuffer_cpython.py`) の `Framebuffer` クラスが純粋なPythonの `bytearray` 操作で実装されていたため、そのメソッド群をごっそりWASM版に移植（再利用）することで解決しました。
3. **キー入力の定数名タイポ**
   * **原因**: `input_wasm.py` で `Button_LEFT` のように大文字で記述してしまい `NameError` が発生しました。
   * **解決策**: `engine/constants.py` の定義通り、キャメルケース (`Button_Left`) に修正しました。
4. **サウンドAPIのタプルアンパックエラー**
   * **原因**: MMLパーサーが `(周波数, 長さ)` のタプルを返すのに、`sound_wasm.py` 側で辞書型 (`note['freq']`) として取り出そうとしてエラーになりました。
   * **解決策**: 正しくタプルをアンパックするように修正しました。
5. **ブラウザのAutoplayブロックによる無音化**
   * **原因**: ブラウザの仕様で、ユーザー操作なしに音を鳴らすことが許可されておらず、Web Audio APIが `suspended` 状態のままブロックされていました。
   * **解決策**: グローバルに `keydown`, `mousedown` イベントリスナーを追加し、ユーザーがゲーム操作をした瞬間に `AudioContext.resume()` を呼び出してロックを解除する仕組みを導入しました。
