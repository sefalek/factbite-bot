import json, os
from datetime import datetime
from zoneinfo import ZoneInfo

p = json.load(open("data/daily_plan.json", encoding="utf-8"))
now = datetime.now(ZoneInfo("Europe/Istanbul"))
time = now.strftime("%H:%M")
special = p.get("special") or []
is_special = (time == "13:30" and bool(special))

if is_special:
    slot = {"language": "tr", "category": "culture", "format": "reel", "topic": special[0].get("name", "Özel Gün")}
    name = special[0].get("name", "Özel Gün")
else:
    slots = p.get("slots", [])
    slot = next((x for x in slots if x.get("time") == time), slots[0] if slots else {})
    name = ""

lang = slot.get("language", "tr")
cat = slot.get("category", "general")
fmt = slot.get("format", "reel")
topic = slot.get("topic", "")

out = os.environ.get("GITHUB_OUTPUT")
if out:
    with open(out, "a", encoding="utf-8") as f:
        f.write(f"category={cat}\nformat={fmt}\nlanguage={lang}\ntopic={topic}\nspecial={name}\nis_special={str(is_special).lower()}\n")
print(lang, cat, fmt, topic, name, is_special)
