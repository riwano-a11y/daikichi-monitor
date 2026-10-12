#!/usr/bin/env python3
from pathlib import Path
import py_compile
import re
import shutil
import sys

target = Path("/root/ip-monitor/daikichi_monitor.py")
backup = target.with_suffix(".py.before_format")

if not target.exists():
    print(f"ERROR: {target} が見つかりません")
    sys.exit(1)

source = target.read_text(encoding="utf-8")
if "# NOTIFICATION_FORMAT_V2" in source:
    print("FORMAT_UPDATE_OK (すでに反映済み)")
    sys.exit(0)

if "def notify_slack(title, link):" not in source:
    print("ERROR: notify_slack が見つかりません")
    sys.exit(1)

old_line = "    phone, address = fetch_store_details(link)\n"
new_lines = """    phone, address = fetch_store_details(link)
    # NOTIFICATION_FORMAT_V2
    name_match = re.search(r"『([^』]+)』", title)
    store_name = name_match.group(1).strip() if name_match else title.strip()
"""
if old_line not in source:
    print("ERROR: 詳細取得部分が見つかりません。先に update_details.py を実行してください")
    sys.exit(1)
source = source.replace(old_line, new_lines, 1)

message_pattern = re.compile(
    r'(?ms)^    text = f"""NEW DAIKICHI STORE\n.*?^    """'
)
new_message = '''    text = f"""NEW DAIKICHI STORE

店舗名：{store_name}
電話番号：{phone}
住所：{address}
URL：{link}
    """'''
source, count = message_pattern.subn(new_message, source, count=1)
if count != 1:
    print("ERROR: 通知文の置換対象が見つかりません")
    sys.exit(1)

shutil.copy2(target, backup)
try:
    target.write_text(source, encoding="utf-8", newline="\n")
    py_compile.compile(str(target), doraise=True)
except Exception as error:
    shutil.copy2(backup, target)
    print(f"ERROR: {error}")
    sys.exit(1)

print("FORMAT_UPDATE_OK")
print("通知形式を店舗名・電話番号・住所・URLの4行に変更しました。")
