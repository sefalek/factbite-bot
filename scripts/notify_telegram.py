"""Send a FactBite workflow notification to Telegram."""
import json
import os
import urllib.parse
import urllib.request

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
MESSAGE = os.environ.get("TELEGRAM_MESSAGE", "FactBite bildirimi")

if not TOKEN or not CHAT_ID:
    print("Telegram notification skipped: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is not configured.")
    raise SystemExit(0)

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
data = urllib.parse.urlencode({
    "chat_id": CHAT_ID,
    "text": MESSAGE,
    "disable_web_page_preview": "true",
}).encode("utf-8")
req = urllib.request.Request(url, data=data, method="POST")
with urllib.request.urlopen(req) as resp:
    result = json.loads(resp.read())
if not result.get("ok"):
    raise RuntimeError(result)
print("Telegram notification sent.")
