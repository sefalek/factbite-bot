import json, math, os, subprocess, wave
from array import array
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W,H=1080,1920; PAD=82
NAVY=(10,25,45); BLUE=(27,74,116); ORANGE=(238,146,11); WHITE=(255,255,255); MUTED=(220,230,240)
HERE=os.path.dirname(os.path.abspath(__file__)); ASSETS=os.path.join(HERE,"..","assets")
FONT_B=os.path.join(ASSETS,"fonts","Poppins-Bold.ttf"); FONT_M=os.path.join(ASSETS,"fonts","Poppins-Medium.ttf"); LOGO=os.path.join(ASSETS,"logo.png")

def font(path,size): return ImageFont.truetype(path,size)
def wrap(d,text,f,maxw):
    out=[]; cur=""
    for w in str(text).split():
        n=(cur+" "+w).strip()
        if d.textlength(n,font=f)<=maxw: cur=n
        else:
            if cur: out.append(cur)
            cur=w
    if cur: out.append(cur)
    return out

def bg(seed):
    im=Image.new("RGB",(W,H)); p=im.load(); a=(seed*37)%255
    for y in range(H):
        for x in range(W):
            t=(x/W)*.72+(y/H)*.28
            r=int(NAVY[0]*(1-t)+BLUE[0]*t); g=int(NAVY[1]*(1-t)+BLUE[1]*t); b=int(NAVY[2]*(1-t)+BLUE[2]*t)
            p[x,y]=(r,g,b)
    ov=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(ov)
    for i in range(9):
        x=(i*173+a)%W; y=150+(i*257+a*2)%(H-250); r=80+(i%4)*55
        d.ellipse((x-r,y-r,x+r,y+r),fill=ORANGE+(18,))
    ov=ov.filter(ImageFilter.GaussianBlur(35)); im=Image.alpha_composite(im.convert("RGBA"),ov)
    return im

def icon(d,category):
    c=ORANGE; cx,cy=W-PAD-115,250
    d.ellipse((cx-78,cy-78,cx+78,cy+78),fill=(255,255,255,28),outline=(255,255,255,90),width=2)
    symbols={"science":"✦","space":"◉","animals":"🐾","history":"⌛","tech":"⌘","sports":"★","health":"+","culture":"◆","language":"A","news":"!","general":"?"}
    s=symbols.get(category,"✦")
    try: d.text((cx,cy),s,font=font(FONT_B,58),anchor="mm",fill=c)
    except Exception: d.text((cx-20,cy-35),s,font=font(FONT_B,58),fill=c)

def frame(title,body,badge,seed,category):
    im=bg(seed); d=ImageDraw.Draw(im,"RGBA")
    if os.path.exists(LOGO): im.alpha_composite(Image.open(LOGO).convert("RGBA").resize((82,82)),(PAD,62))
    d.text((PAD+102,88),"FACTBITE",font=font(FONT_B,30),fill=WHITE)
    d.text((W-PAD,90),"@factbitee",font=font(FONT_M,27),fill=MUTED,anchor="ra")
    icon(d,category)
    d.rounded_rectangle((PAD,390,W-PAD,510),35,fill=(255,255,255,24),outline=(255,255,255,70),width=2)
    d.text((PAD+30,425),badge.upper(),font=font(FONT_B,27),fill=ORANGE)
    y=610; hf=font(FONT_B,82); bf=font(FONT_M,43)
    for line in wrap(d,title,hf,W-2*PAD): d.text((PAD,y),line,font=hf,fill=WHITE); y+=98
    y+=35
    for line in wrap(d,body,bf,W-2*PAD): d.text((PAD,y),line,font=bf,fill=MUTED); y+=64
    d.rounded_rectangle((PAD,H-250,W-PAD,H-130),30,fill=(0,0,0,45),outline=(255,255,255,55),width=2)
    d.text((PAD+30,H-215),"BİL • MERAK ET • PAYLAŞ",font=font(FONT_B,25),fill=WHITE)
    return im.convert("RGB")

def make_audio(path,category,duration=20.0):
    sr=44100; total=int(sr*duration); data=array("h")
    patterns={"history":[60,64,67,72],"tech":[60,65,69,72],"science":[62,65,69,74],"animals":[64,67,71,74],"sports":[55,59,62,67],"space":[57,60,64,69],"culture":[60,64,67,71],"general":[60,64,67,72]}
    notes=patterns.get(category,patterns["general"])
    for i in range(total):
        t=i/sr; step=int(t*2.0)%len(notes); f=440*2**((notes[step]-69)/12)
        val=.035*math.sin(2*math.pi*f*t)+.022*math.sin(2*math.pi*f*.5*t)+.012*math.sin(2*math.pi*f*2*t)
        val+=.045*math.exp(-((t*2.0-int(t*2.0))/.035)**2)
        env=min(1,t/.6,min(1,(duration-t)/.8)); data.append(int(max(-1,min(1,val*env))*32767))
    with wave.open(path,"wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(data.tobytes())

def make_voice(path,fact):
    tr=fact["tr"]; hook=fact.get("reel_hook",{}).get("tr") or tr["headline"]
    script=f"{hook}. {tr['body']} {tr['headline']}. Böyle kısa bilgiler için FactBite'ı takip et."
    voice="tr-TR-EmelNeural"
    try:
        subprocess.run(["edge-tts","--voice",voice,"--text",script,"--write-media",path],check=True,timeout=45)
        return True
    except Exception as e:
        print("TTS unavailable, using music only:",e); return False

def main():
    d=open("latest_post_dir.txt",encoding="utf-8").read().strip(); fact=json.load(open("fact.json",encoding="utf-8")); tr=fact["tr"]; category=fact.get("_category","general")
    hook=fact.get("reel_hook",{}).get("tr") or "Bunu biliyor muydun?"; q=fact.get("story_question",{}).get("tr") or hook
    specs=[("BUNU BİLİYOR MUYDUN?",hook,"HOOK"),("TAHMİN ET",q,"MERAK"),(tr["headline"],tr["body"],"GERÇEK"),("ASLINDA DAHA İLGİNÇ...",f"Bu bilgi neden önemli? {tr['body']}","TWIST"),("BÖYLE BİLGİLER İÇİN", "Takip et • Kaydet • Paylaş\n@factbitee","CTA")]
    for i,(t,b,badge) in enumerate(specs,1): frame(t,b,badge,i,category).save(os.path.join(d,f"reel_{i}.png"),quality=95)
    voice=os.path.join(d,"reel_voice.mp3"); music=os.path.join(d,"reel_music.wav"); make_voice(voice,fact); make_audio(music,category)
    out=os.path.join(d,"factbite_reel.mp4"); inputs=os.path.join(d,"reel_inputs.txt")
    with open(inputs,"w",encoding="utf-8") as f:
        for i in range(1,6): f.write(f"file '{os.path.abspath(os.path.join(d,f'reel_{i}.png'))}'\n")
    # 5 x 4 seconds; gentle Ken Burns-like motion via zoompan.
    vf="zoompan=z='min(zoom+0.0008,1.06)':d=120:s=1080x1920:fps=30,format=yuv420p"
    audio_inputs=["-i",music]
    if os.path.exists(voice): audio_inputs += ["-i",voice]
    cmd=["ffmpeg","-y","-f","concat","-safe","0","-i",inputs]+audio_inputs+[
        "-vf",vf,"-t","20","-c:v","libx264","-preset","veryfast","-crf","22","-pix_fmt","yuv420p"]
    if os.path.exists(voice): cmd += ["-filter_complex","[1:a]volume=0.16[m];[2:a]volume=1.0[v];[v][m]amix=inputs=2:duration=longest:dropout_transition=2[a]","-map","0:v","-map","[a]"]
    else: cmd += ["-c:a","aac","-b:a","128k","-shortest"]
    cmd += ["-c:a","aac","-b:a","128k",out]
    subprocess.run(cmd,check=True); os.remove(inputs); os.remove(music)
    if os.path.exists(voice): os.remove(voice)

if __name__=="__main__": main()
