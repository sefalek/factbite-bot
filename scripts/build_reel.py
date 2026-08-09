import json, math, os, subprocess, wave
from array import array
from PIL import Image, ImageDraw, ImageFont
W,H=1080,1920; NAVY=(18,42,72); ORANGE=(238,146,11); WHITE=(255,255,255); PAD=88
HERE=os.path.dirname(os.path.abspath(__file__)); ASSETS=os.path.join(HERE,"..","assets"); FB=os.path.join(ASSETS,"fonts","Poppins-Bold.ttf"); FS=os.path.join(ASSETS,"fonts","Poppins-SemiBold.ttf"); FM=os.path.join(ASSETS,"fonts","Poppins-Medium.ttf"); LOGO=os.path.join(ASSETS,"logo.png")
def gradient(seed=1):
 img=Image.new("RGBA",(W,H)); px=img.load(); shift=(seed*83)%255
 for y in range(H):
  for x in range(W):
   t=max(0,min(1,(x+y*.35)/(W+H*.35))); px[x,y]=(int(NAVY[0]*(1-t)+ORANGE[0]*t),int(NAVY[1]*(1-t)+ORANGE[1]*t),int(NAVY[2]*(1-t)+ORANGE[2]*t),255)
 d=ImageDraw.Draw(img,"RGBA")
 for i in range(18):
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
def make_frames(fact,out_dir):
 tr=fact["tr"]; hook=fact.get("reel_hook",{}).get("tr") or "Bunu biliyor muydun?"; hashtags=" ".join(fact.get("hashtags",[])[:6]); specs=[(hook,"",1),(tr["headline"],tr["body"],2),("Aynı fact, 4 dilde.","Devamı carousel'de → @factbitee",3),("Her gün yeni bir fact.","Takip et • Kaydet • Paylaş\n@factbitee",4)]
 for idx,(title,body,seed) in enumerate(specs,1):
  bg=gradient(seed); logo=Image.open(LOGO).convert("RGBA").resize((110,110)); bg.alpha_composite(logo,(PAD,70)); d=ImageDraw.Draw(bg,"RGBA"); d.text((W-PAD-260,92),"@factbitee",font=ImageFont.truetype(FM,32),fill=WHITE); y=500; tf=ImageFont.truetype(FB,82); bf=ImageFont.truetype(FM,42); d.rounded_rectangle((PAD,y-38,W-PAD,y+110),radius=36,fill=(255,255,255,30),outline=(255,255,255,90),width=2); d.text((PAD+38,y),"FACTBITE",font=ImageFont.truetype(FS,30),fill=WHITE); y+=170
  for line in wrap(d,title,tf,W-2*PAD-20): d.text((PAD,y),line,font=tf,fill=WHITE); y+=100
  if body:
   y+=38
   for line in wrap(d,body,bf,W-2*PAD-20): d.text((PAD,y),line,font=bf,fill=(255,255,255,225)); y+=62
  if idx==4: d.text((PAD,1640),hashtags,font=ImageFont.truetype(FM,28),fill=WHITE)
  bg.convert("RGB").save(os.path.join(out_dir,f"reel_{idx}.png"),quality=95)
def note_hz(n): return 440.0*(2.0**((n-69)/12.0))
def make_audio(path,category):
 sr,duration=44100,15.0; data=array("h"); patterns={"history":[60,64,67,72,67,64],"tech":[60,65,69,72,69,65],"science":[62,65,69,74,69,65],"animals":[64,67,71,74,71,67],"language":[60,63,67,70,67,63],"health":[62,66,69,73,69,66]}; notes=patterns.get(category,patterns["science"])
 for i in range(int(sr*duration)):
  t=i/sr; beat=t*2.0; step=int(beat)%len(notes); phase=beat-int(beat); freq=note_hz(notes[step]); chord=sum(math.sin(2*math.pi*note_hz(notes[step]+o)*t)*.045 for o in (0,4,7)); bass=math.sin(2*math.pi*note_hz(notes[step]-24)*t)*.06; pulse=math.exp(-((phase-.02)/.045)**2)*.12; shimmer=math.sin(2*math.pi*freq*2*t)*.018; env=min(1,t/.6)*min(1,(duration-t)/.8); data.append(max(-32767,min(32767,int((chord+bass+pulse+shimmer)*env*32767))))
 with wave.open(path,"wb") as wav: wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(sr); wav.writeframes(data.tobytes())
def main():
 d=open("latest_post_dir.txt",encoding="utf-8").read().strip(); fact=json.load(open("fact.json",encoding="utf-8")); make_frames(fact,d); audio=os.path.join(d,"reel_audio.wav"); make_audio(audio,fact.get("_category","science")); out=os.path.join(d,"factbite_reel.mp4"); inp=os.path.join(d,"reel_slides.txt")
 with open(inp,"w",encoding="utf-8") as f:
  for i in range(1,5): f.write(f"file '{os.path.abspath(os.path.join(d,f'reel_{i}.png'))}'\n"); f.write("duration 3.75\n")
  f.write(f"file '{os.path.abspath(os.path.join(d,'reel_4.png'))}'\n")
 subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",inp,"-i",audio,"-vf","format=yuv420p","-r","30","-t","15","-c:v","libx264","-preset","veryfast","-crf","24","-c:a","aac","-b:a","128k","-shortest",out],check=True); os.remove(inp); os.remove(audio)
if __name__=="__main__": main()
