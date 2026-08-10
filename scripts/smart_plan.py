"""FactBite Brain: independent AI topic selection for each language."""
import json, os, urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

KEY = os.environ["GEMINI_API_KEY"]
MODEL = os.environ.get("GEMINI_PLAN_MODEL", "gemini-3.5-flash-lite")
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={KEY}"
PLAN = "data/daily_plan.json"
HISTORY = "data/topic_history.json"
SLOTS = ["12:00", "15:00", "18:00", "21:00"]
LANGS = {"tr": "Turkish", "en": "English", "es": "Spanish", "ar": "Arabic"}
CATS = ["general", "history", "language", "health", "animals", "tech", "science", "sports", "news", "culture", "space"]

def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def ask(prompt):
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"response_mime_type": "application/json"}}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as response:
        payload = json.loads(response.read())
    return json.loads(payload["candidates"][0]["content"]["parts"][0]["text"])

def fallback_plan():
    data = [("tr", "animals", "Şaşırtıcı bir hayvan davranışı"), ("en", "space", "A surprising fact about space"), ("es", "science", "Un dato científico sorprendente"), ("ar", "history", "حقيقة تاريخية غريبة")]
    return {"slots": [{"time": t, "language": l, "category": c, "topic": topic, "format": "reel", "reason": "fallback"} for t, (l, c, topic) in zip(SLOTS, data)]}

def main():
    today = datetime.now(ZoneInfo("Europe/Istanbul")).date().isoformat()
    old = load(PLAN, {})
    if old.get("date") == today and len(old.get("slots", [])) == 4 and {x.get("language") for x in old["slots"]} == set(LANGS) and all(x.get("topic") for x in old["slots"]):
        print(json.dumps(old, ensure_ascii=False)); return
    history = load(HISTORY, [])[-120:]
    special = [x for x in load("data/special_days.json", []) if x.get("date") == today]
    prompt = f'''You are the FactBite chief editor. Build today's FOUR independent Reel plans.
Date: {today}
Slots: {SLOTS}
Languages: {json.dumps(LANGS, ensure_ascii=False)}
Allowed categories: {CATS}
Special day today: {json.dumps(special, ensure_ascii=False)}
Recent topics: {json.dumps(history, ensure_ascii=False)}
Rules: exactly one slot per language (tr/en/es/ar); every language MUST choose its own topic and it may be completely unrelated to the other languages; do not translate the same topic across languages; avoid recent/near-duplicate topics; prefer interesting, visual, factual topics suitable for a 20-25 second Reel; use current-interest signals when available; mix categories; sports/news should be factual context, not generic breaking-news feeds; special days may influence the most relevant language.
Return JSON only: {{"slots":[{{"time":"12:00","language":"tr","category":"animals","topic":"...","format":"reel","reason":"..."}},{{"time":"15:00","language":"en","category":"space","topic":"...","format":"reel","reason":"..."}},{{"time":"18:00","language":"es","category":"science","topic":"...","format":"reel","reason":"..."}},{{"time":"21:00","language":"ar","category":"history","topic":"...","format":"reel","reason":"..."}}]}}'''
    try:
        plan = ask(prompt)
        slots = plan.get("slots", []) if isinstance(plan, dict) else []
        if len(slots) != 4 or {x.get("language") for x in slots} != set(LANGS) or any(not x.get("topic") for x in slots):
            plan = fallback_plan()
    except Exception:
        plan = fallback_plan()
    plan = {"date": today, "slots": plan["slots"], "special": special}
    os.makedirs("data", exist_ok=True)
    with open(PLAN, "w", encoding="utf-8") as f: json.dump(plan, f, ensure_ascii=False, indent=2)
    print(json.dumps(plan, ensure_ascii=False))

if __name__ == "__main__": main()
