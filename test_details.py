import sys
sys.path.insert(0, "/root/ip-monitor")
import daikichi_monitor as monitor

url = "https://www.kaitori-daikichi.jp/open/open-5161401/"
phone, address = monitor.fetch_store_details(url)
print("PHONE:", phone)
print("ADDRESS:", address)
