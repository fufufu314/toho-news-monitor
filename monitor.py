import requests
from bs4 import BeautifulSoup
import os
import difflib
import json
from datetime import datetime, timedelta, timezone

# --- 設定 ---
CONFIG_FILE = "targets.json"
LOG_FILE = "diff_history.log"
IFTTT_KEY = os.environ.get("IFTTT_KEY")
IFTTT_EVENT = "toho_news_update"
JST = timezone(timedelta(hours=+9), 'JST')

def fetch_content(site):
    """設定に基づきサイトから特定セクションの内容を取得"""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    try:
        response = requests.get(site['url'], headers=headers, timeout=15)
        response.encoding = response.apparent_encoding 
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 動的なタグ検索
        find_args = { "name": site['tag'] }
        if 'class' in site: find_args['class_'] = site['class']
        if 'id' in site: find_args['id'] = site['id']
        
        target_section = soup.find(**find_args)
        return target_section.get_text("\n", strip=True) if target_section else None
    except Exception as e:
        print(f"Error fetching {site['name']}: {e}")
        return None

def send_ifttt(site_name, diff_text):
    if not IFTTT_KEY: return
    url = f"https://maker.ifttt.com/trigger/{IFTTT_EVENT}/with/key/{IFTTT_KEY}"
    data = {"value1": f"【{site_name}】更新検知\n\n{diff_text[:500]}"}
    requests.post(url, json=data)

def main():
    if not os.path.exists(CONFIG_FILE):
        print("設定ファイルが見つかりません。")
        return

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        targets = json.load(f)

    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
    
    for site in targets:
        print(f"Checking: {site['name']}...")
        current_content = fetch_content(site)
        if current_content is None: continue

        # サイトごとに保存ファイル名を変える (例: last_TOHOシネマズ上野.txt)
        save_file = f"last_{site['name']}.txt"
        old_content = ""
        if os.path.exists(save_file):
            with open(save_file, "r", encoding="utf-8") as f:
                old_content = f.read()

        if current_content != old_content:
            diff = difflib.unified_diff(
                old_content.splitlines(),
                current_content.splitlines(),
                fromfile='Old', tofile='New', lineterm=''
            )
            diff_text = "\n".join(list(diff))

            # ログ記録
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"\n[{now}] {site['name']} 変更検知\n{diff_text}\n" + "-"*30 + "\n")
            
            # 最新保存
            with open(save_file, "w", encoding="utf-8") as f:
                f.write(current_content)

            # IFTTT通知
            send_ifttt(site['name'], diff_text)
            print(f"Done: {site['name']} (Changed)")
        else:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{now}] {site['name']} チェック完了: 変更なし\n")
            print(f"Done: {site['name']} (No change)")

if __name__ == "__main__":
    main()
