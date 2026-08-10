import json, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H=1080,1920; PAD=78; NAVY=(10,25,45); BLUE=(28,76,120); ORANGE=(238,146,11); WHITE=(255,255,255); MUTED=(220,230,240)
HERE=os.path.dirname(os.path.abspath(__file__)); ASSETS=os.path.join(HERE,"..","assets"); B=os.path.join(ASSETS,"fonts","Poppins-Bold.ttf"); M=os.path.join(ASSETS,"fonts","Poppins-Medium.ttf"); LOGO=os.path.join(ASSETS,"logo.png")
def f(p,s): return ImageFont.truetype(p,s)
def wrap(d,t,ft,w):
 out=[]; c=""
 for x in str(t).split():
  n=(c+" "+x).strip()
  if d.textlength(n,font=ft)<=w:c=n
  else:
   if c:out.append(c)
   c=x
 if c:out.append(c)
 return out
def make(seed):
 im=Image.new("RGB",(W,H)); p=im.load()
 for y in range(H):
  for x in range(W):
   t=.65*x/W+.35*y/H; p[x,y]=(int(NAVY[0]*(1-t)+BLUE[0]*t),int(NAVY[1]*(1-t)+BLUE[1]*t),int(NAVY[2]*(1-t)+BLUE[2]*t))
 ov=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(ov)
 for i in range(12):
  x=(i*137+seed*91)%W; y=(i*211+seed*53)%H; r=70+(i%3)*45; d.ellipse((x-r,y-r,x+r,y+r),fill=ORANGE+(16,))
 return Image.alpha_composite(im.convert("RGBA"),ov.filter(ImageFilter.GaussianBlur(38)))
def card(path,title,body,label,seed):
 im=make(seed); d=ImageDraw.Draw(im,"RGBA")
 if os.path.exists(LOGO): im.alpha_composite(Image.open(LOGO).convert("RGBA").resize((84,84)),(PAD,62))
 d.text((PAD+105,88),"FACTBITE",font=f(B,30),fill=WHITE); d.text((W-PAD,90),"@factbitee",font=f(M,27),fill=MUTED,anchor="ra")
 d.rounded_rectangle((PAD,430,W-PAD,555),35,fill=(255,255,255,25),outline=(255,255,255,70),width=2); d.text((PAD+32,466),label,font=f(B,28),fill=ORANGE)
 y=690
 for line in wrap(d,title,f(B,76),W-2*PAD): d.text((PAD,y),line,font=f(B,76),fill=WHITE); y+=92
 y+=38
 for line in wrap(d,body,f(M,43),W-2*PAD): d.text((PAD,y),line,font=f(M,43),fill=MUTED); y+=63
 d.rounded_rectangle((PAD,H-245,W-PAD,H-120),30,fill=(0,0,0,55),outline=(255,255,255,55),width=2); d.text((PAD+30,H-205),"@FACTBITEE  •  BİLMEK GÜZELDİR",font=f(B,24),fill=WHITE)
 im.convert("RGB").save(path,quality=95)
def main():
 d=open("latest_post_dir.txt",encoding="utf-8").read().strip(); fact=json.load(open("fact.json",encoding="utf-8")); tr=fact["tr"]; hook=fact.get("story_question",{}).get("tr") or fact.get("reel_hook",{}).get("tr") or tr["headline"]
 card(os.path.join(d,"story_v2.png"),hook,"Cevabı biliyor musun?\nYorumlara tahminini yaz 👇","GÜNÜN TAHMİNİ",1)
 card(os.path.join(d,"story_v2_answer.png"),tr["headline"],tr["body"],"CEVAP",2)
 card(os.path.join(d,"story_v2_cta.png"),"Böyle kısa bilgiler hoşuna gidiyorsa...","FactBite'ı takip et.\nYeni Reel ve carousel her gün.","TAKİP ET",3)
if __name__=="__main__": main()
