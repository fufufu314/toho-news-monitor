import requests
from bs4 import BeautifulSoup
import os
import difflib
from datetime import datetime, timedelta, timezone

# --- 設定 ---
URL = "https://hlo.tohotheater.jp/net/schedule/076/TNPI2000J01.do"
SAVE_FILE = "last_news.txt"
LOG_FILE = "diff_history.log"
# GitHub Secretsから環境変数を読み込む
IFTTT_KEY = os.environ.get("IFTTT_KEY")
IFTTT_EVENT = "toho_news_update"

JST = timezone(timedelta(hours=+9), 'JST')

def fetch_news_content():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    try:
        response = requests.get(URL, headers=headers)
        response.encoding = response.apparent_encoding 
        soup = BeautifulSoup(response.text, "html.parser")
        news_section = soup.find("section", class_="news")
        if news_section:
            return news_section.get_text("\n", strip=True)
    except Exception as e:
        print(f"取得エラー: {e}")
    return ""

def send_ifttt_notification(diff_text):
    if not IFTTT_KEY:
        print("IFTTT_KEYが設定されていません。")
        return
    
    # IFTTT WebhookのURL
    url = f"https://maker.ifttt.com/trigger/{IFTTT_EVENT}/with/key/{IFTTT_KEY}"
    # Value1に差分内容を乗せる
    data = {"value1": f"TOHOシネマズ上野に更新があります！\n\n{diff_text[:500]}"} # 長すぎるとエラーになるため制限
    
    response = requests.post(url, json=data)
    if response.status_code == 200:
        print("IFTTT通知を送信しました。")
    else:
        print(f"IFTTTエラー: {response.status_code}")

def main():
    current_content = fetch_news_content()
    if not current_content: return

    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
    old_content = ""
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            old_content = f.read()

    if current_content != old_content:
        # 差分の作成
        diff = difflib.unified_diff(
            old_content.splitlines(),
            current_content.splitlines(),
            fromfile='Previous', tofile='Current', lineterm=''
        )
        diff_text = "\n".join(list(diff))

        # ログ保存
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n--- {now} 変更検知 ---\n{diff_text}\n" + "-"*30 + "\n")
        
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            f.write(current_content)

        # IFTTT通知の実行
        send_ifttt_notification(diff_text)
    else:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{now}] 変更なし\n")

if __name__ == "__main__":
    main()
