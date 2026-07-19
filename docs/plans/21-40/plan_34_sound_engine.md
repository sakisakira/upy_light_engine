# Phase 4: サウンドエンジン実装計画

現在のファームウェアには、すでにサウンド用のC言語スケルトン（`_sound_engine`）とPython側のラッパー（`engine.sound`）が組み込まれており、I2S（およびES8311）を通じたビープ音の再生が可能になっています。

このフェーズでは、これを本格的なゲーム用サウンドエンジンへと進化させます。

## Goal Description

**目標**: 
Python側からBGM（MML形式）と効果音（SFX）を同時に、遅延なく（非同期に）再生できるレトロな8ビットサウンドエンジンを完成させること。

現状の課題：
- 発音波形が「矩形波（Square）」しか実装されていない。
- 音の減衰（エンベロープ）がなく、プツッというノイズが入りやすい。
- `main.py` などのメインループに `sound.update()` が組み込まれておらず、MMLの自動再生が進行しない。

## User Review Required

以下の実装案についてレビューをお願いします。特に、**「C言語側でどこまで処理を持つか（エンベロープの自動減衰など）」**について、今回の提案で十分かご意見があれば教えてください。

## Proposed Changes

### 1. _lightengine C Module (`sound_engine.c`) の強化

#### [MODIFY] [sound_engine.c](file:///d:/sakira/work/cardputer/upy_light_engine/c_modules/sound_engine/sound_engine.c)
- **複数波形のサポート**:
  - `wave_type` に応じて波形を生成するロジックを追加します。
  - `0`: 矩形波（Square）
  - `1`: ノコギリ波（Sawtooth）
  - `2`: 三角波（Triangle）
  - `3`: ノイズ（Noise - 線形合同法などによる擬似乱数）
- **シンプルな減衰（Decay）エンベロープ**:
  - レトロゲーム特有の「ピコッ」という効果音を出しやすくするため、指定したサンプル数で音量が0に向かって自動で減衰する機能（Decay）を実装します。

### 2. Pythonレイヤーの強化 (`engine/sound.py` 等)

#### [MODIFY] [sound.py](file:///d:/sakira/work/cardputer/upy_light_engine/engine/sound.py) および [sound_micropython.py](file:///d:/sakira/work/cardputer/upy_light_engine/engine/hal/sound_micropython.py)
- `engine.sound.play_sfx(preset_name)` のような、あらかじめ定義された効果音を鳴らす高レベルAPIを追加します（例："jump", "coin", "hit"）。
- 波形（wave_type）の定数を定義します。

#### [MODIFY] [mml_parser.py](file:///d:/sakira/work/cardputer/upy_light_engine/engine/mml_parser.py)
- 和音（複数トラック）のMMLをパースできるように拡張するか、複数トラックを同時に鳴らせるように `sound.py` 側で和音のスケジューリングを調整します。

#### [NEW] [__init__.py](file:///d:/sakira/work/cardputer/upy_light_engine/engine/__init__.py)
- `engine` パッケージのルートに `engine.update()` などの統合関数を定義し、その内部で `framebuffer.update()` や `sound.update()`、`input.update()` などを一括して呼び出すようにします。
- これにより、「`framebuffer` の中で `sound` を更新する」という不自然な依存関係をなくし、ユーザーは `engine.update()` を呼ぶだけで全システムが進行する自然な設計にします。

### 3. デモへの統合 (`main.py`)

#### [MODIFY] [main.py](file:///d:/sakira/work/cardputer/upy_light_engine/main.py)
- メインループで `engine.update()` を呼ぶように修正します。
- 起動時に4和音のテスト用MMLを再生します。
  - テスト内容は「ド → ド・ミ → ド・ミ・ソ → ド・ミ・ソ・ド」と徐々に音が重なっていくシーケンスにし、4和音が正しく独立して鳴っているかを耳でハッキリ聞き分けられるようにします。

## Verification Plan

### Automated Tests
- Cモジュールを再ビルドし、Cardputer実機にフラッシュしてエラーなく起動することを確認します。

### Manual Verification
- `main.py` を実行した際、スピーカーから意図したメロディ（MML）が再生されること。
- 新しく実装した波形（ノコギリ波やノイズ）が正常に聞こえること。
- 描画の60FPS（63FPS）に影響を与えず、非同期にサウンドが再生され続けること。
