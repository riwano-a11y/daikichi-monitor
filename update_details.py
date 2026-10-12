from pathlib import Path
import py_compile
import shutil
import sys

path = Path("/root/ip-monitor/daikichi_monitor.py")
backup = Path("/root/ip-monitor/daikichi_monitor.py.before_github_update")

if not path.exists():
    print("ERROR: daikichi_monitor.py not found")
    sys.exit(1)

source = path.read_text(encoding="utf-8")
shutil.copy2(path, backup)

has_re_import = any(line.strip() == "import re" for line in source.splitlines())
if not has_re_import:
    source = source.replace("import os\n", "import os\nimport re\n", 1)

if "# DETAILS_UPDATE_V1" in source:
    path.write_text(source, encoding="utf-8")
    py_compile.compile(str(path), doraise=True)
    print("UPDATE_OK_V2")
    sys.exit(0)

details_code = r'''
# DETAILS_UPDATE_V1
def fetch_store_details(link):
    phone = "記載なし"
    address = "記載なし"
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(link, headers=headers, timeout=20)
        response.raise_for_status()
        page_text = BeautifulSoup(response.text, "html.parser").get_text("\n", strip=True)

        phone_match = re.search(
            r"(?:電話番号|TEL)[：:\s]*([0-9０-９()\-ー−‐–\s]{10,})",
            page_text,
            re.IGNORECASE,
        )
        if phone_match:
            raw_phone = phone_match.group(1)
            raw_phone = raw_phone.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
            digits = re.sub(r"\D", "", raw_phone)
            if len(digits) >= 10:
                phone = digits

        address_match = re.search(
            r"(?:住所|所在地)[：:\s]*([^\n]+)",
            page_text,
        )
        if address_match:
            address = address_match.group(1).strip()
    except Exception as error:
        print(f"Detail fetch error for {link}: {error}")

    return phone, address


'''

anchor = "def notify_slack(title, link):"
if anchor not in source:
    print("ERROR: notify_slack function not found")
    sys.exit(1)

source = source.replace(anchor, details_code + anchor, 1)
source = source.replace(
    "def notify_slack(title, link):\n",
    "def notify_slack(title, link):\n    phone, address = fetch_store_details(link)\n",
    1,
)

old_text = """{title}

URL:
{link}"""
new_text = """{title}

電話番号:
{phone}

住所:
{address}

URL:
{link}"""
if old_text not in source:
    print("ERROR: notification text not found")
    sys.exit(1)

source = source.replace(old_text, new_text, 1)
path.write_text(source, encoding="utf-8")

try:
    py_compile.compile(str(path), doraise=True)
except Exception as error:
    shutil.copy2(backup, path)
    print(f"ERROR: syntax check failed; restored backup: {error}")
    sys.exit(1)

print("UPDATE_OK")
