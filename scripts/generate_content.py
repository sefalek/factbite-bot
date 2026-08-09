"""
generate_content.py — FactBite V3
Generates a single topic in TR/EN/ES/AR plus metadata for carousel,
quiz/mystery stories, teaser Reels, hashtags and quality scoring.
"""
import json, os, urllib.request

API_KEY = os.environ["GEMINI_API_KEY"]
MODEL = "gemini-flash-latest"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"
CATEGORY = os.environ.get("CATEGORY", "general")
HISTORY_PATH = "data/topic_history.json"

CATEGORY_INSTRUCTIONS = {
    "history": "Tarih ve kültür: az bilinen ama doğrulanabilir bir olay, gelenek, kişi veya nesne.",
    "language": "Dil ve kelime kökenleri: şaşırtıcı bir etimoloji veya dil hikâyesi.",
    "health": "İnsan vücudu ve sağlık: bilimsel, güvenli, abartısız ve teşhis/tedavi içermeyen bir gerçek.",
    "animals": "Hayvanlar ve doğa: sıra dışı davranış veya doğrulanabilir doğa olgusu.",
    "tech": "Teknoloji ve icatlar: ilginç bir icadın hikâyesi veya beklenmedik teknoloji gerçeği.",
    "science": "Bilim ve uzay: fizik, astronomi, biyoloji veya uzaydan şaşırtıcı bir gerçek.",
    "general": "Bilim, tarih, doğa, uzay, insan, dil, hayvanlar veya teknoloji.",
}

JSON_EXAMPLE = '''{
  "format": "mystery",
  "tr": {"headline": "kısa çarpıcı başlık", "body": "1-2 cümle"},
  "en": {"headline": "...", "body": "..."},
  "es": {"headline": "...", "body": "..."},
  "ar": {"headline": "...", "body": "..."},
  "reel_hook": {"tr": "çok kısa hook", "en": "...", "es": "...", "ar": "..."},
  "story_question": {"tr": "tahmin sorusu", "en": "...", "es": "...", "ar": "..."},
  "story_options": ["A", "B", "C"],
  "hashtags": ["#FactBite", "#..."],
  "cta": {"tr": "Her gün yeni bir şey öğren.", "en": "Learn something new every day.", "es": "Aprende algo nuevo cada día.", "ar": "تعلم شيئًا جديدًا كل يوم."},
  "quality": {"curiosity": 1, "surprise": 1, "shareability": 1, "clarity": 1, "overall": 1},
  "source": {"name": "kaynak adı", "url": "https://..."}
}'''

def load_history():
    try:
        with open(HISTORY_PATH, encoding="utf-8") as f: return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError): return []

def request_fact(history):
    recent = history[-200:]
    history_text = "\n".join(f"- [{x.get('category','general')}] {x.get('headline','')} — {x.get('body','')}" for x in recent) or "HENÜZ ÖNCEKİ KONU YOK."
    prompt = f'''FactBite için tek bir sosyal medya konusu üret.
Kategori: {CATEGORY_INSTRUCTIONS.get(CATEGORY, CATEGORY_INSTRUCTIONS["general"])}
Amaç: sıradan ansiklopedi cümlesi değil, kaydırmayı durduracak gerçek bilgi.
Çok bilinen klişelerden kaçın. Clickbait, uydurma istatistik ve abartı kullanma.
Geçmişteki olay/kişi/nesne/mekânı başka açıdan bile tekrar etme.
Sağlıkta teşhis, tedavi veya korku dili kullanma.
Dört dilde doğal ve yerelleştirilmiş anlat; Arapça modern standart Arapça olsun.
classic, mystery, myth_vs_fact veya question_first formatlarından birini seç.
Story için 3 kısa seçenek üret. #FactBite ilk hashtag olsun; 5-8 alakalı etiket üret.
quality puanlarını 1-10 ver; overall 7'nin altında ise daha güçlü konu seç.
source alanında yalnızca gerçekten bildiğin güvenilir kaynak adı/URL kullan; emin değilsen boş bırak.
reel_hook 1-2 saniyede okunabilecek güçlü bir merak cümlesi olsun.

GEÇMİŞ KONULAR:
{history_text}

Yalnızca şu JSON'u döndür:
{JSON_EXAMPLE}'''
    body = json.dumps({"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"response_mime_type":"application/json"}}).encode()
    req = urllib.request.Request(API_URL, data=body, headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req) as resp: data=json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code in (429, 403):
            print("GEMINI_QUOTA_EXHAUSTED")
        raise
    text=data["candidates"][0]["content"]["parts"][0]["text"].strip()
    if text.startswith("```"):
        text=text.split("```")[1]; text=text[4:] if text.startswith("json") else text
    return json.loads(text.strip())

def main():
    history=load_history(); fact=request_fact(history); quality=fact.get("quality",{})
    fact["_category"]=CATEGORY; fact["_v3"]=True
    history.append({"category":CATEGORY,"headline":fact["tr"]["headline"],"body":fact["tr"]["body"],"format":fact.get("format","classic"),"quality":quality})
    os.makedirs(os.path.dirname(HISTORY_PATH),exist_ok=True)
    with open(HISTORY_PATH,"w",encoding="utf-8") as f: json.dump(history[-200:],f,ensure_ascii=False,indent=2)
    with open("fact.json","w",encoding="utf-8") as f: json.dump(fact,f,ensure_ascii=False,indent=2)
    print("V3 fact generated:",CATEGORY,fact.get("format"),quality)

if __name__=="__main__": main()
