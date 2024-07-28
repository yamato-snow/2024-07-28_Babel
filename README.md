# プロジェクト バベル

![bigban_optimized_final](https://github.com/user-attachments/assets/b0d0e8aa-4702-45ac-9ee7-5e5a74a0a397)
システム生成AI #Babel にて「多段要件定義生成フロー」の実装を試験中。

これまでのZoltraakフローの
要望 → 要件定義書 → 実装

の「要件定義書」生成を多段にする事で
・箇条書きレベルの概要のみ人間が確認
・専門家レベルの要件定義書は基本AIが見ることで、大規模かつ詳細の実装が可能に
・細かいチューニングをしたい時のみ人が詳細要件定義を見る

といったメリットがあります。

こちらも近日リリースします。

**注意** プロジェクト バベルは実験的なプロジェクトです。
まだ正式なリリースではないのでご了承下さい。

### フロントエンドの立ち上げ

こちらのURLにアクセスしてください。
→ https://babelv1.vercel.app/development/editor

### バックエンドの立ち上げ

バックエンドは FastAPI と webソケットを利用しています。

1. `src/backend` ディレクトリに移動します：

```bash
git clone https://github.com/dai-motoki/babel-v1-backend.git
cd babel-v1-backend
```

2. バックエンドサーバーを起動します：


事前に 

以下AnthropicのAPIキーを設定してください。
https://console.anthropic.com/settings/keys

```sh
export ANTHROPIC_API_KEY=sk-ant-xxxxx
export OPENAI_API_KEY=sk-ant-xxxxx
```

Pythonバージョンの設定

```bash
pyenv local 3.12.2
```
※ 必要に応じて `pyenv install 3.12.2` でPythonをインストールしてください。

仮想環境の作成と有効化
```bash
python -m venv .venv
```

```bash
. .venv/bin/activate  # Windowsのコマンドプロンプトの場合は `.venv\Scripts\activate.bat`
```

依存関係のインストール
```bash
pip install -r requirements.txt
```

以下２つは別のターミナルで立ち上げてください。
```bash
uvicorn file_watcher:app --host 0.0.0.0 --port 8001 --reload
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

4. バックエンドサーバーが `http://localhost:8000`, `http://localhost:8001` で起動します。


注意：実際の環境設定や依存関係は、プロジェクトの具体的な構成によって異なる場合があります。必要に応じて、プロジェクトのREADMEファイルや設定ファイルを確認してください。
