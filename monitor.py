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
    # 🎯 ご指定いただいた、本当の新着オープン公式ページを見に行きます
    url = "https://www.kaitori-daikichi.jp/open/category/new/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Monitor/1.0"}
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200: return
    except:
        return

    soup = BeautifulSoup(r.text, "html.parser")
    state = load_state()
    new_state = state.copy()
    
    # 大吉の新しいお知らせ記事（カード）をすべてループ処理します
    articles = soup.find_all("article")
    
    for article in articles:
        # 記事のタイトル（例：【愛知県名古屋市】 5月20日 『買取大吉 大曽根店』 OPEN!!）
        title_tag = article.find(["h2", "h3", "p"], class_=lambda x: x and 'title' in x.lower())
        if not title_tag:
            title_tag = article.find(["h2", "h3"])
            
        # 記事のリンク（例：https://www.kaitori-daikichi.jp/open/open-5124360）
        link_tag = article.find("a")
        
        if title_tag and link_tag:
            raw_title = title_tag.text.strip()
            store_url = link_tag["href"]
            
            # 余計な文字や改行を綺麗にお掃除
            clean_title = " ".join(raw_title.split())
            
            # 必要な個別ページURLだけを対象にする
            if "/open/" not in store_url or "category" in store_url:
                continue
                
            if store_url.startswith("/"):
                store_url = f"https://www.kaitori-daikichi.jp{store_url}"
                
            # すでに通知済みのURLなら重複なのでスルー
            if store_url in state:
                continue
                
            # 🎯 スクショと寸分違わぬ「完全再現」の銀座屋風レイアウト
            msg = (
                f"💎 買取大吉 [公式オープン] ✨新店オープン検知✨\n"
                f" 【詳細】：{clean_title}\n"
                f" 🔗 公式告知ページ: {store_url}\n"
                f"----------------------------------------"
            )
            send_slack_notification(msg)
            new_state.append(store_url)
            
    save_state(new_state)

if __name__ == "__main__":
    main()
