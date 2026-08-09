"""FactBite Brain: one lightweight daily plan, reused by all six publishing slots."""
import json, os, urllib.parse, urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

KEY=os.environ["GEMINI_API_KEY"]
MODEL=os.environ.get("GEMINI_PLAN_MODEL","gemini-3.5-flash-lite")
URL=f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={KEY}"
PLAN="data/daily_plan.json"
HISTORY="data/topic_history.json"
CATS=["general","history","language","health","animals","tech","science","sports","news","culture","space"]
SLOTS=["08:17","10:17","12:17","15:17","18:17","22:17"]

def load(p,default):
    try:
        with open(p,encoding="utf-8") as f:return json.load(f)
    except Exception:return default

def ask(prompt):
    body=json.dumps({"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"response_mime_type":"application/json"}}).encode()
    req=urllib.request.Request(URL,data=body,headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req) as r:return json.loads(json.loads(r.read())["candidates"][0]["content"]["parts"][0]["text"])

def main():
    today=datetime.now(ZoneInfo("Europe/Istanbul")).date().isoformat()
    old=load(PLAN,{})
    if old.get("date")==today and len(old.get("slots",[]))==6:
        print(json.dumps(old,ensure_ascii=False)); return
    history=load(HISTORY,[])[-80:]
    special=load("data/special_days.json",[])
    today_special=[x for x in special if x.get("date")==today]
    prompt=f'''You are FactBite Brain. Build today's six-slot content plan.\nDate: {today}\nAllowed categories: {CATS}\nSlots: {SLOTS}\nSpecial day today: {today_special}\nRecent topics: {json.dumps(history,ensure_ascii=False)}\nRules: keep FactBite coherent; favor current-interest subjects but preserve 30% evergreen variety; never repeat recent topics or close variants; sports/news are allowed but must be framed as facts/context, not a generic news feed; do not let one category exceed 2 of 6 slots unless there is an exceptional major event. Return JSON only: {{"slots":[{{"time":"08:17","category":"science","format":"mystery","reason":"..."}}]}}. Use exactly the six slots.''' 
    try: plan=ask(prompt)
    except Exception:
        # Safe fallback: deterministic rotation; publishing can continue if planning quota is unavailable.
        plan={"slots":[{"time":t,"category":c,"format":"classic","reason":"fallback"} for t,c in zip(SLOTS,["general","history","science","animals","tech","culture"])]}
    plan={"date":today,"slots":plan.get("slots",[]),"special":today_special}
    os.makedirs("data",exist_ok=True)
    with open(PLAN,"w",encoding="utf-8") as f:json.dump(plan,f,ensure_ascii=False,indent=2)
    print(json.dumps(plan,ensure_ascii=False))

if __name__=="__main__":main()
