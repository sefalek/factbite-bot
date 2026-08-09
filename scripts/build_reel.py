import json, math, os, subprocess, wave
from array import array
from PIL import Image, ImageDraw, ImageFont

W,H=1080,1920; NAVY=(18,42,72); ORANGE=(238,146,11); WHITE=(255,255,255); PAD=88
HERE=os.path.dirname(os.path.abspath(__file__)); ASSETS=os.path.join(HERE,"..","assets")
FB=os.path.join(ASSETS,"fonts","Poppins-Bold.ttf"); FS=os.path.join(ASSETS,"fonts","Poppins-SemiBold.ttf"); FM=os.path.join(ASSETS,"fonts","Poppins-Medium.ttf"); LOGO=os.path.join(ASSETS,"logo.png")

def gradient(seed=1):
    img=Image.new("RGBA",(W,H)); px=img.load(); shift=(seed*83)%255
    for y in range(H):
        for x in range(W):
            t=max(0,min(1,(x+y*.35)/(W+H*.35))); px[x,y]=(int(NAVY[0]*(1-t)+ORANGE[0]*t),int(NAVY[1]*(1-t)+ORANGE[1]*t),int(NAVY[2]*(1-t)+ORANGE[2]*t),255)
    d=ImageDraw.Draw(img,"RGBA")
    for i in range(20):
        x=40+((i*173+shift)%(W-80)); y=100+((i*251+shift*2)%(H-300)); r=5+(i%4)*3; d.ellipse((x-r,y-r,x+r,y+r),fill=WHITE+(35,))
    return img

def wrap(d,text,font,max_width):
    lines=[]; cur=""
    for word in text.split():
        cand=(cur+" "+word).strip()
        if d.textlength(cand,font=font)<=max_width: cur=cand
        else:
            if cur: lines.append(cur)
            cur=word
    if cur: lines.append(cur)
    return lines

def frame(seed,title,body,badge):
    bg=gradient(seed); d=ImageDraw.Draw(bg,"RGBA"); logo=Image.open(LOGO).convert("RGBA").resize((96,96)); bg.alpha_composite(logo,(PAD,64)); d.text((W-PAD-250,86),"@factbitee",font=ImageFont.truetype(FM,30),fill=WHITE)
    d.rounded_rectangle((PAD,390,W-PAD,505),radius=32,fill=(255,255,255,30),outline=(255,255,255,90),width=2); d.text((PAD+34,425),badge,font=ImageFont.truetype(FS,30),fill=WHITE)
    y=600; hf=ImageFont.truetype(FB,88); bf=ImageFont.truetype(FM,42)
    for line in wrap(d,title,hf,W-2*PAD): d.text((PAD,y),line,font=hf,fill=WHITE); y+=104
    if body:
        y+=38
        for line in wrap(d,body,bf,W-2*PAD): d.text((PAD,y),line,font=bf,fill=(255,255,255,225)); y+=62
    return bg.convert("RGB")

def make_frames(fact,out_dir):
    tr=fact["tr"]; hook=fact.get("reel_hook",{}).get("tr") or "Bunu biliyor muydun?"; fmt=fact.get("format","classic")
    if fmt=="mystery":
        title1="BU NE OLABİLİR?"; body1=hook; title2="3 İPUCU"; body2=fact.get("story_question",{}).get("tr",tr["body"]); title3=tr["headline"]; body3=tr["body"]
    elif fmt=="myth_vs_fact":
        title1="YANLIŞ MI, GERÇEK Mİ?"; body1=hook; title2="CEVAP: GERÇEK"; body2=tr["body"]; title3="NEDEN İLGİNÇ?"; body3=tr["headline"]
    elif fmt=="question_first":
        title1="TAHMİN ET!"; body1=fact.get("story_question",{}).get("tr",hook); title2="CEVAP"; body2=tr["headline"]; title3="KISA CEVAP"; body3=tr["body"]
    else:
        title1="BUNU BİLİYOR MUYDUN?"; body1=hook; title2=tr["headline"]; body2=tr["body"]; title3="DEVAMI CAROUSEL'DE"; body3="Aynı fact, 4 dilde. @factbitee"
    specs=[(title1,body1,"HOOK",1),(title2,body2,"FACT",2),(title3,body3,"FACTBITE",3),("HER GÜN YENİ BİR FACT","Takip et • Kaydet • Paylaş\n@factbitee","CTA",4)]
    for i,(t,b,badge,s) in enumerate(specs,1): frame(s,t,b,badge).save(os.path.join(out_dir,f"reel_{i}.png"),quality=95)

def note_hz(note): return 440.0*(2.0**((note-69)/12.0))

def make_audio(path,category):
    sr,duration=44100,16.0; total=int(sr*duration); data=array("h")
    patterns={"history":[60,64,67,72,67,64],"tech":[60,65,69,72,69,65],"science":[62,65,69,74,69,65],"animals":[64,67,71,74,71,67],"language":[60,63,67,70,67,63],"health":[62,66,69,73,69,66]}
    notes=patterns.get(category,patterns["science"])
    for i in range(total):
        t=i/sr; beat=t*2.4; step=int(beat)%len(notes); phase=beat-int(beat); freq=note_hz(notes[step]);
        chord=sum(math.sin(2*math.pi*note_hz(notes[step]+o)*t)*.035 for o in (0,4,7)); bass=math.sin(2*math.pi*note_hz(notes[step]-24)*t)*.045; pulse=math.exp(-((phase-.02)/.04)**2)*.09; shimmer=math.sin(2*math.pi*freq*2*t)*.012; env=min(1,t/.8)*min(1,(duration-t)/1.0); sample=(chord+bass+pulse+shimmer)*env; data.append(max(-32767,min(32767,int(sample*32767))))
    with wave.open(path,"wb") as wav: wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(sr); wav.writeframes(data.tobytes())

def main():
    d=open("latest_post_dir.txt",encoding="utf-8").read().strip(); fact=json.load(open("fact.json",encoding="utf-8")); make_frames(fact,d); audio=os.path.join(d,"reel_audio.wav"); make_audio(audio,fact.get("_category","science")); out=os.path.join(d,"factbite_reel.mp4"); inp=os.path.join(d,"reel_slides.txt")
    with open(inp,"w",encoding="utf-8") as f:
        for i in range(1,5): f.write(f"file '{os.path.abspath(os.path.join(d,f'reel_{i}.png'))}'\n"); f.write("duration 4\n")
        f.write(f"file '{os.path.abspath(os.path.join(d,'reel_4.png'))}'\n")
    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",inp,"-i",audio,"-vf","format=yuv420p","-r","30","-t","16","-c:v","libx264","-preset","veryfast","-crf","23","-c:a","aac","-b:a","128k","-shortest",out],check=True)
    os.remove(inp); os.remove(audio); print("V3 Reel created:",out)
if __name__=="__main__": main()
