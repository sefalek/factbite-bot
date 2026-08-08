"""
generate_content.py
Calls the Google Gemini API (free tier, no credit card required) to produce
one "fact of the day" in Turkish, English, Spanish and Arabic, and writes
it to fact.json for the render step to use.

Requires env vars:
  GEMINI_API_KEY - get a free key at https://aistudio.google.com/apikey
  CATEGORY       - one of: history, language, health, animals, tech, science, general
"""
import json
import os
import urllib.request

API_KEY = os.environ["GEMINI_API_KEY"]
MODEL = "gemini-flash-latest"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

CATEGORY = os.environ.get("CATEGORY", "general")

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
  "ar": {"headline": "...", "body": "..."}
}"""

PROMPT = (
    "Bugun icin ilginc, dogrulanabilir, sasirtici bir \"genel kultur bilgisi\" uret.\n"
    + CATEGORY_INSTRUCTIONS.get(CATEGORY, CATEGORY_INSTRUCTIONS["general"]) + "\n"
    "Daha once cok bilinen klise bilgilerden kacin.\n\n"
    "Bunu tam olarak su JSON formatinda, baska hicbir aciklama eklemeden dondur:\n\n"
    + JSON_EXAMPLE + "\n\n"
    "Dort dildeki metin ayni bilgiyi anlatmali (birebir ceviri olmasa da anlamca esdeger olmali).\n"
    "Arapca metin dogru ve akici olmali, modern standart Arapca kullan.\n"
)


def main():
    body = json.dumps({
        "contents": [{"parts": [{"text": PROMPT}]}],
        "generationConfig": {
            "response_mime_type": "application/json",
        },
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())

    text = data["candidates"][0]["content"]["parts"][0]["text"]
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    fact = json.loads(text.strip())
    fact["_category"] = CATEGORY

    with open("fact.json", "w", encoding="utf-8") as f:
        json.dump(fact, f, ensure_ascii=False, indent=2)

    print("Wrote fact.json (category:", CATEGORY, ")")
    print(json.dumps(fact, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
