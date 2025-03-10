# cardi-sale

カルディのセール情報をスクレイピングし、特定の店舗のセール情報をDiscordに通知するボットです。

## 必要環境

- Python 3.10 以上
- pip (Pythonパッケージマネージャー)

## セットアップ

1. 依存ライブラリをインストール
   ```bash
   pip install -r requirements.txt
   ```

2. 設定ファイルの準備
   - `.env.example`を`.env`にコピー
     ```bash
     cp .env.example .env
     ```
   - `.env`ファイルを編集して設定をカスタマイズ
     - Discord Webhook URL
     - 対象店舗リスト
     - 出力ファイル名
     - デバッグモード

3. Discord Webhookの設定
   - Discord上で通知先チャンネルのWebhook URLを取得
     1. Discordサーバーの設定を開く
     2. 「連携サービス」→「ウェブフック」を選択
     3. 「新しいウェブフック」をクリック
     4. 名前を設定し、通知を送信したいチャンネルを選択
     5. 「ウェブフックURLをコピー」をクリックしてURLを取得
   - コピーしたURLを`.env`ファイルの`DISCORD_WEBHOOK_URL`に設定

3. セール情報のHTMLファイルを保存
   - `data` ディレクトリにHTMLファイルを保存
   - ファイル名は任意（拡張子は `.html`）

## 使用方法

1. 現在日付のセール情報HTMLを取得して処理
   ```bash
   python src/scraper.py
   ```

2. 特定のURLからHTMLを取得して保存する（必要な場合のみ）
   ```bash
   python src/scraper.py --url "https://map.kaldi.co.jp/kaldi/articleList?account=kaldi&accmd=1&ftop=1&kkw001=2025-03-10"
   ```

3. HTMLの取得のみを行う場合
   ```bash
   python src/scraper.py --fetch-only
   ```

4. HTMLの取得をスキップして既存ファイルを解析
   ```bash
   python src/scraper.py --no-fetch
   ```

5. セール情報をテキストファイルに出力する（デフォルト動作）
   ```bash
   python src/scraper.py
   ```
   出力ファイルは `sales_output.txt` に保存されます

6. 出力ファイル名を指定する
   ```bash
   python src/scraper.py --output results.txt
   ```

7. Discordに通知する（DISCORD_WEBHOOK_URL環境変数が必要）
   ```bash
   python src/scraper.py --notify
   ```

8. 全ての処理を一度に行う（HTML取得→解析→Discord通知）
   ```bash
   python src/scraper.py --notify
   ```

9. 特定の店舗のみを対象にする
   ```bash
   python src/scraper.py --shops "渋谷店,新宿店,池袋店"
   ```

10. すべての店舗を対象にする
   ```bash
   python src/scraper.py --all-shops
   ```

11. 設定をカスタマイズする場合
   - `src/scraper.py` の `main()` 関数内でデフォルトの対象店舗リストを編集

## 環境変数による設定

`.env`ファイルで以下の設定を行えます。コマンドライン引数が指定された場合は、環境変数よりも優先されます。

| 環境変数 | 説明 | コマンドライン引数 |
|----------|------|-------------------|
| DISCORD_WEBHOOK_URL | Discord Webhookの通知先URL | --discord-webhook |
| TARGET_SHOPS | 対象店舗リスト（カンマ区切り） | --shops |
| OUTPUT_FILE | セール情報の出力ファイル名 | --output |
| DEBUG | デバッグモード（1=有効、0=無効） | --debug |

## カスタマイズ

セール情報の抽出ロジックは、実際のHTMLの構造に合わせて `_extract_sales_info()` メソッドを修正する必要があります。対象ウェブサイトのHTML構造を確認し、適切なセレクタやパターンを設定してください。

## 自動化

cronやWindowsのタスクスケジューラで定期実行するように設定すると、セール情報を自動的に取得・通知できます。

### Linuxでのcron設定例

```bash
# 毎日午前9時に実行
0 9 * * * cd /path/to/cardi && python src/scraper.py --notify
```

### Windowsでのタスクスケジューラ設定

1. タスクスケジューラを開く
2. 「基本タスクの作成」をクリック
3. 名前と説明を入力
4. トリガーを「毎日」に設定
5. 実行時間を設定
6. アクションを「プログラムの開始」に設定
7. プログラムに`pythonw`（バックグラウンド実行の場合）またはpython.exeのフルパスを指定
8. 引数に`C:\path\to\cardi\src\scraper.py --notify`を指定
9. 開始場所に`C:\path\to\cardi`を指定