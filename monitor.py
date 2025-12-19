import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime, timedelta, timezone

# --- 設定 ---
URL = "https://hlo.tohotheater.jp/net/schedule/076/TNPI2000J01.do"
SAVE_FILE = "last_news.txt"
LOG_FILE = "diff_history.log"

# 日本時間のタイムゾーン設定
JST = timezone(timedelta(hours=+9), 'JST')

def fetch_news_content():
    """サイトから<section class='news'>の内容を取得する"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(URL, headers=headers)
        # 文字化け対策: レスポンスから文字コードを自動判定
        response.encoding = response.apparent_encoding 
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 指定されたタグを抽出
        news_section = soup.find("section", class_="news")
        if news_section:
            # テキストを抽出し、余計な空白を削除。各要素の間には改行を入れる
            return news_section.get_text("\n", strip=True)
            
    except Exception as e:
        print(f"取得エラー: {e}")
    return ""

def main():
    # 1. 現在の内容を取得
    current_content = fetch_news_content()
    if not current_content:
        print("ニュースセクションが見つかりませんでした。")
        return

    # 現在時刻（JST）
    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")

    # 2. 前回の内容を読み込み
    old_content = ""
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            old_content = f.read()

    # 3. 比較とログ記録
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        if current_content != old_content:
            print(f"[{now}] 差分を検知しました。内容を更新します。")
            f.write(f"[{now}] 更新あり: 内容が変更されました。\n")
            
            # 差分があるときだけ最新内容を保存
            with open(SAVE_FILE, "w", encoding="utf-8") as f_save:
                f_save.write(current_content)
        else:
            print(f"[{now}] 変更はありませんでした。")
            # 変更がなくても実行した証拠をログに残す
            f.write(f"[{now}] チェック完了: 変更なし\n")

if __name__ == "__main__":
    main()
