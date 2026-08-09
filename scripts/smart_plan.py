"""FactBite Brain: one lightweight daily plan, reused by all publishing slots."""
import json, os, urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

KEY = os.environ["GEMINI_API_KEY"]
MODEL = os.environ.get("GEMINI_PLAN_MODEL", "gemini-3.5-flash-lite")
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={KEY}"
PLAN = "data/daily_plan.json"
HISTORY = "data/topic_history.json"
SLOTS = ["08:17", "10:17", "12:17", "15:17", "18:17", "22:17"]
CATS = ["general", "history", "language", "health", "animals", "tech", "science", "sports", "news", "culture", "space"]

def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def ask(prompt):
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"response_mime_type": "application/json"},
    }).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as response:
        payload = json.loads(response.read())
    text = payload["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text)

def fallback_plan():
    cats = ["general", "history", "science", "animals", "tech", "culture"]
    return {
        "slots": [
            {"time": time, "category": category, "format": "classic", "reason": "fallback"}
            for time, category in zip(SLOTS, cats)
        ]
    }

def main():
    today = datetime.now(ZoneInfo("Europe/Istanbul")).date().isoformat()
    old = load(PLAN, {})
    if old.get("date") == today and len(old.get("slots", [])) == 6:
        print(json.dumps(old, ensure_ascii=False))
        return

    history = load(HISTORY, [])[-80:]
    special = [x for x in load("data/special_days.json", []) if x.get("date") == today]
    prompt = f"""You are FactBite Brain. Build today's six-slot content plan.
Date: {today}
Allowed categories: {CATS}
Slots: {SLOTS}
Special day today: {json.dumps(special, ensure_ascii=False)}
Recent topics: {json.dumps(history, ensure_ascii=False)}
Keep the brand coherent. Favor current interest but preserve evergreen variety.
Never repeat recent topics or close variants.
Sports/news must be framed as facts/context, not a generic news feed.
No category over 2 of 6 unless there is an exceptional major event.
Return JSON only with exactly six slots: {{"slots":[{{"time":"08:17","category":"science","format":"mystery","reason":"..."}}]}}"""

    try:
        plan = ask(prompt)
        if not isinstance(plan, dict) or not isinstance(plan.get("slots"), list) or len(plan["slots"]) != 6:
            plan = fallback_plan()
    except Exception:
        plan = fallback_plan()

    plan = {"date": today, "slots": plan["slots"], "special": special}
    os.makedirs("data", exist_ok=True)
    with open(PLAN, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)
    print(json.dumps(plan, ensure_ascii=False))

if __name__ == "__main__":
    main()
