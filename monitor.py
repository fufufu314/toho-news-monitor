import requests
from bs4 import BeautifulSoup
import os

URL = "https://hlo.tohotheater.jp/net/schedule/076/TNPI2000J01.do"
SAVE_FILE = "last_news.txt"
LOG_FILE = "diff_history.log"

def fetch_news_content():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    
    try:
        response = requests.get(URL, headers=headers)
        
        # --- 文字化け対策の重要ポイント ---
        # response.encoding を response.apparent_encoding (解析結果) に設定する
        response.encoding = response.apparent_encoding 
        
        # もし上記でもダメな場合は、明示的に以下を指定してみてください
        # response.encoding = 'shift_jis' 
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # <section class="news"> タグを取得
        news_section = soup.find("section", class_="news")
        if news_section:
            # textだけでなく、構造を保ちたい場合は strip=True を使用
            return news_section.get_text("\n", strip=True)
            
    except Exception as e:
        print(f"エラーが発生しました: {e}")
    return ""

def main():
    current_content = fetch_news_content()
    if not current_content:
        print("ニュースセクションを取得できませんでした。")
        return

    # 保存・比較（utf-8で統一して保存）
    old_content = ""
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            old_content = f.read()

    if current_content != old_content:
        print("差分を検知しました。")
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            f.write(current_content)
    else:
        print("変更はありません。")

if __name__ == "__main__":
    main()
