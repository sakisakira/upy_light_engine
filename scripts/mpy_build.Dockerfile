# MicroPythonのCモジュールビルド用 Dockerfile
# ESP32-S3向けの開発ツールが含まれるESP-IDFの公式イメージを使用します。
# ※MicroPythonのバージョンに合ったIDFバージョンを選ぶ必要があります。
# 現時点でのMicroPythonのesp32ポート推奨バージョンである v5.0.4 を指定しています。
FROM espressif/idf:release-v5.3

# 追加で必要なパッケージのインストール
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# コンテナ内の作業ディレクトリ
WORKDIR /workspace

CMD ["bash"]
