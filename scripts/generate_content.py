"""
generate_content.py
Calls the Google Gemini API (free tier, no credit card required) to produce
one "fact of the day" in Turkish, English, Spanish and Arabic, and writes
it to fact.json for the render step to use.

Requires env var: GEMINI_API_KEY
Get a free key at: https://aistudio.google.com/apikey
"""
import json
import os
import urllib.request

API_KEY = os.environ["GEMINI_API_KEY"]
MODEL = "gemini-2.5-flash-lite"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

PROMPT = """Bugün için ilginç, doğrulanabilir, şaşırtıcı bir "genel kültür bilgisi" üret.
Bilim, tarih, doğa, uzay, insan vücudu, dil, hayvanlar gibi konulardan olabilir.
Daha önce çok bilinen klişe bilgilerden kaçın (örn. "bal bozulmaz" gibi çok tekrarlanmış olanlar).

Bunu tam olarak şu JSON formatında, başka hiçbir açıklama eklemeden döndür:

{
  "tr": {"headline": "kısa çarpıcı başlık (max 8 kelime)", "body": "1-2 cümlelik açıklama"},
  "en": {"headline": "...", "body": "..."},
  "es": {"headline": "...", "body": "..."},
  "ar": {"headline": "...", "body": "..."}
}

Dört dildeki metin aynı bilgiyi anlatmalı (birebir çeviri olmasa da anlamca eşdeğer olmalı).
Arapça metin doğru ve akıcı olmalı, modern standart Arapça kullan.
"""


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

    with open("fact.json", "w", encoding="utf-8") as f:
        json.dump(fact, f, ensure_ascii=False, indent=2)

    print("Wrote fact.json:")
    print(json.dumps(fact, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
