import os
import re
import datetime
from pathlib import Path
from bs4 import BeautifulSoup
import requests
from discord_webhook import DiscordWebhook
from dotenv import load_dotenv

class KaldiSaleScraper:
    def __init__(self, html_dir, target_shops=None, webhook_url=None, debug=False):
        """
        初期化
        
        Args:
            html_dir: HTMLファイルが保存されているディレクトリパス
            target_shops: 対象店舗リスト（Noneの場合は全店舗）
            webhook_url: Discord Webhook URL
            debug: デバッグモードフラグ
        """
        self.html_dir = Path(html_dir)
        self.target_shops = target_shops
        self.webhook_url = webhook_url
        self.debug = debug
        
        # ディレクトリがなければ作成
        os.makedirs(self.html_dir, exist_ok=True)
    
    def get_kaldi_url(self):
        """
        現在の日付を使用したカルディのURL生成
        
        Returns:
            生成したURL
        """
        # 今日の日付をフォーマット (yyyy-MM-dd)
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        # 基本URLに日付を追加
        url = f"https://map.kaldi.co.jp/kaldi/articleList?account=kaldi&accmd=1&ftop=1&kkw001={today}"
        return url
        
    def fetch_and_save_html(self, url=None):
        """
        指定URLからHTMLを取得して保存
        
        Args:
            url: 取得するURL（Noneの場合は自動生成）
            
        Returns:
            保存したファイルパス
        """
        try:
            # URLが指定されていない場合は自動生成
            if url is None:
                url = self.get_kaldi_url()
                print(f"自動生成したURLを使用します: {url}")
                
            # リクエストヘッダー（Webサイトによっては必要）
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            if self.debug:
                print(f"リクエスト送信: {url}")
                print(f"ヘッダー: {headers}")
            
            # GETリクエスト送信
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()  # エラーチェック
            
            if self.debug:
                print(f"ステータスコード: {response.status_code}")
                print(f"レスポンスヘッダー: {response.headers}")
                print(f"HTML長さ: {len(response.text)} バイト")
            
            # 現在日時をファイル名に使用
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"kaldi_sale_{timestamp}.html"
            filepath = self.html_dir / filename
            
            # HTMLをファイルに保存
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(response.text)
                
            print(f"HTMLを保存しました: {filepath}")
            return filepath
            
        except requests.exceptions.RequestException as e:
            print(f"HTMLの取得に失敗しました: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return None
    
    def parse_html_files(self):
        """ディレクトリ内のすべてのHTMLファイルを解析"""
        sales_info = []
        
        for html_file in self.html_dir.glob("*.html"):
            if self.debug:
                print(f"HTMLファイル解析: {html_file}")
                
            with open(html_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            if self.debug:
                print(f"HTML長さ: {len(content)} バイト")
                
            soup = BeautifulSoup(content, "html.parser")
            file_sales = self._extract_sales_info(soup)
            
            if self.debug:
                print(f"抽出されたセール情報数: {len(file_sales)}")
                if len(file_sales) > 0:
                    print(f"最初のセール情報サンプル: {file_sales[0]}")
                    
            sales_info.extend(file_sales)
        
        return sales_info
    
    def _extract_sales_info(self, soup):
        """
        BeautifulSoupオブジェクトからカルディのセール情報を抽出
        """
        sales = []
        base_url = "https://map.kaldi.co.jp"
        
        # テーブル行で店舗ごとのセール情報を取得
        sale_rows = soup.select("table.cz_sp_table tr")
        
        for row in sale_rows:
            # テーブルヘッダーや空の行は無視
            if not row.select_one("td"):
                continue
            
            # 店舗情報を含むtdを取得
            shop_cell = row.select_one("td[aria-label='店舗名、住所など']")
            if not shop_cell:
                continue
                
            # セール内容を含むtdを取得
            detail_cell = row.select_one("td[aria-label='セール内容']")
            if not detail_cell:
                continue
            
            # 店舗名
            shop_name_elem = shop_cell.select_one("span.salename a")
            if not shop_name_elem:
                continue
                
            shop_name = shop_name_elem.text.strip()
            
            # 対象店舗のみフィルタリング
            if self.target_shops and shop_name not in self.target_shops:
                continue
                
            # 店舗URL
            shop_url = base_url + shop_name_elem["href"] if shop_name_elem.has_attr("href") else ""
            
            # 店舗住所
            shop_address = shop_cell.select_one("span.saleadress").text.strip() if shop_cell.select_one("span.saleadress") else ""
            
            # セールアイコン（開催中/予告など）- 通常と予告の両方をチェック
            sale_status_elem = shop_cell.select_one("span.saleicon") or shop_cell.select_one("span.saleicon_f")
            sale_status = sale_status_elem.text.strip() if sale_status_elem else ""
            
            # セールタイトル - 通常と予告の両方をチェック
            sale_title_elem = shop_cell.select_one("span.saletitle") or shop_cell.select_one("span.saletitle_f")
            sale_title = sale_title_elem.text.strip() if sale_title_elem else ""
            
            # セール期間（通常と予告の両方をチェック）
            sale_date_elem = detail_cell.select_one("p.saledate") or detail_cell.select_one("p.saledate_f")
            sale_date = sale_date_elem.text.strip() if sale_date_elem else ""
            
            # セール詳細
            sale_detail = detail_cell.select_one("p.saledetail").text.strip() if detail_cell.select_one("p.saledetail") else ""
            
            # セール詳細の注意書き
            sale_notes = detail_cell.select_one("p.saledetail_notes").text.strip() if detail_cell.select_one("p.saledetail_notes") else ""
            
            # 販売情報をまとめる
            sales.append({
                "shop": shop_name,
                "address": shop_address,
                "status": sale_status,
                "title": sale_title,
                "date": sale_date,
                "detail": sale_detail,
                "notes": sale_notes,
                "url": shop_url
            })
        
        return sales
    
    def format_sale_message(self, sale):
        """セール情報を通知用フォーマットに変換"""
        return f"""
🔔 {sale.get('status', '新セール')}!
📍 {sale.get('shop', '不明')}
🏬 {sale.get('address', '')}
🎯 {sale.get('title', 'セール詳細不明')}
📅 {sale.get('date', '日付不明')}
💰 {sale.get('detail', '')}
🔗 {sale.get('url', '#')}
"""

    def save_to_text_file(self, sales_info, output_file="sales_output.txt"):
        """セール情報をテキストファイルに保存"""
        if not sales_info:
            return False
        
        with open(output_file, "w", encoding="utf-8") as f:
            for sale in sales_info:
                message = self.format_sale_message(sale)
                f.write(message)
                f.write("\n" + "-"*40 + "\n")  # 区切り線
        
        return True
        
    def notify_discord(self, sales_info):
        """Discord Webhookを使用してセール情報を通知"""
        if not self.webhook_url or not sales_info:
            if self.debug:
                if not self.webhook_url:
                    print("Discord通知: Webhook URLが設定されていません")
                if not sales_info:
                    print("Discord通知: 通知するセール情報がありません")
            return False
        
        if self.debug:
            print(f"Discord通知: {len(sales_info)}件のセール情報を送信します")
            # Webhookの最初の数文字を表示（セキュリティのため全部は表示しない）
            webhook_prefix = self.webhook_url[:30] + "..." if len(self.webhook_url) > 30 else self.webhook_url
            print(f"Discord Webhook URL: {webhook_prefix}")
        
        for i, sale in enumerate(sales_info):
            message = self.format_sale_message(sale)
            
            if self.debug:
                print(f"Discord通知 {i+1}/{len(sales_info)}: {sale.get('shop')} - {sale.get('title')}")
                
            webhook = DiscordWebhook(url=self.webhook_url, content=message)
            response = webhook.execute()
            
            if self.debug:
                print(f"Discord通知レスポンス: ステータスコード {response.status_code}")
            
            # API制限を避けるため少し待機
            if i < len(sales_info) - 1:
                import time
                time.sleep(1)
        
        return True

def main():
    import argparse
    
    # .envファイルを読み込む
    load_dotenv()
    
    # コマンドライン引数の設定
    parser = argparse.ArgumentParser(description='カルディセール情報取得ツール')
    parser.add_argument('--url', type=str, help='セール情報を取得するURL（指定しない場合は現在の日付で自動生成）')
    parser.add_argument('--notify', action='store_true', help='Discordに通知する')
    parser.add_argument('--output', type=str, help='出力テキストファイル名（.envファイルの設定を上書き、デフォルト: sales_output.txt）')
    parser.add_argument('--fetch-only', action='store_true', help='HTMLの取得のみを行う')
    parser.add_argument('--no-fetch', action='store_true', help='HTMLの取得をスキップして既存ファイルを解析')
    parser.add_argument('--shops', type=str, help='対象店舗のリスト（カンマ区切り）')
    parser.add_argument('--all-shops', action='store_true', help='全店舗を対象にする')
    parser.add_argument('--discord-webhook', type=str, help='Discord Webhook URL（.envファイルの設定を上書き）')
    parser.add_argument('--debug', action='store_true', help='デバッグモード（詳細情報を表示）')
    args = parser.parse_args()
    
    # Discord Webhook URLを取得（優先順位: コマンドライン引数 > 環境変数）
    webhook_url = None
    if args.notify:
        webhook_url = args.discord_webhook or os.environ.get("DISCORD_WEBHOOK_URL")
    
    # 対象店舗リスト（優先順位: コマンドラインオプション > 環境変数 > デフォルト値）
    if args.all_shops:
        target_shops = None  # すべての店舗を対象
    elif args.shops:
        target_shops = [shop.strip() for shop in args.shops.split(',')]
    elif os.environ.get("TARGET_SHOPS"):
        target_shops = [shop.strip() for shop in os.environ.get("TARGET_SHOPS").split(',')]
    else:
        # デフォルトの対象店舗リスト
        target_shops = ["池袋店", "渋谷店", "新宿店", "立川若葉ケヤキモール店"]
    
    # デバッグモードの設定（コマンドラインオプション > 環境変数）
    debug_mode = args.debug or os.environ.get("DEBUG") == "1"
    
    # スクレイパーインスタンス
    scraper = KaldiSaleScraper(
        html_dir="./data",
        target_shops=target_shops,
        webhook_url=webhook_url,
        debug=debug_mode
    )
    
    # no-fetchオプションが指定されていない場合はHTMLを取得
    if not args.no_fetch:
        html_path = scraper.fetch_and_save_html(args.url)  # 引数なしの場合は自動生成URLを使用
        if not html_path:
            print("HTMLの取得に失敗しました")
            return
        
        # fetch-onlyオプションが指定されている場合はここで終了
        if args.fetch_only:
            return
    
    # セール情報を抽出
    sales_info = scraper.parse_html_files()
    
    # 出力ファイル名の決定（優先順位: コマンドラインオプション > 環境変数 > デフォルト値）
    output_file = args.output or os.environ.get("OUTPUT_FILE") or "sales_output.txt"
    
    if sales_info:
        # テキストファイルに保存
        scraper.save_to_text_file(sales_info, output_file)
        print(f"{len(sales_info)}件のセール情報を{output_file}に保存しました")
        
        # Discord通知（--notifyオプションがある場合のみ）
        if args.notify and webhook_url:
            scraper.notify_discord(sales_info)
            print(f"{len(sales_info)}件のセール情報をDiscordに通知しました")
    else:
        print("セール情報は見つかりませんでした")

if __name__ == "__main__":
    main()