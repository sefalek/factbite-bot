"""FactBite V4 content generator: one AI-selected topic per language/slot."""
import json, os, urllib.request, urllib.error
API_KEY=os.environ["GEMINI_API_KEY"]
MODEL=os.environ.get("GEMINI_CONTENT_MODEL","gemini-3.5-flash-lite")
API_URL=f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"
CATEGORY=os.environ.get("CATEGORY","general")
FORMAT=os.environ.get("CONTENT_FORMAT","reel")
LANGUAGE=os.environ.get("LANGUAGE","tr")
TOPIC=os.environ.get("TOPIC","")
SPECIAL_NAME=os.environ.get("SPECIAL_DAY","")
HISTORY_PATH="data/topic_history.json"
CATEGORY_INSTRUCTIONS={"history":"Tarih ve kültür: az bilinen ama doğrulanabilir olay, gelenek, kişi veya nesne.","language":"Dil ve kelime kökenleri: şaşırtıcı ve doğrulanabilir etimoloji.","health":"İnsan vücudu ve sağlık: bilimsel, güvenli, abartısız; teşhis/tedavi yok.","animals":"Hayvanlar ve doğa: sıra dışı doğrulanabilir davranış veya olgu.","tech":"Teknoloji ve icatlar: ilginç icat veya beklenmedik teknoloji gerçeği.","science":"Bilim ve uzay: fizik, astronomi, biyoloji veya uzaydan şaşırtıcı gerçek.","sports":"Spor: sporun tarihi, kuralları, teknoloji veya şaşırtıcı doğrulanabilir bağlam; maç sonucu haberi değil.","news":"Gündem: güncel olayın arkasındaki doğrulanabilir bağlam/fact; sansasyonel haber dili değil.","culture":"Popüler kültür, sanat, coğrafya ve toplumdan doğrulanabilir şaşırtıcı bilgi.","space":"Uzay ve astronomiden doğrulanabilir, görselleştirilebilir bilgi.","general":"Bilim, tarih, doğa, uzay, insan, dil, hayvanlar veya teknoloji."}
LANG_NAMES={"tr":"Turkish","en":"English","es":"Spanish","ar":"Arabic"}

def load_history():
 try:
  with open(HISTORY_PATH,encoding="utf-8") as f:return json.load(f)
 except (FileNotFoundError,json.JSONDecodeError):return []

def ask(prompt):
 body=json.dumps({"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"response_mime_type":"application/json"}}).encode(); req=urllib.request.Request(API_URL,data=body,headers={"Content-Type":"application/json"})
 try:
  with urllib.request.urlopen(req) as r:data=json.loads(r.read())
 except urllib.error.HTTPError as e:
  if e.code in (429,403):
   out=os.environ.get("GITHUB_OUTPUT")
   if out:
    with open(out,"a",encoding="utf-8") as f:f.write("quota_exhausted=true\n")
  raise
 text=data["candidates"][0]["content"]["parts"][0]["text"].strip()
 if text.startswith("```"):text=text.split("```")[1].removeprefix("json")
 return json.loads(text.strip())

def main():
 history=load_history()[-200:]
 history_text="\n".join(f"- {x.get('language','')}: {x.get('headline','')}" for x in history) or "YOK"
 special=f"Özel gün: {SPECIAL_NAME}. Uygunsa bu Reel'e doğal biçimde bağla." if SPECIAL_NAME else ""
 language=LANG_NAMES.get(LANGUAGE,LANGUAGE)
 prompt=f'''FactBite için tek bir Reel üret.\nHEDEF DİL: {language} ({LANGUAGE})\nKATEGORİ: {CATEGORY_INSTRUCTIONS.get(CATEGORY,CATEGORY_INSTRUCTIONS["general"])}\nAI EDİTÖRÜNÜN SEÇTİĞİ KONU: {TOPIC}\n{special}\nAmaç: kaydırmayı durduracak, görsel olarak güçlü, gerçek ve doğrulanabilir 20-25 saniyelik Reel. Konuyu başka dillere göre değiştirme; bu slotun konusu yalnızca bu hedef dil/kitle içindir. Doğal, yerel ve konuşma diline yakın yaz. Clickbait, uydurma istatistik ve aşırı iddialardan kaçın. Hook ilk 1-2 saniyede merak yaratmalı ama cevabı hemen vermemeli. 5-8 hashtag üret; #FactBite ilk olsun. Quality 1-10 puanla; overall 8 altındaysa aynı konu içinde daha güçlü bir açı seç.\nGEÇMİŞ:\n{history_text}\n\nJSON ONLY. Reel hedef dil içeriğini {LANGUAGE} alanına koy. Diğer dört dil alanlarını mevcut carousel uyumluluğu için aynı gerçeğin doğal çevirileri olarak doldur; ancak bu slotun yayın dili SADECE {LANGUAGE} olacaktır.\nSchema: {{"format":"reel","tr":{{"headline":"...","body":"..."}},"en":{{"headline":"...","body":"..."}},"es":{{"headline":"...","body":"..."}},"ar":{{"headline":"...","body":"..."}},"reel_hook":{{"tr":"...","en":"...","es":"...","ar":"..."}},"story_question":{{"tr":"...","en":"...","es":"...","ar":"..."}},"story_options":["A","B","C"],"hashtags":["#FactBite"],"cta":{{"tr":"...","en":"...","es":"...","ar":"..."}},"quality":{{"curiosity":1,"surprise":1,"shareability":1,"clarity":1,"overall":1}},"source":{{"name":"","url":""}}}}'''
 fact=ask(prompt); q=fact.get("quality",{})
 if int(q.get("overall",0))<8:raise RuntimeError(f"QUALITY_GATE_REJECTED overall={q.get('overall')}")
 fact.update({"_category":CATEGORY,"_language":LANGUAGE,"_topic":TOPIC,"_v4":True,"_special_day":SPECIAL_NAME})
 history.append({"language":LANGUAGE,"category":CATEGORY,"topic":TOPIC,"headline":fact.get(LANGUAGE,{}).get("headline",""),"body":fact.get(LANGUAGE,{}).get("body",""),"format":"reel","quality":q})
 os.makedirs("data",exist_ok=True)
 with open(HISTORY_PATH,"w",encoding="utf-8") as f:json.dump(history[-200:],f,ensure_ascii=False,indent=2)
 with open("fact.json","w",encoding="utf-8") as f:json.dump(fact,f,ensure_ascii=False,indent=2)
 print("V4 fact generated",LANGUAGE,CATEGORY,TOPIC,q)
if __name__=="__main__":main()
