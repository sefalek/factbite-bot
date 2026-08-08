"""
render_slides.py
Reads fact.json (produced by generate_content.py) and renders the 4
carousel slide images (TR, EN, ES, AR) using the FactBite brand template.
Outputs to posts/<date>/slide_1.png .. slide_4.png
"""
import datetime
import math
import os
import random

import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont
import json

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")

W, H = 1080, 1350
NAVY = (18, 42, 72)
ORANGE = (238, 146, 11)
WHITE = (255, 255, 255)
PAD = 88

F_BOLD = os.path.join(ASSETS, "fonts", "Poppins-Bold.ttf")
F_SEMI = os.path.join(ASSETS, "fonts", "Poppins-SemiBold.ttf")
F_MED = os.path.join(ASSETS, "fonts", "Poppins-Medium.ttf")
F_AR = os.path.join(ASSETS, "fonts", "NotoSansArabic-Bold-static.ttf")
F_AR_REG = os.path.join(ASSETS, "fonts", "NotoSansArabic-Regular-static.ttf")
LOGO_PATH = os.path.join(ASSETS, "logo.png")

LANGS = [
    {"code": "tr", "label": "TÜRKÇE", "eyebrow": "GÜNÜN BİLGİSİ", "rtl": False},
    {"code": "en", "label": "ENGLISH", "eyebrow": "FACT OF THE DAY", "rtl": False},
    {"code": "es", "label": "ESPAÑOL", "eyebrow": "DATO DEL DÍA", "rtl": False},
    {"code": "ar", "label": "العربية", "eyebrow": "حقيقة اليوم", "rtl": True},
]


def shape_ar(text):
    return get_display(arabic_reshaper.reshape(text))


def wrap_text(draw, text, font, max_width):
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def diagonal_gradient(w, h, c1, c2):
    base = Image.new("RGB", (w, h), c1)
    top = Image.new("RGB", (w, h), c2)
    mask = Image.new("L", (w, h))
    mpx = mask.load()
    diag = w + h
    for y in range(h):
        for x in range(0, w, 4):
            t = (x + y) / diag
            v = int(255 * min(max(t, 0), 1))
            for xx in range(x, min(x + 4, w)):
                mpx[xx, y] = v
    return Image.composite(top, base, mask)


def draw_spark(draw, cx, cy, size, color, opacity=255):
    pts = []
    for i in range(8):
        ang = math.pi / 4 * i
        r = size if i % 2 == 0 else size * 0.35
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    overlay = Image.new("RGBA", draw._image.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    odraw.polygon(pts, fill=color + (opacity,))
    draw._image.alpha_composite(overlay)


def make_slide(out_path, lang_label, eyebrow, headline, body, page_label, rtl, seed):
    random.seed(seed)
    bg = diagonal_gradient(W, H, NAVY, ORANGE).convert("RGBA")
    draw = ImageDraw.Draw(bg, "RGBA")
    draw._image = bg

    for _ in range(14):
        x = random.randint(60, W - 60)
        y = random.randint(60, H - 220)
        s = random.randint(6, 22)
        op = random.randint(35, 90)
        draw_spark(draw, x, y, s, WHITE, opacity=op)

    big_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    big_draw = ImageDraw.Draw(big_overlay)
    big_draw._image = big_overlay
    draw_spark(big_draw, W - 180, H - 480, 260, WHITE, opacity=18)
    bg.alpha_composite(big_overlay)
    draw = ImageDraw.Draw(bg, "RGBA")
    draw._image = bg

    logo = Image.open(LOGO_PATH).convert("RGBA").resize((108, 108))
    halo = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo)
    hd.ellipse((0, 0, 128, 128), fill=(255, 255, 255, 235))
    bg.alpha_composite(halo, (PAD - 10, 58))
    bg.alpha_composite(logo, (PAD, 68))

    f_pill = ImageFont.truetype(F_AR if rtl else F_SEMI, 28)
    tw = draw.textlength(lang_label, font=f_pill)
    pill_w = int(tw) + 60
    pill_box = (W - PAD - pill_w, 82, W - PAD, 82 + 56)
    draw.rounded_rectangle(pill_box, radius=28, fill=(255, 255, 255, 235))
    draw.text((pill_box[0] + 30, pill_box[1] + 12), lang_label, font=f_pill, fill=NAVY)

    f_eyebrow = ImageFont.truetype(F_AR if rtl else F_SEMI, 30)
    ey_y = 300
    if rtl:
        ew = draw.textlength(eyebrow, font=f_eyebrow)
        draw.text((W - PAD - ew, ey_y), eyebrow, font=f_eyebrow, fill=(255, 255, 255, 255))
    else:
        draw.text((PAD, ey_y), eyebrow, font=f_eyebrow, fill=(255, 255, 255, 255))
    uy = ey_y + (58 if rtl else 46)
    if rtl:
        draw.rounded_rectangle((W - PAD - 70, uy, W - PAD, uy + 8), radius=4, fill=WHITE)
    else:
        draw.rounded_rectangle((PAD, uy, PAD + 70, uy + 8), radius=4, fill=WHITE)

    f_head = ImageFont.truetype(F_AR if rtl else F_BOLD, 84)
    max_w = W - 2 * PAD
    lines = wrap_text(draw, headline, f_head, max_w)
    y = uy + 50
    line_h = 96
    for ln in lines:
        lw = draw.textlength(ln, font=f_head)
        x = (W - PAD - lw) if rtl else PAD
        draw.text((x, y), ln, font=f_head, fill=WHITE)
        y += line_h

    y += 26
    f_body = ImageFont.truetype(F_AR_REG if rtl else F_MED, 38)
    body_lines = wrap_text(draw, body, f_body, max_w - 40)
    line_h2 = 56
    for ln in body_lines:
        lw = draw.textlength(ln, font=f_body)
        x = (W - PAD - lw) if rtl else PAD
        draw.text((x, y), ln, font=f_body, fill=(255, 255, 255, 225))
        y += line_h2

    strip = Image.new("RGBA", (W, 130), (0, 0, 0, 60))
    bg.alpha_composite(strip, (0, H - 130))
    f_foot = ImageFont.truetype(F_MED, 30)
    draw.text((PAD, H - 90), "@factbitee", font=f_foot, fill=WHITE)
    pw = draw.textlength(page_label, font=f_foot)
    draw.text((W - PAD - pw, H - 90), page_label, font=f_foot, fill=(255, 255, 255, 210))

    bg.convert("RGB").save(out_path)


def main():
    with open("fact.json", encoding="utf-8") as f:
        fact = json.load(f)

    category = fact.get("_category", "general")
    today = datetime.date.today().isoformat()
    now = datetime.datetime.now().strftime("%H%M")
    out_dir = os.path.join("posts", f"{today}_{now}_{category}")
    os.makedirs(out_dir, exist_ok=True)

    total = len(LANGS)
    paths = []
    for i, lang in enumerate(LANGS, start=1):
        entry = fact[lang["code"]]
        out_path = os.path.join(out_dir, f"slide_{i}.png")
        make_slide(
            out_path,
            lang_label=shape_ar(lang["label"]) if lang["rtl"] else lang["label"],
            eyebrow=shape_ar(lang["eyebrow"]) if lang["rtl"] else lang["eyebrow"],
            headline=shape_ar(entry["headline"]) if lang["rtl"] else entry["headline"],
            body=shape_ar(entry["body"]) if lang["rtl"] else entry["body"],
            page_label=f"{i} / {total}",
            rtl=lang["rtl"],
            seed=i,
        )
        paths.append(out_path)
        print("wrote", out_path)

    # also write the caption (all 4 languages stacked) for the publish step
    caption_parts = []
    flags = {"tr": "🇹🇷", "en": "🇬🇧", "es": "🇪🇸", "ar": "🇸🇦"}
    for lang in LANGS:
        entry = fact[lang["code"]]
        caption_parts.append(f"{flags[lang['code']]} {entry['headline']}\n{entry['body']}")
    caption = "\n\n".join(caption_parts)
    caption += "\n\n#FactBite #GünününBilgisi #FactOfTheDay #DatoDelDia"
    with open(os.path.join(out_dir, "caption.txt"), "w", encoding="utf-8") as f:
        f.write(caption)

    with open("latest_post_dir.txt", "w") as f:
        f.write(out_dir)


if __name__ == "__main__":
    main()
