import os
import requests
import json
from bs4 import BeautifulSoup

# GitHubの金庫からSlackのURLを読み込みます
WEBHOOK = os.environ.get("SLACK_WEBHOOK")
STATE_FILE = "daikichi_monitor_state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f: return json.load(f)
        except: return []
    return []

def save_state(state):
    try:
        with open(STATE_FILE, "w") as f: json.dump(state, f, indent=4)
    except: pass

def send_slack_notification(message):
    if not WEBHOOK: return
    payload = {"text": message}
    try: requests.post(WEBHOOK, json=payload, timeout=10)
    except: pass

def main():
    url = "https://www.kaitori-daikichi.jp/store-search/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Monitor/1.0"}
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200: return
    except:
        return

    soup = BeautifulSoup(r.text, "html.parser")
    state = load_state()
    new_state = state.copy()
    
    # 大吉の公式サイトから新着オープンの店舗リストを抜き出します
    stores = soup.find_all("div", class_="p-store-search__new-item")
    
    for store in stores:
        title_tag = store.find("p", class_="p-store-search__new-title")
        link_tag = store.find("a")
        
        if title_tag and link_tag:
            store_name = title_tag.text.strip()
            store_url = link_tag["href"]
            
            # すでに通知済みの店舗ならスルーします
            if store_url in state:
                continue
                
            # 🎉 新着店舗を見つけたら、銀座屋風のかっこいいレイアウトで通知！
            msg = (
                f"✨🈚 **買取大吉 新着オープン情報** 🈚✨\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🏬 **店舗名**: {store_name}\n"
                f"🔗 **URL**: {store_url}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            send_slack_notification(msg)
            new_state.append(store_url)
            
    save_state(new_state)

if __name__ == "__main__":
    main()
