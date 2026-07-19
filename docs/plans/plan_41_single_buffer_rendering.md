# Plan 14: シングルバッファ化とFreeRTOSヒープの活用

## 目的
126.5KBのSRAMを占有しているダブルバッファを「シングルバッファ化（待機型DMA）」に変更し、約32.4KBのFreeRTOSヒープを解放する。
解放されたSRAM領域を、Python側の巨大なバッファ（ImageBufferManager等）の確保先として直接利用できるようにすることで、MicroPythonヒープの逼迫を劇的に改善する。

## 現状の課題と前提知識
1. **ダブルバッファが実質的に機能していない**:
   現在のエンジン (modlightengine.c) では、描画スレッド(Core 1)が「DisplayListからFramebufferへの描画」を行った後、「DMA転送が終わるまで待機」する直列処理になっています。そのため、2枚のFramebufferを用意しても並列化の恩恵を受けておらず、単に32.4KBのSRAMを無駄に占有している状態です。
2. **MicroPythonのヒープ仕様**:
   MicroPythonのヒープ（約141KB）は起動時にサイズが固定されるため、C層でFramebufferを1面減らしてFreeRTOSヒープが空いても、自動的にPythonの空き容量が増えるわけではありません。

## 解決策（実装アプローチ）

### Step 1: フレームバッファのシングルバッファ化
game/main.py および engine/hal/framebuffer_micropython.py を修正し、_c_fbs を2面から1面に減らします。
DMA転送中はどうせ描画スレッドが待機するため、ティアリング（画面の分断）は発生しません。これにより、直ちに **約32.4KB** のFreeRTOSヒープが解放されます。

### Step 2: Cモジュール側に malloc インターフェースを追加
解放されたFreeRTOSヒープをPythonから直接利用できるようにするため、upy_light_engine/c_modules/port_micropython/modlightengine.c に以下のAPIを追加します。
- _lightengine.malloc(size): FreeRTOSヒープからメモリを確保し、Pythonの bytearray (参照渡し) として返す。
- _lightengine.free(buffer): 確保したメモリを解放する。

これにより、MicroPythonのガベージコレクション領域を消費せずに、数十KBの巨大なバッファをC層から直接確保できるようになります。

### Step 3: ゲーム側の ImageBufferManager の移行
game/main.py で bytearray(12 * 1024) として確保している画像バッファを、上記で作成した _lightengine.malloc を用いるように変更します。
さらに、1/4縮小化による画質低下を解消するため、バッファサイズを大幅に引き上げ（例えば35KBなど）、元の解像度（あるいは1/2縮小）のアセットをロードできるようにします。

## ユーザーへの確認事項 (User Review Required)
> [!IMPORTANT]
> - この変更では、Cモジュール (modlightengine.c) を編集するため、**Cardputer用のファームウェア（.bin）を再ビルドし、実機に焼き直す**必要があります。ファームウェアのビルドと書き込みをお願いしてもよろしいでしょうか？
> - また、このアプローチで問題なければ、実装に進みたいと思います。

## Verification Plan
1. modlightengine.c に malloc / ree を追加してファームウェアをビルドする。
2. ramebuffer_micropython.py をシングルバッファに変更。
3. main.py の ImageBufferManager が _lightengine.malloc を使ってエラーなく確保できることを確認。
4. Cardputer実機で実行し、以前と同じくクラッシュせずにゲームが起動すること、および画質の向上が可能かを確認する。
