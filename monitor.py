import requests
from bs4 import BeautifulSoup
import os
import difflib
import json
import re
from datetime import datetime, timedelta, timezone

# --- 設定 ---
CONFIG_FILE = "targets.json"
LOG_FILE = "diff_history.log"
# GitHub Secretsから読み込む（設定されていない場合はNone）
IFTTT_KEY = os.environ.get("IFTTT_KEY")
IFTTT_EVENT = "toho_news_update"

# 日本時間のタイムゾーン
JST = timezone(timedelta(hours=+9), 'JST')

def fetch_content(site):
    """設定に基づきサイトから情報を取得（HTML/JS Payload両対応）"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        print(f"--- 巡回開始: {site['name']} ---")
        response = requests.get(site['url'], headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"  [!] アクセス失敗 (Status: {response.status_code})")
            return None

        # A. Nuxt.js payload.js の解析（グラシネ池袋など）
        if site.get('format') == 'js_payload':
            text = response.text
            # 正規表現で news: { ... } の中身を最短一致で抽出
            match = re.search(r'news:\{(.*?)\}', text, re.DOTALL)
            if match:
                print(f"  [✓] payload内のnewsデータを抽出しました")
                # 差分監視用なので、生の文字列をそのまま返す
                return match.group(0) 
            else:
                print(f"  [!] newsデータ構造が見つかりませんでした")
                return None

        # B. 通常のHTML解析（TOHOシネマズなど）
        response.encoding = response.apparent_encoding 
        soup = BeautifulSoup(response.text, "html.parser")
        
        find_args = { "name": site['tag'] }
        if 'class' in site: find_args['class_'] = site['class']
        if 'id' in site: find_args['id'] = site['id']
        
        target_section = soup.find(**find_args)
        if target_section:
            print(f"  [✓] HTML要素を取得しました ({site['tag']})")
            return target_section.get_text("\n", strip=True)
        else:
            print(f"  [!] 指定されたHTML要素が見つかりません: {find_args}")
            return None

    except Exception as e:
        print(f"  [!] 例外が発生しました: {e}")
        return None

def send_ifttt(site_name, diff_text):
    """IFTTT Webhookへ通知を送信"""
    if not IFTTT_KEY:
        return
    
    url = f"https://maker.ifttt.com/trigger/{IFTTT_EVENT}/with/key/{IFTTT_KEY}"
    # メッセージの整形（最大800文字）
    message = f"【{site_name}】更新検知\n\n{diff_text}"
    data = {"value1": message[:800]}
    
    try:
        requests.post(url, json=data, timeout=10)
    except Exception as e:
        print(f"  [!] IFTTT送信エラー: {e}")

def main():
    if not os.path.exists(CONFIG_FILE):
        print(f"設定ファイル {CONFIG_FILE} が見つかりません。")
        return

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        targets = json.load(f)

    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
    
    for site in targets:
        current_content = fetch_content(site)
        if current_content is None:
            continue

        # サイト名に基づいて保存ファイル名を生成（禁止文字を置換）
        safe_name = re.sub(r'[\\/:*?"<>|]', '_', site['name'])
        save_file = f"last_{safe_name}.txt"
        
        old_content = ""
        if os.path.exists(save_file):
            with open(save_file, "r", encoding="utf-8") as f:
                old_content = f.read()

        if current_content != old_content:
            print(f"  [*] 差分あり。更新します。")
            
            # Unified Diff形式で差分を生成
            diff = difflib.unified_diff(
                old_content.splitlines(),
                current_content.splitlines(),
                fromfile='Old', tofile='New', lineterm=''
            )
            diff_text = "\n".join(list(diff))

            # ログ記録
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"\n[{now}] {site['name']} 変更検知\n{diff_text}\n" + "-"*30 + "\n")
            
            # 今回の内容を保存
            with open(save_file, "w", encoding="utf-8") as f:
                f.write(current_content)

            # IFTTT通知
            send_ifttt(site['name'], diff_text)
        else:
            print(f"  [-] 変更なし")
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{now}] {site['name']} チェック完了 (変更なし)\n")

if __name__ == "__main__":
    main()
