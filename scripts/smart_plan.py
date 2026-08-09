"""FactBite Brain: one lightweight daily plan, reused by all publishing slots."""
import json,os,urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo
KEY=os.environ["GEMINI_API_KEY"]; MODEL=os.environ.get("GEMINI_PLAN_MODEL","gemini-3.5-flash-lite"); URL=f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={KEY}"; PLAN="data/daily_plan.json"; HISTORY="data/topic_history.json"
SLOTS=["08:17","10:17","12:17","15:17","18:17","22:17"]; CATS=["general","history","language","health","animals","tech","science","sports","news","culture","space"]
def load(p,d):
 try:
  with open(p,encoding="utf-8") as f:return json.load(f)
 except Exception:return d
def ask(prompt):
 body=json.dumps({"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"response_mime_type":"application/json"}}).encode(); req=urllib.request.Request(URL,data=body,headers={"Content-Type":"application/json"})
 with urllib.request.urlopen(req) as r:return json.loads(json.loads(r.read())["candidates"][0]["content"]["parts"][0]["text"])
def main():
 today=datetime.now(ZoneInfo("Europe/Istanbul")).date().isoformat(); old=load(PLAN,{})
 if old.get("date")==today and len(old.get("slots",[]))==6:print(json.dumps(old,ensure_ascii=False));return
 history=load(HISTORY,[])[-80:]; special=[x for x in load("data/special_days.json",[]) if x.get("date")==today]
 prompt=f'''You are FactBite Brain. Build today's six-slot content plan. Date: {today}. Allowed categories: {CATS}. Slots: {SLOTS}. Special day today: {special}. Recent topics: {json.dumps(history,ensure_ascii=False)}. Keep the brand coherent. Favor current interest but preserve evergreen variety; never repeat recent topics or close variants; sports/news must be framed as facts/context, not a generic news feed; no category over 2 of 6 unless there is an exceptional major event. Return JSON only: {{"slots":[{{"time":"08:17","category":"science","format":"mystery","reason":"..."}}]}} using exactly six slots.'''
 try: plan=ask(prompt)
 except Exception: plan={"slots":[{"time":t,"category":c,"format":"classic","reason":"fallback"} for t,c in zip(SLOTS,["general","history","science","animals","tech","culture"])]
 plan={"date":today,"slots":plan.get("slots",[]),"special":special}; os.makedirs("data",exist_ok=True)
 with open(PLAN,"w",encoding="utf-8") as f:json.dump(plan,f,ensure_ascii=False,indent=2)
 print(json.dumps(plan,ensure_ascii=False))
if __name__=="__main__":main()
