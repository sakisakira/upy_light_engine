# エンジンの安全性向上とアサーション実装計画 (Plan 40)
**Date**: 2026-07-12 12:40:21

Cardputer (MicroPython) や Web (WASM) など様々なプラットフォームで動作するエンジンの安全性を向上させ、PC開発環境でのフェイルファスト（バグの早期発見）を実現します。

## 背景と課題
1. **アサーションの消失**: NDEBUG 環境では `assert()` が無効化されるため、実機でメモリ破壊などの致命的エラーを防げない。
2. **早期リターンのサイレント化**: オーバーフロー対策として導入した `if (count >= kMaxCommands) return;` はエラーを握り潰してしまう。
3. **引数のオーバーフロー**: 座標 (`x`, `y`) 等が巨大な値だった場合、内部計算でラップアラウンド（符号反転）が発生し、予期せぬ位置に描画されたりクラッシュの原因になる。

## 実装計画

### 1. 独自アサーション機構のプラットフォーム別実装 (`engine_types.h`)
エンジン共通のヘッダに `ENGINE_ASSERT_RETURN` を定義します。
ユーザーの指摘に従い、**PC（開発環境）では実行を停止**させ、**マイコン実機やWASM等では安全にスキップ（return）**する設計にします。

```c
#ifndef ENGINE_ASSERT
#include <stdio.h>
#include <stdlib.h>

// PC環境（Windows, Mac, Linuxのデバッグ/標準環境）では停止させる
#if defined(_WIN32) || defined(__APPLE__) || defined(__linux__)
  #define ENGINE_ABORT() abort()
#else
  #define ENGINE_ABORT() do {} while(0)
#endif

#define ENGINE_ASSERT_RETURN(cond, msg) \
    do { \
        if (!(cond)) { \
            printf("[Engine Error] %s:%d - %s\n", __FILE__, __LINE__, (msg)); \
            ENGINE_ABORT(); \
            return; \
        } \
    } while (0)
#endif
```

### 2. コマンド上限アサーションの復活 (`engine_types.c`)
先ほどの `if (display_list->count >= kMaxCommands) return;` を、`ENGINE_ASSERT_RETURN` に置き換えます。

### 3. 関数引数の型変更 (`int16_t` -> `int32_t`) とマージン考慮のクリッピング (`engine_types.c`)
従来の `dl_push_*` 関数の引数は `int16_t` だったため、Python側から巨大な値が渡された際、関数内部に入る前に暗黙のキャストによって値が切り捨てられ（ラップアラウンド）てしまうことが**本質的なバグの原因**でした。
これを解決するため、引数を `int32_t` で受け取るようにシグネチャを変更し、さらに 16bit 整数の限界 (`INT16_MAX`, `INT16_MIN`) に対し、描画サイズ `w`, `h` のマージン分を引いた安全な範囲でクリッピングしてから `int16_t` に格納します。

```c
// int16_t の限界（-32768等）まで許容するのは、どうせ -w 以下の座標は描画されないため無駄（冗長）です。
// したがって、完全に画面外となる -w（または画面最大幅）を基準にクリッピングします。
// （※ ENGINE_MAX_WIDTH = 320, ENGINE_MAX_HEIGHT = 240 を engine_types.h に定義します）

static inline int16_t sanitize_x(int32_t x, int32_t w) {
    if (x < -w) return (int16_t)-w;
    if (x > ENGINE_MAX_WIDTH) return ENGINE_MAX_WIDTH;
    return (int16_t)x;
}

static inline int16_t sanitize_y(int32_t y, int32_t h) {
    if (y < -h) return (int16_t)-h;
    if (y > ENGINE_MAX_HEIGHT) return ENGINE_MAX_HEIGHT;
    return (int16_t)y;
}
```
`dl_push_*` 内で `cmd->args.fill_rect.x = sanitize_x(x, w);` のように適用します。

### 4. `engine_render.c` のアサーション置換 (`engine_render.c`)
現在の `assert(0 && "Unsupported...");` となっている箇所を `ENGINE_ASSERT_RETURN(0, "Unsupported...");` に置き換えます。

---
この計画ファイル作成後、直ちに実行（ソースコードへの適用）へ移行します。
