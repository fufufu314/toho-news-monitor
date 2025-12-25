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
IFTTT_KEY = os.environ.get("IFTTT_KEY")
IFTTT_EVENT = "toho_news_update"
JST = timezone(timedelta(hours=+9), 'JST')

def fetch_content(site):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    try:
        print(f"--- 巡回開始: {site['name']} ---")
        target_url = site['url']
        is_payload = False

        if site.get('format') == 'sunshine_payload':
            is_payload = True
            res_html = requests.get(target_url, headers=headers, timeout=15)
            js_match = re.search(r'/_nuxt/static/[\d]+/theater/gdcs/news/57/payload\.js', res_html.text)
            if js_match:
                target_url = "https://www.cinemasunshine.co.jp" + js_match.group(0)
                print(f"  [→] 最新パス取得: {target_url}")
            else:
                return None

        response = requests.get(target_url, headers=headers, timeout=15)
        if response.status_code != 200: return None

        if is_payload or site.get('format') == 'js_payload':
            match = re.search(r'news:\{(.*?)\}', response.text, re.DOTALL)
            if match:
                raw_text = match.group(0)
                # 文字化け修復
                try:
                    fixed_text = raw_text.encode('latin-1').decode('utf-8')
                except:
                    fixed_text = raw_text
                # HTMLタグ除去
                return BeautifulSoup(fixed_text, "html.parser").get_text("\n", strip=True)
            return None
        else:
            response.encoding = response.apparent_encoding 
            soup = BeautifulSoup(response.text, "html.parser")
            find_args = {"name": site['tag']}
            if 'class' in site: find_args['class_'] = site['class']
            if 'id' in site: find_args['id'] = site['id']
            target_section = soup.find(**find_args)
            return target_section.get_text("\n", strip=True) if target_section else None
    except Exception as e:
        print(f"  [!] エラー: {e}")
        return None

def send_ifttt(site_name, diff_text):
    if not IFTTT_KEY: return
    url = f"https://maker.ifttt.com/trigger/{IFTTT_EVENT}/with/key/{IFTTT_KEY}"
    data = {"value1": f"【{site_name}】更新検知\n\n{diff_text[:800]}"}
    requests.post(url, json=data, timeout=10)

def main():
    if not os.path.exists(CONFIG_FILE): return
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        targets = json.load(f)
    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
    for site in targets:
        current_content = fetch_content(site)
        if current_content is None: continue
        safe_name = re.sub(r'[\\/:*?"<>|]', '_', site['name'])
        save_file = f"last_{safe_name}.txt"
        old_content = ""
        if os.path.exists(save_file):
            with open(save_file, "r", encoding="utf-8") as f:
                old_content = f.read()
        if current_content != old_content:
            diff = difflib.unified_diff(old_content.splitlines(), current_content.splitlines(), fromfile='Old', tofile='New', lineterm='')
            diff_text = "\n".join(list(diff))
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"\n[{now}] {site['name']} 変更検知\n{diff_text}\n" + "-"*30 + "\n")
            with open(save_file, "w", encoding="utf-8") as f:
                f.write(current_content)
            send_ifttt(site['name'], diff_text)
        else:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{now}] {site['name']} 変更なし\n")

if __name__ == "__main__":
    main()
