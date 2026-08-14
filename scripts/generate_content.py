"""FactBite content generator with a 180-day topic reuse guard."""
import json, os, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher

API_KEY = os.environ["GEMINI_API_KEY"]
MODEL = os.environ.get("GEMINI_CONTENT_MODEL", "gemini-3.5-flash-lite")
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"
CATEGORY = os.environ.get("CATEGORY", "general")
FORMAT = os.environ.get("CONTENT_FORMAT", "reel")
LANGUAGE = os.environ.get("LANGUAGE", "tr")
TOPIC = os.environ.get("TOPIC", "")
SPECIAL_NAME = os.environ.get("SPECIAL_DAY", "")
HISTORY_PATH = "data/topic_history.json"
REUSE_DAYS = 180

CATEGORY_INSTRUCTIONS = {
    "history": "Tarih ve kültür: az bilinen ama doğrulanabilir olay, gelenek, kişi veya nesne.",
    "language": "Dil ve kelime kökenleri: şaşırtıcı ve doğrulanabilir etimoloji.",
    "health": "İnsan vücudu ve sağlık: bilimsel, güvenli, abartısız; teşhis/tedavi yok.",
    "animals": "Hayvanlar ve doğa: sıra dışı doğrulanabilir davranış veya olgu.",
    "tech": "Teknoloji ve icatlar: ilginç icat veya beklenmedik teknoloji gerçeği.",
    "science": "Bilim ve uzay: fizik, astronomi, biyoloji veya uzaydan şaşırtıcı gerçek.",
    "sports": "Spor: sporun tarihi, kuralları, teknoloji veya şaşırtıcı doğrulanabilir bağlam; maç sonucu haberi değil.",
    "news": "Gündem: güncel olayın arkasındaki doğrulanabilir bağlam/fact; sansasyonel haber dili değil.",
    "culture": "Popüler kültür, sanat, coğrafya ve toplumdan doğrulanabilir şaşırtıcı bilgi.",
    "space": "Uzay ve astronomiden doğrulanabilir, görselleştirilebilir bilgi.",
    "general": "Bilim, tarih, doğa, uzay, insan, dil, hayvanlar veya teknoloji."
}
LANG_NAMES = {"tr": "Turkish", "en": "English", "es": "Spanish", "ar": "Arabic"}


def load_history():
    try:
        with open(HISTORY_PATH, encoding="utf-8") as f:
            value = json.load(f)
            return value if isinstance(value, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def parse_timestamp(item):
    value = item.get("published_at") or item.get("generated_at") or item.get("date")
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def active_history(history):
    """Keep all legacy records without dates protected, plus dated records from 180 days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=REUSE_DAYS)
    active = []
    for item in history:
        ts = parse_timestamp(item)
        if ts is None or ts >= cutoff:
            active.append(item)
    return active


def normalize(text):
    return " ".join(str(text or "").lower().split())


def similarity(a, b):
    a = normalize(a)
    b = normalize(b)
    if not a or not b:
        return 0.0
    seq = SequenceMatcher(None, a, b).ratio()
    aw = set(a.split())
    bw = set(b.split())
    jaccard = len(aw & bw) / max(1, len(aw | bw))
    return max(seq, jaccard)


def is_reused(fact, history):
    candidates = []
    for lang in (LANGUAGE, "tr", "en", "es", "ar"):
        block = fact.get(lang) or {}
        candidates.extend([block.get("headline", ""), block.get("body", "")])
    candidates.append(fact.get("_topic", ""))

    for old in active_history(history):
        old_candidates = [
            old.get("topic", ""),
            old.get("headline", ""),
            old.get("body", ""),
        ]
        for new_text in candidates:
            for old_text in old_candidates:
                score = similarity(new_text, old_text)
                if score >= 0.82:
                    return True, score, old.get("headline") or old.get("topic") or old_text
    return False, 0.0, ""


def ask(prompt):
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"response_mime_type": "application/json"}
    }).encode()
    req = urllib.request.Request(API_URL, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code in (429, 403):
            out = os.environ.get("GITHUB_OUTPUT")
            if out:
                with open(out, "a", encoding="utf-8") as f:
                    f.write("quota_exhausted=true\n")
        raise
    text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    if text.startswith("```"):
        text = text.split("```")[1].removeprefix("json")
    return json.loads(text.strip())


def main():
    history = load_history()
    recent = active_history(history)
    history_text = "\n".join(
        f"- {x.get('language','')}: {x.get('headline','') or x.get('topic','')}"
        for x in recent
    ) or "YOK"
    special = f"Özel gün: {SPECIAL_NAME}. Uygunsa bu Reel'e doğal biçimde bağla." if SPECIAL_NAME else ""
    language = LANG_NAMES.get(LANGUAGE, LANGUAGE)

    rejected = []
    fact = None
    quality = {}

    for attempt in range(1, 7):
        rejection_text = "\n".join(f"- {x}" for x in rejected) or "YOK"
        prompt = f'''FactBite için tek bir Reel üret.
HEDEF DİL: {language} ({LANGUAGE})
KATEGORİ: {CATEGORY_INSTRUCTIONS.get(CATEGORY, CATEGORY_INSTRUCTIONS["general"])}
AI EDİTÖRÜNÜN SEÇTİĞİ KONU: {TOPIC or "KONU YOK — KONUYU SEN SEÇ"}
{special}
Amaç: kaydırmayı durduracak, görsel olarak güçlü, gerçek ve doğrulanabilir 20-25 saniyelik Reel. Konuyu başka dillere göre değiştirme; bu slotun konusu yalnızca bu hedef dil/kitle içindir. Doğal, yerel ve konuşma diline yakın yaz. Clickbait, uydurma istatistik ve aşırı iddialardan kaçın. Hook ilk 1-2 saniyede merak yaratmalı ama cevabı hemen vermemeli. 5-8 hashtag üret; #FactBite ilk olsun. Quality 1-10 puanla; overall 8 altındaysa daha güçlü bir açı seç.

ÇOK ÖNEMLİ TEKRAR KURALI: Aşağıdaki konular son 180 gün içinde yayınlandı veya eski sistemden geldiği için güvenlik amacıyla korunuyor. Bunları veya çok benzerlerini kesinlikle seçme. Aynı gerçeği farklı başlıkla anlatmak da tekrardır. Her çalıştırmada yeni ve bağımsız bir konu seç.
GEÇMİŞ:
{history_text}

BU DENEMEDE REDDEDİLEN KONULAR:
{rejection_text}

JSON ONLY. Reel hedef dil içeriğini {LANGUAGE} alanına koy. Diğer dört dil alanlarını mevcut carousel uyumluluğu için aynı gerçeğin doğal çevirileri olarak doldur; ancak bu slotun yayın dili SADECE {LANGUAGE} olacaktır.
Schema: {{"format":"reel","tr":{{"headline":"...","body":"..."}},"en":{{"headline":"...","body":"..."}},"es":{{"headline":"...","body":"..."}},"ar":{{"headline":"...","body":"..."}},"reel_hook":{{"tr":"...","en":"...","es":"...","ar":"..."}},"story_question":{{"tr":"...","en":"...","es":"...","ar":"..."}},"story_options":["A","B","C"],"hashtags":["#FactBite"],"cta":{{"tr":"...","en":"...","es":"...","ar":"..."}},"quality":{{"curiosity":1,"surprise":1,"shareability":1,"clarity":1,"overall":1}},"source":{{"name":"","url":""}}}}'''
        fact = ask(prompt)
        quality = fact.get("quality", {})
        if int(quality.get("overall", 0)) < 8:
            rejected.append(fact.get(LANGUAGE, {}).get("headline", "quality < 8"))
            continue

        reused, score, old_text = is_reused(fact, recent)
        if reused:
            rejected.append(f"{fact.get(LANGUAGE, {}).get('headline','')} (similarity={score:.2f}, old={old_text})")
            continue
        break
    else:
        raise RuntimeError("TOPIC_REUSE_GUARD: 6 AI attempts produced only duplicate/low-quality topics")

    now = datetime.now(timezone.utc).isoformat()
    fact.update({
        "_category": CATEGORY,
        "_language": LANGUAGE,
        "_topic": TOPIC or fact.get(LANGUAGE, {}).get("headline", ""),
        "_v4": True,
        "_special_day": SPECIAL_NAME,
        "generated_at": now,
        "topic_guard_days": REUSE_DAYS,
    })

    history.append({
        "language": LANGUAGE,
        "category": CATEGORY,
        "topic": fact.get("_topic", ""),
        "headline": fact.get(LANGUAGE, {}).get("headline", ""),
        "body": fact.get(LANGUAGE, {}).get("body", ""),
        "format": "reel",
        "quality": quality,
        "generated_at": now,
    })

    os.makedirs("data", exist_ok=True)
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    with open("fact.json", "w", encoding="utf-8") as f:
        json.dump(fact, f, ensure_ascii=False, indent=2)
    print("V4 fact generated", LANGUAGE, CATEGORY, fact.get("_topic"), quality, "history=", len(history))


if __name__ == "__main__":
    main()
