#!/usr/bin/env python3
from pathlib import Path
import py_compile
import re
import shutil
import sys

target = Path("/root/ip-monitor/daikichi_monitor.py")
backup = target.with_suffix(".py.before_format")

if not target.exists():
    print("ERROR_1: target file not found")
    sys.exit(1)

source = target.read_text(encoding="utf-8")
if "# NOTIFICATION_FORMAT_V2" in source:
    print("FORMAT_UPDATE_OK")
    sys.exit(0)

lines = source.splitlines(keepends=True)

detail_index = next(
    (i for i, line in enumerate(lines)
     if "phone, address = fetch_store_details(link)" in line),
    None
)
message_start = next(
    (i for i, line in enumerate(lines)
     if 'text = f"""NEW DAIKICHI STORE' in line),
    None
)

if detail_index is None:
    print("ERROR_2: details line not found")
    sys.exit(1)
if message_start is None:
    print("ERROR_3: message start not found")
    sys.exit(1)

message_end = next(
    (i for i in range(message_start + 1, len(lines))
     if '"""' in lines[i]),
    None
)
if message_end is None:
    print("ERROR_4: message end not found")
    sys.exit(1)

indent = re.match(r"\s*", lines[detail_index]).group(0)
detail_block = (
    lines[detail_index]
    + indent + "# NOTIFICATION_FORMAT_V2\n"
    + indent + 'name_match = re.search(r"『([^』]+)』", title)\n'
    + indent + "store_name = name_match.group(1).strip() if name_match else title.strip()\n"
)
lines[detail_index:detail_index + 1] = [detail_block]

# The insertion above shifts the message by two physical lines inside one list item,
# but its list index stays unchanged.
message_block = (
    indent + 'text = f"""NEW DAIKICHI STORE\n\n'
    + "店舗名：{store_name}\n"
    + "電話番号：{phone}\n"
    + "住所：{address}\n"
    + "URL：{link}\n"
    + indent + '"""\n'
)
lines[message_start:message_end + 1] = [message_block]
new_source = "".join(lines)

shutil.copy2(target, backup)
try:
    target.write_text(new_source, encoding="utf-8", newline="\n")
    py_compile.compile(str(target), doraise=True)
except Exception as error:
    shutil.copy2(backup, target)
    print("ERROR_5:", repr(error))
    sys.exit(1)

print("FORMAT_UPDATE_OK")
