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

7. 同じ日付のHTMLファイルが存在しても強制的に取得する
   ```bash
   python src/scraper.py --force-fetch
   ```

8. Discordに通知する（DISCORD_WEBHOOK_URL環境変数が必要）
   ```bash
   python src/scraper.py --notify
   ```

9. 通知履歴を無視して強制的に通知する
   ```bash
   python src/scraper.py --notify --force-notify
   ```

10. 通知履歴ファイルのパスを指定する
   ```bash
   python src/scraper.py --notify --history-file "./custom_history.json"
   ```

11. 特定の店舗のみを対象にする
   ```bash
   python src/scraper.py --shops "渋谷店,新宿店,池袋店"
   ```

12. すべての店舗を対象にする
   ```bash
   python src/scraper.py --all-shops
   ```

13. 設定をカスタマイズする場合
   - `src/scraper.py` の `main()` 関数内でデフォルトの対象店舗リストを編集

## 環境変数による設定

`.env`ファイルで以下の設定を行えます。コマンドライン引数が指定された場合は、環境変数よりも優先されます。

| 環境変数 | 説明 | コマンドライン引数 |
|----------|------|-------------------|
| DISCORD_WEBHOOK_URL | Discord Webhookの通知先URL | --discord-webhook |
| TARGET_SHOPS | 対象店舗リスト（カンマ区切り） | --shops |
| OUTPUT_FILE | セール情報の出力ファイル名 | --output |
| HISTORY_FILE | 通知履歴ファイルのパス | --history-file |
| DEBUG | デバッグモード（1=有効、0=無効） | --debug |

## カスタマイズ

セール情報の抽出ロジックは、実際のHTMLの構造に合わせて `_extract_sales_info()` メソッドを修正する必要があります。対象ウェブサイトのHTML構造を確認し、適切なセレクタやパターンを設定してください。

## 重複防止機能

本ツールには2つの重複防止機能があります：

1. HTMLファイルの重複取得防止
2. セール情報の重複通知防止

### HTMLファイルの重複防止

同じ日付のHTMLファイルを重複して取得することを防ぎます：

1. URLから日付情報を抽出（例: `kkw001=2025-03-10` → `20250310`）
2. 同じ日付のHTMLファイルが既に存在するか確認
3. 既存のファイルが見つかった場合は、新たにダウンロードせず既存ファイルを使用
4. `--force-fetch` オプションで強制的に再取得することも可能

### 通知履歴の仕組み

通知済みのセール情報を記録し、同じセール情報を重複して通知することを防ぎます：

1. 各セール情報に対してユニークなIDを生成（店舗名、タイトル、日付、詳細情報から生成）
2. 通知履歴ファイル（JSONフォーマット）に通知済みのセール情報IDを保存
3. 新しくスクレイピングしたセール情報と通知履歴を比較
4. 通知済みのセール情報は自動的にフィルタリング

#### ユニークID生成の詳細

ユニークIDは以下のフィールドのみを使用して生成されます：
- 店舗名（shop）
- セールタイトル（title）
- セール期間（date）
- セール詳細（detail）

**重要**: ユニークIDには通知日時は含まれません。そのため、実行時間が異なっても、同じセール情報は同じIDを持ちます。これにより、毎日実行しても同じセール情報が重複して通知されることはありません。

```python
# 実際のユニークID生成ロジック
key_fields = [
    sale.get('shop', ''),
    sale.get('title', ''),
    sale.get('date', ''),
    sale.get('detail', '')
]
hash_string = "|".join(key_fields)
sale_id = hashlib.sha256(hash_string.encode('utf-8')).hexdigest()
```

### 通知履歴ファイル

デフォルトでは `./data/notification_history.json` に保存されます。ファイル形式は以下の通りです。

```json
{
  "セールID": {
    "notified_at": "通知日時（ISO形式）",
    "shop": "店舗名",
    "title": "セールタイトル",
    "date": "セール期間"
  },
  "セールID2": {
    ...
  }
}
```

### 履歴機能のオプション

- `--history-file`: 履歴ファイルのパスを指定（環境変数: `HISTORY_FILE`）
- `--force-notify`: 履歴を無視して強制的に通知する（重複チェックを行わない）
- `--debug`: 詳細なログを表示（通知済みか新規かの判定結果も表示される）

### 履歴チェックの確認方法

実行時に`--debug`オプションを付けると、各セール情報が通知済みか新規かの判定結果が表示されます：

```bash
python src/scraper.py --notify --debug
```

以下のようなメッセージが表示されます：
- 通知済みの場合: `既に通知済み: 渋谷店 - 春のコーヒーセール`
- 新規情報の場合: `新しいセール情報: 池袋店 - 紅茶フェア`

### 履歴のリセット

履歴をリセットしたい場合は、履歴ファイルを削除してください。

```bash
rm ./data/notification_history.json
```

## 自動化

cronやWindowsのタスクスケジューラで定期実行するように設定すると、セール情報を自動的に取得・通知できます。
通知履歴機能により、同じセール情報が重複して通知されることはありません。

### Raspberry Piでの設定手順

#### 1. 準備

最初にログ保存用のディレクトリを作成しておきます：

```bash
# プロジェクトのルートディレクトリで実行
mkdir -p logs
```

#### 2. cronの設定

crontabを編集してスケジュールを設定します：

```bash
# cronの設定ファイルを開く
crontab -e
```

以下のような設定を追加します（毎日午前8時に実行する例）：

```bash
# 毎日午前8時に実行
0 8 * * * cd /home/pi/cardi-sale && python src/scraper.py --notify >> /home/pi/cardi-sale/logs/cron.log 2>&1
```

**注意事項**:
- パスは実際のインストール場所に合わせて調整してください
- `python` コマンドがPython 3を指していることを確認してください（必要に応じて `python3` に変更）
- `>> /home/pi/cardi-sale/logs/cron.log 2>&1` で実行結果とエラーをログファイルに記録します

#### 3. 動作確認

設定をテストするには、一時的に実行間隔を短くしてみましょう：

```bash
# 5分ごとに実行（テスト用）
*/5 * * * * cd /home/pi/cardi-sale && python src/scraper.py --notify >> /home/pi/cardi-sale/logs/cron.log 2>&1
```

実行結果は以下のコマンドでログファイルを確認できます：

```bash
tail -f /home/pi/cardi-sale/logs/cron.log
```

問題なく動作することを確認したら、本来の実行間隔に戻してください。

#### 4. その他の実行スケジュール例

```bash
# 毎日午前7時と午後7時の2回実行
0 7,19 * * * cd /home/pi/cardi-sale && python src/scraper.py --notify >> /home/pi/cardi-sale/logs/cron.log 2>&1

# 平日（月〜金）のみ実行
0 8 * * 1-5 cd /home/pi/cardi-sale && python src/scraper.py --notify >> /home/pi/cardi-sale/logs/cron.log 2>&1
```

### その他のLinuxでのcron設定例

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