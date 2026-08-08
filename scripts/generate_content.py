"""
generate_content.py
Generate one FactBite topic in Turkish, English, Spanish and Arabic plus
metadata used by carousel, Reel, Story and Facebook distribution.
"""
import json
import os
import urllib.request

API_KEY = os.environ["GEMINI_API_KEY"]
MODEL = "gemini-flash-latest"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"
CATEGORY = os.environ.get("CATEGORY", "general")
HISTORY_PATH = "data/topic_history.json"

CATEGORY_INSTRUCTIONS = {
    "history": "Konu: tarih ve kultur. Az bilinen bir tarihi olay veya kulturel gelenekle ilgili sasirtici bir bilgi ver.",
    "language": "Konu: dil ve kelime kokenleri. Bir kelimenin ilginc kokeni veya farkli dillerdeki ilginc hikayesiyle ilgili bilgi ver.",
    "health": "Konu: insan vucudu ve saglik. Vucutla ilgili sasirtici, bilimsel olarak dogrulanmis ve abartisiz bir bilgi ver.",
    "animals": "Konu: hayvanlar ve doga. Hayvan davranislari veya doga olaylariyla ilgili sasirtici bir bilgi ver.",
    "tech": "Konu: teknoloji ve icatlar. Bir icadin hikayesi veya teknoloji tarihiyle ilgili ilginc bir bilgi ver.",
    "science": "Konu: bilim ve uzay. Fizik, astronomi veya biyoloji alanindan sasirtici bir bilgi ver.",
    "general": "Bilim, tarih, doga, uzay, insan vucudu, dil, hayvanlar gibi konulardan olabilir.",
}

JSON_EXAMPLE = """{
  "tr": {"headline": "kisa carpici baslik (max 8 kelime)", "body": "1-2 cumlelik aciklama"},
  "en": {"headline": "...", "body": "..."},
  "es": {"headline": "...", "body": "..."},
  "ar": {"headline": "...", "body": "..."},
  "reel_hook": {"tr": "ilk 2 saniyede merak uyandiran cok kisa hook", "en": "..."},
  "story_question": {"tr": "cevabi tahmin ettiren soru", "en": "...", "es": "...", "ar": "..."},
  "story_options": ["1", "2", "3"],
  "hashtags": ["#FactBite", "#Science", "#Space"],
  "cta": {"tr": "Her gun yeni bir sey ogren. @factbitee", "en": "Learn something new every day. @factbitee", "es": "Aprende algo nuevo cada dia. @factbitee", "ar": "تعلم شيئًا جديدًا كل يوم. @factbitee"}
}"""


def load_history():
    try:
        with open(HISTORY_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def build_history_text(history):
    recent = history[-200:]
    if not recent:
        return "HENUZ ONCEKI KONU YOK."
    return "\n".join(
        f"- [{x.get('category','general')}] {x.get('headline','')} — {x.get('body','')}"
        for x in recent
    )


def request_fact(history_text):
    prompt = (
        "Bugun icin ilginc, dogrulanabilir, sasirtici bir genel kultur bilgisi uret.\n"
        + CATEGORY_INSTRUCTIONS.get(CATEGORY, CATEGORY_INSTRUCTIONS["general"]) + "\n"
        "Cok bilinen klise bilgilerden kac. Sosyal medyada merak uyandiracak ama clickbait olmayan bir konu sec.\n"
        "GECMIS KONULARIN HICBIRINI TEKRARLAMA. Ayni olay, nesne, kisi veya mekanin baska ayrintisini anlatarak dolanma. Konu belirgin sekilde farkli olsun.\n\n"
        "GECMIS KONULAR:\n" + history_text + "\n\n"
        "Bilgi gercekten dogrulanabilir olmali; uydurma istatistik, sahte alinti, kesin olmayan iddia veya sansasyonel abartma kullanma.\n"
        "Saglik konusunda teshis, tedavi onerisi veya korku dili kullanma.\n"
        "Tam olarak su JSON formatini dondur, baska aciklama ekleme:\n\n" + JSON_EXAMPLE + "\n\n"
        "Dort dilde ayni bilgiyi dogal ve yerellestirilmis sekilde anlat. Arapca modern standart Arapca olsun.\n"
        "reel_hook alaninda 1-2 saniyede okunabilecek, merak uyandiran ama cevabi hemen vermeyen kisa metinler ver.\n"
        "story_question ve story_options basit bir quiz icin uygun olsun; options 3 kisa secenek olsun.\n"
        "hashtags alaninda 5-8 adet konuya dogrudan ilgili hashtag sec. #FactBite ilk sirada olsun. Spam etiket kullanma.\n"
        "CTA metinlerinde kullaniciyi @factbitee hesabini takip etmeye tesvik et."
    )
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"response_mime_type": "application/json"},
    }).encode("utf-8")
    req = urllib.request.Request(API_URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def main():
    history = load_history()
    fact = request_fact(build_history_text(history))
    fact["_category"] = CATEGORY

    history.append({
        "category": CATEGORY,
        "headline": fact["tr"]["headline"],
        "body": fact["tr"]["body"],
    })
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history[-200:], f, ensure_ascii=False, indent=2)

    with open("fact.json", "w", encoding="utf-8") as f:
        json.dump(fact, f, ensure_ascii=False, indent=2)

    print("Wrote fact.json (category:", CATEGORY, ")")


if __name__ == "__main__":
    main()
