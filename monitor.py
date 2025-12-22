import requests
from bs4 import BeautifulSoup
import os
import difflib
from datetime import datetime, timedelta, timezone

# --- 設定 ---
URL = "https://hlo.tohotheater.jp/net/schedule/076/TNPI2000J01.do"
SAVE_FILE = "last_news.txt"
LOG_FILE = "diff_history.log"

JST = timezone(timedelta(hours=+9), 'JST')

def fetch_news_content():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(URL, headers=headers)
        response.encoding = response.apparent_encoding 
        soup = BeautifulSoup(response.text, "html.parser")
        news_section = soup.find("section", class_="news")
        if news_section:
            # 各行をリスト形式で取得するため、一旦改行で分割
            return news_section.get_text("\n", strip=True)
    except Exception as e:
        print(f"取得エラー: {e}")
    return ""

def main():
    current_content = fetch_news_content()
    if not current_content:
        return

    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")

    old_content = ""
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            old_content = f.read()

    # 差分比較の実行
    if current_content != old_content:
        print(f"[{now}] 差分を検知しました。")
        
        # 行ごとの差分（Unified Diff形式）を生成
        diff = difflib.unified_diff(
            old_content.splitlines(),
            current_content.splitlines(),
            fromfile='Previous',
            tofile='Current',
            lineterm=''
        )
        diff_text = "\n".join(list(diff))

        # ログファイルに書き込み
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n--- {now} 変更検知 ---\n")
            f.write(diff_text + "\n")
            f.write("-" * 30 + "\n")
        
        # 最新内容を保存
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            f.write(current_content)
    else:
        print(f"[{now}] 変更なし")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{now}] チェック完了: 変更なし\n")

if __name__ == "__main__":
    main()
