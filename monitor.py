import requests
from bs4 import BeautifulSoup
import os
import difflib
import json
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
    """設定に基づきサイトから特定セクションの内容を取得"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        print(f"--- 巡回開始: {site['name']} ---")
        response = requests.get(site['url'], headers=headers, timeout=15)
        
        # ステータスコードの確認（200以外はエラー）
        if response.status_code != 200:
            print(f"  [!] アクセス失敗 (Status: {response.status_code})")
            return None

        response.encoding = response.apparent_encoding 
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 検索条件の組み立て
        find_args = { "name": site['tag'] }
        if 'class' in site: find_args['class_'] = site['class']
        if 'id' in site: find_args['id'] = site['id']
        
        target_section = soup.find(**find_args)
        
        if target_section:
            print(f"  [✓] 要素を取得しました ({site['tag']})")
            return target_section.get_text("\n", strip=True)
        else:
            print(f"  [!] 指定された要素が見つかりません: {find_args}")
            return None

    except Exception as e:
        print(f"  [!] 例外が発生しました: {e}")
        return None

def send_ifttt(site_name, diff_text):
    """IFTTT Webhookへ通知を送信"""
    if not IFTTT_KEY:
        print("  [!] IFTTT_KEY未設定のため通知をスキップします。")
        return
    
    url = f"https://maker.ifttt.com/trigger/{IFTTT_EVENT}/with/key/{IFTTT_KEY}"
    # 通知内容を作成（IFTTTの制限を考慮し最大800文字程度にカット）
    message = f"【{site_name}】に更新があります！\n\n{diff_text}"
    data = {"value1": message[:800]}
    
    try:
        res = requests.post(url, json=data)
        if res.status_code == 200:
            print(f"  [✓] IFTTT通知を送信しました。")
        else:
            print(f"  [!] IFTTT送信失敗 (Status: {res.status_code})")
    except Exception as e:
        print(f"  [!] IFTTT連携エラー: {e}")

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

        # サイトごとに保存ファイル名を分ける
        save_file = f"last_{site['name']}.txt"
        old_content = ""
        if os.path.exists(save_file):
            with open(save_file, "r", encoding="utf-8") as f:
                old_content = f.read()

        if current_content != old_content:
            print(f"  [*] 差分を検知しました。記録を更新します。")
            
            # 差分テキストの生成
            diff = difflib.unified_diff(
                old_content.splitlines(),
                current_content.splitlines(),
                fromfile='Old', tofile='New', lineterm=''
            )
            diff_text = "\n".join(list(diff))

            # ログファイルへの詳細記録
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"\n[{now}] {site['name']} 変更検知\n{diff_text}\n" + "-"*30 + "\n")
            
            # 今回の内容を次回用に保存
            with open(save_file, "w", encoding="utf-8") as f:
                f.write(current_content)

            # 変更時のみIFTTTへ飛ばす
            send_ifttt(site['name'], diff_text)
        else:
            print(f"  [-] 変更はありません。")
            # 実行記録のみログに残す
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{now}] {site['name']} チェック完了 (変更なし)\n")

if __name__ == "__main__":
    main()
