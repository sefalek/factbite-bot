"""
generate_content.py
Calls Gemini to produce one FactBite in Turkish, English, Spanish and Arabic.
Keeps a small topic history so the same/similar fact is not generated again.
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
    "language": "Konu: dil ve kelime kokenleri. Bir kelimenin ilginc kokeni veya farkli dillerde karsiligi olmayan bir kavramla ilgili bilgi ver.",
    "health": "Konu: insan vucudu ve saglik. Vucutla ilgili sasirtici, bilimsel olarak dogrulanmis bir bilgi ver.",
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
  "hashtags": ["#FactBite", "#Science", "#Space"]
}"""


def load_history():
    try:
        with open(HISTORY_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def build_history_text(history):
    recent = history[-100:]
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
        "Daha once cok bilinen klise bilgilerden kacin.\n"
        "ASAGIDAKI GECMIS KONULARIN HICBIRINI TEKRARLAMA. Ayni olayin/nesnenin baska bir ayrintisini anlatarak dolanma; konu belirgin sekilde farkli olsun.\n\n"
        "GECMIS KONULAR:\n" + history_text + "\n\n"
        "Cok onemli: Bilgi gercekten dogrulanabilir olmali; uydurma istatistik, sahte alinti veya kesin olmayan iddia kullanma.\n"
        "Tam olarak su JSON formatini dondur, baska aciklama ekleme:\n\n" + JSON_EXAMPLE + "\n\n"
        "Dort dilde ayni bilgiyi anlat. Arapca modern standart Arapca olsun.\n"
        "hashtags alaninda 5-8 adet, bu konuyla dogrudan ilgili, gercek ve kullanilan hashtag sec. Marka etiketi #FactBite ilk sirada olsun. Hashtagleri spam gibi doldurma."
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
    history_text = build_history_text(history)
    fact = request_fact(history_text)
    fact["_category"] = CATEGORY

    # Keep history compact and append the Turkish canonical topic.
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
    print(json.dumps(fact, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
