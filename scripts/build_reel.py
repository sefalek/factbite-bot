import json, math, os, subprocess, wave
from array import array
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H=1080,1920; PAD=82; NAVY=(10,25,45); BLUE=(27,74,116); ORANGE=(238,146,11); WHITE=(255,255,255); MUTED=(220,230,240)
HERE=os.path.dirname(os.path.abspath(__file__)); ASSETS=os.path.join(HERE,"..","assets"); FB=os.path.join(ASSETS,"fonts","Poppins-Bold.ttf"); FM=os.path.join(ASSETS,"fonts","Poppins-Medium.ttf"); FA=os.path.join(ASSETS,"fonts","NotoSansArabic-Bold-static.ttf"); LOGO=os.path.join(ASSETS,"logo.png")
VOICES={"tr":"tr-TR-EmelNeural","en":"en-US-AriaNeural","es":"es-ES-ElviraNeural","ar":"ar-SA-ZariyahNeural"}
LABELS={"tr":"TÜRKÇE","en":"ENGLISH","es":"ESPAÑOL","ar":"العربية"}

def font(path,size): return ImageFont.truetype(path,size)
def wrap(d,text,f,maxw):
 out=[]; cur=""
 for word in str(text).split():
  c=(cur+" "+word).strip()
  if d.textlength(c,font=f)<=maxw: cur=c
  else:
   if cur: out.append(cur)
   cur=word
 if cur: out.append(cur)
 return out

def bg(seed):
 im=Image.new("RGB",(W,H)); p=im.load(); a=(seed*37)%255
 for y in range(H):
  for x in range(W):
   t=(x/W)*.72+(y/H)*.28; p[x,y]=(int(NAVY[0]*(1-t)+BLUE[0]*t),int(NAVY[1]*(1-t)+BLUE[1]*t),int(NAVY[2]*(1-t)+BLUE[2]*t))
 ov=Image.new("RGBA",(W,H)); d=ImageDraw.Draw(ov)
 for i in range(9):
  x=(i*173+a)%W; y=150+(i*257+a*2)%(H-250); r=80+(i%4)*55; d.ellipse((x-r,y-r,x+r,y+r),fill=ORANGE+(18,))
 return Image.alpha_composite(im.convert("RGBA"),ov.filter(ImageFilter.GaussianBlur(35)))

def frame(title,body,badge,seed,category,lang):
 im=bg(seed); d=ImageDraw.Draw(im,"RGBA")
 if os.path.exists(LOGO): im.alpha_composite(Image.open(LOGO).convert("RGBA").resize((82,82)),(PAD,62))
 d.text((PAD+102,88),"FACTBITE",font=font(FB,30),fill=WHITE); d.text((W-PAD,90),"@factbitee",font=font(FM,27),fill=MUTED,anchor="ra")
 d.rounded_rectangle((PAD-10,370,W-PAD+10,1585),46,fill=(4,15,30,62),outline=(255,255,255,55),width=2)
 d.rounded_rectangle((PAD,390,W-PAD,510),35,fill=(255,255,255,24),outline=(255,255,255,70),width=2)
 d.rounded_rectangle((PAD+24,414,PAD+43,486),9,fill=ORANGE+(255,))
 d.text((PAD+65,425),f"{LABELS.get(lang,lang)}  •  {badge}",font=font(FB,27),fill=ORANGE)
 y=610; hf=font(FB,82); bf=font(FM,43)
 for line in wrap(d,title,hf,W-2*PAD-20): d.text((PAD,y),line,font=hf,fill=WHITE); y+=98
 y+=35
 for line in wrap(d,body,bf,W-2*PAD-20): d.text((PAD,y),line,font=bf,fill=MUTED); y+=64
 d.rounded_rectangle((PAD,H-250,W-PAD,H-130),30,fill=(0,0,0,45),outline=(255,255,255,55),width=2)
 d.text((PAD+30,H-215),"BİL • MERAK ET • PAYLAŞ",font=font(FB,25),fill=WHITE)
 return im.convert("RGB")

def make_audio(path,duration=23.0):
 sr=44100; data=array("h"); total=int(sr*duration); chords=[(48,52,55),(50,55,60),(45,50,54),(48,53,57)]
 for i in range(total):
  t=i/sr; chord=chords[int(t/5.75)%4]; val=sum(.018*math.sin(2*math.pi*(440*2**((m-69)/12))*t)+.008*math.sin(2*math.pi*(440*2**((m-69)/12)/2)*t) for m in chord); val*=.75+.25*math.sin(2*math.pi*t/7.5)**2; val*=min(1,t/1.2)*min(1,max(0,(duration-t)/1.2)); data.append(int(max(-1,min(1,val))*32767))
 with wave.open(path,"wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(data.tobytes())

def make_voice(path,fact,lang):
 x=fact[lang]; hook=fact.get("reel_hook",{}).get(lang) or x["headline"]; cta={"tr":"Böyle bilgiler için FactBite'ı takip et.","en":"Follow FactBite for more facts like this.","es":"Sigue a FactBite para descubrir más datos.","ar":"تابع FactBite لمزيد من المعلومات."}[lang]
 script=f"{hook}. {x['body']} {cta}"; subprocess.run(["edge-tts","--voice",VOICES[lang],"--text",script,"--write-media",path],check=True,timeout=45)

def main():
 d=open("latest_post_dir.txt",encoding="utf-8").read().strip(); fact=json.load(open("fact.json",encoding="utf-8")); lang=fact.get("_language","tr"); x=fact[lang]; cat=fact.get("_category","general"); hook=fact.get("reel_hook",{}).get(lang) or x["headline"]
 q=fact.get("story_question",{}).get(lang) or hook
 specs=[("DUR",hook,"HOOK"),("TAHMİN ET",q,"MERAK"),(x["headline"],x["body"],"GERÇEK"),("ASLINDA DAHA İLGİLİ...",x["body"],"TWIST"),("BÖYLE BİLGİLER İÇİN","Takip et • Kaydet • Paylaş\n@factbitee","CTA")]
 for i,(title,body,badge) in enumerate(specs,1): frame(title,body,badge,i,cat,lang).save(os.path.join(d,f"reel_{i}.png"),quality=95)
 voice=os.path.join(d,"reel_voice.mp3"); music=os.path.join(d,"reel_music.wav"); make_voice(voice,fact,lang); make_audio(music)
 out=os.path.join(d,"factbite_reel.mp4"); cmd=["ffmpeg","-y"]
 for i in range(1,6): cmd += ["-loop","1","-t","4.6","-i",os.path.join(d,f"reel_{i}.png")]
 cmd += ["-i",music,"-i",voice]
 f=[]
 for i in range(5): f.append(f"[{i}:v]zoompan=z='min(zoom+0.00055,1.045)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=138:s=1080x1920:fps=30,format=yuv420p,setpts=PTS-STARTPTS[v{i}]")
 f += ["[v0][v1]xfade=transition=slideleft:duration=0.30:offset=4.30[x1]","[x1][v2]xfade=transition=fade:duration=0.30:offset=8.60[x2]","[x2][v3]xfade=transition=slideright:duration=0.30:offset=12.90[x3]","[x3][v4]xfade=transition=fade:duration=0.30:offset=17.20[x4]","[x4]drawbox=x='-320+(iw+320)*mod(t,4.3)/4.3':y=570:w=320:h=6:color=0xEE920B@0.88:t=fill,drawbox=x=82:y=1680:w='(iw-164)*mod(t,4.3)/4.3':h=5:color=0xEE920B@0.95:t=fill,fade=t=in:st=0:d=0.25,format=yuv420p[vout]","[5:a]volume=0.075[music]","[6:a]volume=1.0[voice]","[voice][music]amix=inputs=2:duration=first:dropout_transition=2,aresample=44100[aout]"]
 cmd += ["-filter_complex",";".join(f),"-map","[vout]","-map","[aout]","-t","23","-c:v","libx264","-preset","veryfast","-crf","21","-pix_fmt","yuv420p","-c:a","aac","-b:a","160k","-movflags","+faststart",out]
 subprocess.run(cmd,check=True); os.remove(music); os.path.exists(voice) and os.remove(voice)
if __name__=="__main__": main()
