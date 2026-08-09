import json
import math
import os
import subprocess
import wave
from array import array

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
NAVY = (18, 42, 72)
ORANGE = (238, 146, 11)
WHITE = (255, 255, 255)
PAD = 88
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")
FB = os.path.join(ASSETS, "fonts", "Poppins-Bold.ttf")
FS = os.path.join(ASSETS, "fonts", "Poppins-SemiBold.ttf")
FM = os.path.join(ASSETS, "fonts", "Poppins-Medium.ttf")
FA = os.path.join(ASSETS, "fonts", "NotoSansArabic-Bold-static.ttf")
LOGO = os.path.join(ASSETS, "logo.png")


def gradient(seed=1):
    img = Image.new("RGBA", (W, H))
    px = img.load()
    shift = (seed * 83) % 255
    for y in range(H):
        for x in range(W):
            t = (x + y * 0.35) / (W + H * 0.35)
            t = max(0.0, min(1.0, t))
            r = int(NAVY[0] * (1 - t) + ORANGE[0] * t)
            g = int(NAVY[1] * (1 - t) + ORANGE[1] * t)
            b = int(NAVY[2] * (1 - t) + ORANGE[2] * t)
            px[x, y] = (r, g, b, 255)
    d = ImageDraw.Draw(img, "RGBA")
    for i in range(18):
        x = 40 + ((i * 173 + shift) % (W - 80))
        y = 100 + ((i * 251 + shift * 2) % (H - 300))
        r = 5 + (i % 4) * 3
        d.ellipse((x-r, y-r, x+r, y+r), fill=WHITE + (35,))
    return img


def wrap(draw, text, font, max_width):
    lines, current = [], ""
    for word in text.split():
        candidate = (current + " " + word).strip()
        if draw.textlength(candidate, font=font) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def frame_base(seed):
    bg = gradient(seed)
    logo = Image.open(LOGO).convert("RGBA").resize((110, 110))
    bg.alpha_composite(logo, (PAD, 70))
    d = ImageDraw.Draw(bg, "RGBA")
    d.text((W-PAD-260, 92), "@factbitee", font=ImageFont.truetype(FM, 32), fill=WHITE)
    return bg, d


def make_frames(fact, out_dir):
    tr = fact["tr"]
    hook = fact.get("reel_hook", {}).get("tr") or "Bunu biliyor muydun?"
    hashtags = " ".join(fact.get("hashtags", [])[:6])
    cta = "Devamı 4 dilde carousel'de → @factbitee"

    specs = [
        (hook, "", 1),
        (tr["headline"], tr["body"], 2),
        ("Aynı fact, 4 dilde.", cta, 3),
        ("Her gün yeni bir fact.", "Takip et  •  Kaydet  •  Paylaş\n@factbitee", 4),
    ]
    for idx, (title, body, seed) in enumerate(specs, 1):
        bg, d = frame_base(seed)
        title_font = ImageFont.truetype(FB, 82 if idx != 3 else 74)
        body_font = ImageFont.truetype(FM, 42)
        y = 560 if idx == 1 else 500
        d.rounded_rectangle((PAD, y-38, W-PAD, y+110), radius=36, fill=(255,255,255,30), outline=(255,255,255,90), width=2)
        d.text((PAD+38, y), "FACTBITE", font=ImageFont.truetype(FS, 30), fill=WHITE)
        y += 170
        for line in wrap(d, title, title_font, W-2*PAD-20):
            d.text((PAD, y), line, font=title_font, fill=WHITE)
            y += 100
        if body:
            y += 38
            for line in wrap(d, body, body_font, W-2*PAD-20):
                d.text((PAD, y), line, font=body_font, fill=(255,255,255,225))
                y += 62
        if idx == 2:
            d.text((PAD, 1630), "🇹🇷 Türkçe teaser", font=ImageFont.truetype(FS, 32), fill=WHITE)
        elif idx == 3:
            d.text((PAD, 1640), "🇹🇷 🇬🇧 🇪🇸 🇸🇦", font=ImageFont.truetype(FS, 48), fill=WHITE)
        elif idx == 4:
            d.text((PAD, 1640), hashtags, font=ImageFont.truetype(FM, 28), fill=WHITE)
        bg.convert("RGB").save(os.path.join(out_dir, f"reel_{idx}.png"), quality=95)


def note_hz(note):
    return 440.0 * (2.0 ** ((note - 69) / 12.0))


def make_audio(path, category):
    sr, duration = 44100, 15.0
    total = int(sr * duration)
    data = array("h")
    patterns = {
        "history": [60, 64, 67, 72, 67, 64],
        "tech": [60, 65, 69, 72, 69, 65],
        "science": [62, 65, 69, 74, 69, 65],
        "animals": [64, 67, 71, 74, 71, 67],
        "language": [60, 63, 67, 70, 67, 63],
        "health": [62, 66, 69, 73, 69, 66],
    }
    notes = patterns.get(category, patterns["science"])
    for i in range(total):
        t = i / sr
        beat = t * 2.0
        step = int(beat) % len(notes)
        phase = (beat - int(beat))
        freq = note_hz(notes[step])
        chord = 0.0
        for offset in (0, 4, 7):
            chord += math.sin(2 * math.pi * note_hz(notes[step] + offset) * t) * 0.045
        bass = math.sin(2 * math.pi * note_hz(notes[step] - 24) * t) * 0.06
        pulse = math.exp(-((phase - 0.02) / 0.045) ** 2) * 0.12
        shimmer = math.sin(2 * math.pi * freq * 2 * t) * 0.018
        env = min(1.0, t / 0.6) * min(1.0, (duration - t) / 0.8)
        sample = (chord + bass + pulse + shimmer) * env
        data.append(max(-32767, min(32767, int(sample * 32767))))
    with wave.open(path, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sr)
        wav.writeframes(data.tobytes())


def main():
    post_dir = open("latest_post_dir.txt", encoding="utf-8").read().strip()
    fact = json.load(open("fact.json", encoding="utf-8"))
    make_frames(fact, post_dir)
    audio = os.path.join(post_dir, "reel_audio.wav")
    make_audio(audio, fact.get("_category", "science"))
    out = os.path.join(post_dir, "factbite_reel.mp4")
    inp = os.path.join(post_dir, "reel_slides.txt")
    with open(inp, "w", encoding="utf-8") as f:
        for i in range(1, 5):
            f.write(f"file '{os.path.abspath(os.path.join(post_dir, f'reel_{i}.png'))}'\n")
            f.write("duration 3.75\n")
        f.write(f"file '{os.path.abspath(os.path.join(post_dir, 'reel_4.png'))}'\n")
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", inp,
        "-i", audio,
        "-vf", "format=yuv420p",
        "-r", "30", "-t", "15",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
        "-c:a", "aac", "-b:a", "128k", "-shortest", out,
    ]
    subprocess.run(cmd, check=True)
    os.remove(inp)
    os.remove(audio)
    print("Reel created:", out)


if __name__ == "__main__":
    main()
