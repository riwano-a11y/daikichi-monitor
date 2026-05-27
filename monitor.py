import os
import requests
import json
from bs4 import BeautifulSoup

# 金庫から安全にSlackのURLを読み込みます
WEBHOOK = os.environ.get("SLACK_WEBHOOK")
STATE_FILE = "daikichi_monitor_state.json"
TARGET_URL = "https://www.kaitori-daikichi.jp/open/category/new/"

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f: json.dump(state, f, indent=4)

def send_slack_notification(message):
    if not WEBHOOK: return
    payload = {"text": message}
    try: requests.post(WEBHOOK, json=payload, timeout=10)
    except: pass

def main():
    state = load_state()
    print("大吉の新店オープン情報を確認中...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Asset-Monitor/1.0"}
    
    try:
        r = requests.get(TARGET_URL, headers=headers, timeout=15)
        if r.status_code != 200:
            print(f"サイトアクセスエラー: {r.status_code}")
            return
            
        soup = BeautifulSoup(r.text, 'html.parser')
        shop_items = []
        
        # 大吉のサイト構造から記事を抽出
        for article in soup.find_all(['article', 'div'], class_=['post', 'type-post', 'loop-item', 'entry-item']):
            link_tag = article.find('a')
            if link_tag and link_tag.get('href'):
                url = link_tag.get('href')
                title = article.text.strip().split('\n')[0]
                shop_items.append({"url": url, "title": title})
                
        if not shop_items:
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if '/open/' in href and href != TARGET_URL:
                    title = link.text.strip() or "新店オープン情報"
                    if {"url": href, "title": title} not in shop_items:
                        shop_items.append({"url": href, "title": title})

        print(f"発見した店舗数: {len(shop_items)}")

        for item in shop_items:
            url = item["url"]
            raw_title = item["title"]
            
            # 店舗名だけを綺麗に抽出（例: 「〇〇店」）
            clean_name = raw_title.replace("【新店オープン】", "").replace("新店オープン", "").replace("オープン", "")
            clean_name = clean_name.replace("買取の大吉", "").replace("大吉", "").strip()
            
            state_key = url

            # まだ通知したことがない新店の場合のみ、1回だけ通知する（重複ガード）
            if state_key not in state:
                state[state_key] = {"status": "published"}
                
                # 🎯 スクショでご指定いただいた「銀座屋のあの最高に綺麗なレイアウト」を完全移植！
                message = (
                    f"⭐ 買取の大吉 [新店オープン] ✨新店オープン検知✨\n"
                    f"【詳細】：大吉 「{clean_name}」 がOPENします！\n"
                    f"🔗 公式告知ページ：\n"
                    f"{url}\n"
                    f"----------------------------------------"
                )
                send_slack_notification(message)

    except Exception as e:
        print(f"エラー発生: {e}")
                
    save_state(state)

if __name__ == "__main__":
    main()
