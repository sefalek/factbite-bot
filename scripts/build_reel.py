import json, math, os, subprocess, wave
from array import array
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
PAD = 82
NAVY = (10, 25, 45)
BLUE = (27, 74, 116)
ORANGE = (238, 146, 11)
WHITE = (255, 255, 255)
MUTED = (220, 230, 240)
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")
FONT_B = os.path.join(ASSETS, "fonts", "Poppins-Bold.ttf")
FONT_M = os.path.join(ASSETS, "fonts", "Poppins-Medium.ttf")
LOGO = os.path.join(ASSETS, "logo.png")


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(d, text, f, maxw):
    out, cur = [], ""
    for word in str(text).split():
        candidate = (cur + " " + word).strip()
        if d.textlength(candidate, font=f) <= maxw:
            cur = candidate
        else:
            if cur:
                out.append(cur)
            cur = word
    if cur:
        out.append(cur)
    return out


def bg(seed):
    im = Image.new("RGB", (W, H))
    p = im.load()
    a = (seed * 37) % 255
    for y in range(H):
        for x in range(W):
            t = (x / W) * 0.72 + (y / H) * 0.28
            r = int(NAVY[0] * (1 - t) + BLUE[0] * t)
            g = int(NAVY[1] * (1 - t) + BLUE[1] * t)
            b = int(NAVY[2] * (1 - t) + BLUE[2] * t)
            p[x, y] = (r, g, b)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for i in range(9):
        x = (i * 173 + a) % W
        y = 150 + (i * 257 + a * 2) % (H - 250)
        r = 80 + (i % 4) * 55
        d.ellipse((x - r, y - r, x + r, y + r), fill=ORANGE + (18,))
    ov = ov.filter(ImageFilter.GaussianBlur(35))
    return Image.alpha_composite(im.convert("RGBA"), ov)


def icon(d, category):
    cx, cy = W - PAD - 115, 250
    d.ellipse((cx - 78, cy - 78, cx + 78, cy + 78), fill=(255, 255, 255, 28), outline=(255, 255, 255, 90), width=2)
    symbols = {
        "science": "✦", "space": "◉", "animals": "🐾", "history": "⌛",
        "tech": "⌘", "sports": "★", "health": "+", "culture": "◆",
        "language": "A", "news": "!", "general": "?"
    }
    s = symbols.get(category, "✦")
    try:
        d.text((cx, cy), s, font=font(FONT_B, 58), anchor="mm", fill=ORANGE)
    except Exception:
        d.text((cx - 20, cy - 35), s, font=font(FONT_B, 58), fill=ORANGE)


def frame(title, body, badge, seed, category):
    im = bg(seed)
    d = ImageDraw.Draw(im, "RGBA")
    if os.path.exists(LOGO):
        im.alpha_composite(Image.open(LOGO).convert("RGBA").resize((82, 82)), (PAD, 62))
    d.text((PAD + 102, 88), "FACTBITE", font=font(FONT_B, 30), fill=WHITE)
    d.text((W - PAD, 90), "@factbitee", font=font(FONT_M, 27), fill=MUTED, anchor="ra")
    icon(d, category)

    d.rounded_rectangle((PAD - 10, 370, W - PAD + 10, 1585), 46, fill=(4, 15, 30, 62), outline=(255, 255, 255, 55), width=2)
    d.rounded_rectangle((PAD, 390, W - PAD, 510), 35, fill=(255, 255, 255, 24), outline=(255, 255, 255, 70), width=2)
    d.rounded_rectangle((PAD + 24, 414, PAD + 43, 486), 9, fill=ORANGE + (255,))
    d.text((PAD + 65, 425), badge.upper(), font=font(FONT_B, 27), fill=ORANGE)

    y = 610
    hf = font(FONT_B, 82)
    bf = font(FONT_M, 43)
    for line in wrap(d, title, hf, W - 2 * PAD - 20):
        d.text((PAD, y), line, font=hf, fill=WHITE)
        y += 98
    y += 35
    for line in wrap(d, body, bf, W - 2 * PAD - 20):
        d.text((PAD, y), line, font=bf, fill=MUTED)
        y += 64

    d.rounded_rectangle((PAD, H - 250, W - PAD, H - 130), 30, fill=(0, 0, 0, 45), outline=(255, 255, 255, 55), width=2)
    d.text((PAD + 30, H - 215), "BİL • MERAK ET • PAYLAŞ", font=font(FONT_B, 25), fill=WHITE)
    return im.convert("RGB")


def make_audio(path, category, duration=23.0):
    """Soft ambient bed. No sharp beeps/tones; speech remains the focus."""
    sr = 44100
    total = int(sr * duration)
    data = array("h")
    progressions = {
        "history": [(48, 52, 55), (50, 53, 57), (45, 50, 54), (48, 52, 57)],
        "tech": [(48, 55, 60), (50, 57, 62), (45, 52, 57), (48, 55, 60)],
        "science": [(50, 53, 57), (52, 55, 60), (48, 52, 55), (50, 53, 59)],
        "animals": [(52, 55, 59), (50, 54, 57), (48, 52, 55), (52, 55, 60)],
        "sports": [(43, 50, 55), (45, 52, 57), (41, 48, 53), (43, 50, 55)],
        "space": [(45, 52, 57), (48, 53, 60), (43, 50, 55), (45, 52, 59)],
        "culture": [(48, 52, 55), (50, 53, 57), (46, 50, 53), (48, 52, 57)],
        "general": [(48, 52, 55), (50, 53, 57), (46, 50, 53), (48, 52, 57)],
    }
    chords = progressions.get(category, progressions["general"])
    for i in range(total):
        t = i / sr
        chord = chords[int(t / 5.75) % len(chords)]
        val = 0.0
        for midi in chord:
            f = 440 * 2 ** ((midi - 69) / 12)
            val += 0.018 * math.sin(2 * math.pi * f * t)
            val += 0.008 * math.sin(2 * math.pi * (f / 2) * t)
        val *= 0.78 + 0.22 * math.sin(2 * math.pi * t / 7.5) ** 2
        fade_in = min(1.0, t / 1.2)
        fade_out = min(1.0, max(0.0, (duration - t) / 1.2))
        val *= fade_in * fade_out
        data.append(int(max(-1.0, min(1.0, val)) * 32767))
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(data.tobytes())


def make_voice(path, fact):
    tr = fact["tr"]
    hook = fact.get("reel_hook", {}).get("tr") or tr["headline"]
    body = tr["body"]
    script = (
        f"{hook}. {body} "
        f"Kısacası, sandığından daha ilginç. "
        f"Böyle kısa ve şaşırtıcı bilgiler için FactBite'ı takip et."
    )
    voice = "tr-TR-EmelNeural"
    try:
        subprocess.run(
            ["edge-tts", "--voice", voice, "--text", script, "--write-media", path],
            check=True,
            timeout=45,
        )
        return True
    except Exception as e:
        raise RuntimeError(f"Turkish TTS generation failed: {e}") from e


def main():
    d = open("latest_post_dir.txt", encoding="utf-8").read().strip()
    fact = json.load(open("fact.json", encoding="utf-8"))
    tr = fact["tr"]
    category = fact.get("_category", "general")
    hook = fact.get("reel_hook", {}).get("tr") or "Bunu biliyor muydun?"
    q = fact.get("story_question", {}).get("tr") or hook

    specs = [
        ("BUNU BİLİYOR MUYDUN?", hook, "HOOK"),
        ("TAHMİN ET", q, "MERAK"),
        (tr["headline"], tr["body"], "GERÇEK"),
        ("ASLINDA DAHA İLGİNÇ...", f"Bu bilgi neden önemli? {tr['body']}", "TWIST"),
        ("BÖYLE BİLGİLER İÇİN", "Takip et • Kaydet • Paylaş\n@factbitee", "CTA"),
    ]
    for i, (title, body, badge) in enumerate(specs, 1):
        frame(title, body, badge, i, category).save(os.path.join(d, f"reel_{i}.png"), quality=95)

    voice = os.path.join(d, "reel_voice.mp3")
    music = os.path.join(d, "reel_music.wav")
    make_voice(voice, fact)
    make_audio(music, category, 23.0)

    out = os.path.join(d, "factbite_reel.mp4")
    inputs = [os.path.join(d, f"reel_{i}.png") for i in range(1, 6)]

    cmd = ["ffmpeg", "-y"]
    for image in inputs:
        cmd += ["-loop", "1", "-t", "4.6", "-i", image]
    cmd += ["-i", music, "-i", voice]

    filters = []
    for i in range(5):
        filters.append(
            f"[{i}:v]zoompan=z='min(zoom+0.00055,1.045)':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=138:s=1080x1920:fps=30,"
            f"format=yuv420p,setpts=PTS-STARTPTS[v{i}]"
        )

    filters += [
        "[v0][v1]xfade=transition=slideleft:duration=0.30:offset=4.30[x1]",
        "[x1][v2]xfade=transition=fade:duration=0.30:offset=8.60[x2]",
        "[x2][v3]xfade=transition=slideright:duration=0.30:offset=12.90[x3]",
        "[x3][v4]xfade=transition=fade:duration=0.30:offset=17.20[x4]",
        # Use ffmpeg's portable iw variable (not W) for animated overlay positioning.
        "[x4]drawbox=x='-320+(iw+320)*mod(t,4.3)/4.3':y=570:w=320:h=6:color=0xEE920B@0.88:t=fill,"
        "drawbox=x=82:y=1680:w='(iw-164)*mod(t,4.3)/4.3':h=5:color=0xEE920B@0.95:t=fill,"
        "fade=t=in:st=0:d=0.25,format=yuv420p[vout]",
        "[5:a]volume=0.075[music]",
        "[6:a]volume=1.0[voice]",
        "[voice][music]amix=inputs=2:duration=first:dropout_transition=2,aresample=44100[aout]",
    ]

    cmd += [
        "-filter_complex", ";".join(filters),
        "-map", "[vout]",
        "-map", "[aout]",
        "-t", "23",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "21",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "160k",
        "-movflags", "+faststart",
        out,
    ]
    subprocess.run(cmd, check=True)

    os.remove(music)
    if os.path.exists(voice):
        os.remove(voice)


if __name__ == "__main__":
    main()
