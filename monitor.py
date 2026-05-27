import os
import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

WEBHOOK = os.environ.get("SLACK_WEBHOOK")
STATE_FILE = "daikichi_monitor_state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        try: with open(STATE_FILE, "r") as f: return json.load(f)
        except: return []
    return []

def save_state(state):
    try: with open(STATE_FILE, "w") as f: json.dump(state, f, indent=4)
    except: pass

def send_slack_notification(message):
    if not WEBHOOK: return
    payload = {"text": message}
    try: requests.post(WEBHOOK, json=payload, timeout=10)
    except: pass

def main():
    url = "https://www.kaitori-daikichi.jp/open/category/new/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Monitor/1.0"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200: return
    except: return

    soup = BeautifulSoup(r.text, "html.parser")
    state = load_state()
    new_state = state.copy()
    
    articles = soup.find_all("article")
    found_count = 0
    
    for article in articles:
        title_tag = article.find(["h2", "h3", "p"], class_=lambda x: x and 'title' in x.lower())
        if not title_tag: title_tag = article.find(["h2", "h3"])
        link_tag = article.find("a")
        
        if title_tag and link_tag:
            clean_title = " ".join(title_tag.text.strip().split())
            store_url = link_tag["href"]
            if "/open/" not in store_url or "category" in store_url: continue
            if store_url.startswith("/"): store_url = f"https://www.kaitori-daikichi.jp{store_url}"
            if store_url in state: continue
                
            found_count += 1
            msg = f"💎 買取大吉 [公式] ✨新店オープン検知✨\n 【詳細】：{clean_title}\n 🔗 {store_url}"
            send_slack_notification(msg)
            new_state.append(store_url)
            
    save_state(new_state)
    
    # 🕒 日本の現在時刻をゲット
    tokyo_time = datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%H:%M:%S')
    
    if found_count == 0:
        send_slack_notification(f"🟢 【買取大吉監視】定期巡回完了（正常稼働中） ➔ タイムスタンプ: 【{tokyo_time}】")

if __name__ == "__main__":
    main()
