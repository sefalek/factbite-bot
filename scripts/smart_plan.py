"""FactBite Brain: independent AI topic selection by language for every daily slot."""
import json, os, urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo
KEY=os.environ["GEMINI_API_KEY"]; MODEL=os.environ.get("GEMINI_PLAN_MODEL","gemini-3.5-flash-lite"); URL=f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={KEY}"
PLAN="data/daily_plan.json"; HISTORY="data/topic_history.json"
SLOTS=["08:17","10:17","12:17","13:30","15:17","18:17","22:17"]
LANGS=["tr","en","es","ar","tr","en","es"]
CATS=["general","history","language","health","animals","tech","science","sports","news","culture","space"]
def load(path,default):
 try:
  with open(path,encoding="utf-8") as f:return json.load(f)
 except Exception:return default
def ask(prompt):
 body=json.dumps({"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"response_mime_type":"application/json"}}).encode(); req=urllib.request.Request(URL,data=body,headers={"Content-Type":"application/json"})
 with urllib.request.urlopen(req) as r:return json.loads(json.loads(r.read())["candidates"][0]["content"]["parts"][0]["text"])
def fallback_plan():
 cats=["animals","space","science","history","tech","culture","general"]
 topics=["Şaşırtıcı bir hayvan gerçeği","A surprising space fact","Un dato científico sorprendente","حقيقة تاريخية غريبة","An unexpected technology fact","Un dato cultural curioso","A fact that sounds impossible but is true"]
 return {"slots":[{"time":t,"language":l,"category":c,"topic":topic,"format":"reel","reason":"fallback"} for t,l,c,topic in zip(SLOTS,LANGS,cats,topics)]}
def main():
 today=datetime.now(ZoneInfo("Europe/Istanbul")).date().isoformat(); old=load(PLAN,{})
 if old.get("date")==today and len(old.get("slots",[]))==7 and all(x.get("language") and x.get("topic") for x in old["slots"]):print(json.dumps(old,ensure_ascii=False));return
 history=load(HISTORY,[])[-120:]; special=[x for x in load("data/special_days.json",[]) if x.get("date")==today]
 prompt=f'''You are FactBite chief editor. Build today's seven independent Reel plans. Date: {today}. Slots: {SLOTS}. Required language by slot: {LANGS}. Allowed categories: {CATS}. Special day: {json.dumps(special,ensure_ascii=False)}. Recent topics: {json.dumps(history,ensure_ascii=False)}.
Rules: every slot gets its own topic; the topic is chosen for that slot's target language/audience; topics can be completely different across languages and slots; never translate one topic into another language; avoid recent/near duplicates; favor current interest, strong curiosity, visual potential and factual verifiability; sports/news are context/facts, not generic breaking-news; mix categories; special-day content may use the relevant slot but does not replace the normal language rotation. Return JSON only with exactly seven slots using the supplied times and languages.
Schema: {{"slots":[{{"time":"08:17","language":"tr","category":"animals","topic":"...","format":"reel","reason":"..."}}]}}'''
 try:
  plan=ask(prompt); slots=plan.get("slots",[]) if isinstance(plan,dict) else []
  if len(slots)!=7 or [x.get("language") for x in slots]!=LANGS or [x.get("time") for x in slots]!=SLOTS or any(not x.get("topic") for x in slots):plan=fallback_plan()
 except Exception:plan=fallback_plan()
 plan={"date":today,"slots":plan["slots"],"special":special};os.makedirs("data",exist_ok=True)
 with open(PLAN,"w",encoding="utf-8") as f:json.dump(plan,f,ensure_ascii=False,indent=2)
 print(json.dumps(plan,ensure_ascii=False))
if __name__=="__main__":main()
