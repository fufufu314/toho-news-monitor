import requests
from bs4 import BeautifulSoup
import os

URL = "https://hlo.tohotheater.jp/net/schedule/076/TNPI2000J01.do"
SAVE_FILE = "last_news.txt"
LOG_FILE = "diff_history.log"

def fetch_news_content():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    response = requests.get(URL, headers=headers)
    response.encoding = 'utf-8' # 文字化け防止
    soup = BeautifulSoup(response.text, "html.parser")
    
    # <section class="news"> タグを取得
    news_section = soup.find("section", class_="news")
    if news_section:
        return news_section.get_text(strip=True)
    return ""

def main():
    current_content = fetch_news_content()
    if not current_content:
        print("ニュースセクションが見つかりませんでした。")
        return

    # 前回保存した内容と比較
    old_content = ""
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            old_content = f.read()

    if current_content != old_content:
        print("差分を検知しました。記録を更新します。")
        # 履歴ログに日付とともに記録（簡易版）
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n[{now}] 更新あり\n{current_content[:100]}...\n") # 冒頭100文字のみログ
        
        # 最新内容を保存
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            f.write(current_content)
    else:
        print("差分はありません。")

if __name__ == "__main__":
    main()
