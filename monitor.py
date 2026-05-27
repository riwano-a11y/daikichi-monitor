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
    # 🎯 最新の新着・店舗一覧ページを見に行きます
    url = "https://www.kaitori-daikichi.jp/store/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Monitor/1.0"}
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200: return
    except:
        return

    soup = BeautifulSoup(r.text, "html.parser")
    state = load_state()
    new_state = state.copy()
    
    # 🎯 2026年現在の大吉の店舗リンク・カードをすべて抽出します
    links = soup.find_all("a")
    found_any = False
    
    for link in links:
        href = link.get("href", "")
        # /store/xxxxx という店舗個別URLだけをターゲットにします
        if "/store/" in href and href != "https://www.kaitori-daikichi.jp/store/" and href != "/store/":
            # フルURLに整形
            if href.startswith("/"):
                store_url = f"https://www.kaitori-daikichi.jp{href}"
            else:
                store_url = href
                
            # テキスト（店舗名）を取得
            store_name = link.text.strip()
            if not store_name or "一覧" in store_name or "検索" in store_name:
                continue
                
            # すでに通知済みの店舗ならスルー
            if store_url in state:
                continue
                
            found_any = True
            # 🎉 銀座屋風のかっこいいレイアウトで通知！
            msg = (
                f"✨🈚 **買取大吉 新着店舗情報** 🈚✨\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🏬 **店舗名**: {store_name}\n"
                f"🔗 **URL**: {store_url}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            send_slack_notification(msg)
            new_state.append(store_url)
            
    # テスト用に、もし1件でも新しいものがあれば保存
    save_state(new_state)
    print(f"処理完了。新着通知対象あり: {found_any}")

if __name__ == "__main__":
    main()
