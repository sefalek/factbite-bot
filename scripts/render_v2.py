import datetime, math, os, random, json
import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont
HERE=os.path.dirname(os.path.abspath(__file__)); ASSETS=os.path.join(HERE,"..","assets")
W,H=1080,1350; NAVY=(18,42,72); ORANGE=(238,146,11); WHITE=(255,255,255); PAD=88
FB=os.path.join(ASSETS,"fonts","Poppins-Bold.ttf"); FS=os.path.join(ASSETS,"fonts","Poppins-SemiBold.ttf"); FM=os.path.join(ASSETS,"fonts","Poppins-Medium.ttf"); FA=os.path.join(ASSETS,"fonts","NotoSansArabic-Bold-static.ttf"); FAR=os.path.join(ASSETS,"fonts","NotoSansArabic-Regular-static.ttf"); LOGO=os.path.join(ASSETS,"logo.png")
LANGS=[("tr","TÜRKÇE","GÜNÜN BİLGİSİ",False),("en","ENGLISH","FACT OF THE DAY",False),("es","ESPAÑOL","DATO DEL DÍA",False),("ar","العربية","حقيقة اليوم",True)]
def ar(s): return get_display(arabic_reshaper.reshape(s))
def wrap(d,s,f,m):
    out=[]; cur=""
    for w in s.split():
        t=(cur+" "+w).strip()
        if d.textlength(t,font=f)<=m: cur=t
        else:
            if cur: out.append(cur)
            cur=w
    if cur: out.append(cur)
    return out
def gradient():
    base=Image.new("RGB",(W,H),NAVY); top=Image.new("RGB",(W,H),ORANGE); mask=Image.new("L",(W,H)); p=mask.load()
    for y in range(H):
        for x in range(0,W,4):
            v=int(255*(x+y)/(W+H))
            for xx in range(x,min(x+4,W)): p[xx,y]=v
    return Image.composite(top,base,mask).convert("RGBA")
def canvas(seed):
    random.seed(seed); bg=gradient(); d=ImageDraw.Draw(bg,"RGBA"); d._image=bg
    for _ in range(14):
        x=random.randint(60,W-60); y=random.randint(60,H-220); r=random.randint(6,22); pts=[]
        for i in range(8):
            a=math.pi*i/4; rr=r if i%2==0 else r*.35; pts.append((x+rr*math.cos(a),y+rr*math.sin(a)))
        d.polygon(pts,fill=WHITE+(random.randint(35,90),))
    logo=Image.open(LOGO).convert("RGBA").resize((108,108)); halo=Image.new("RGBA",(128,128),(0,0,0,0)); ImageDraw.Draw(halo).ellipse((0,0,128,128),fill=(255,255,255,235)); bg.alpha_composite(halo,(PAD-10,58)); bg.alpha_composite(logo,(PAD,68)); return bg
def fact_slide(path,label,ey,headline,body,page,rtl,seed):
    bg=canvas(seed); d=ImageDraw.Draw(bg,"RGBA"); d._image=bg; fp=ImageFont.truetype(FA if rtl else FS,28); tw=d.textlength(label,font=fp); box=(W-PAD-(int(tw)+60),82,W-PAD,138); d.rounded_rectangle(box,radius=28,fill=(255,255,255,235)); d.text((box[0]+30,box[1]+12),label,font=fp,fill=NAVY)
    fe=ImageFont.truetype(FA if rtl else FS,30); ey_y=300; ey=ar(ey) if rtl else ey
    ew=d.textlength(ey,font=fe); d.text(((W-PAD-ew) if rtl else PAD,ey_y),ey,font=fe,fill=WHITE); d.rounded_rectangle(((W-PAD-70 if rtl else PAD),ey_y+(58 if rtl else 46),(W-PAD if rtl else PAD+70),ey_y+(66 if rtl else 54)),radius=4,fill=WHITE)
    fh=ImageFont.truetype(FA if rtl else FB,84); y=400
    for line in wrap(d,headline,fh,W-2*PAD):
        lw=d.textlength(line,font=fh); d.text((W-PAD-lw if rtl else PAD,y),line,font=fh,fill=WHITE); y+=96
    y+=26; fbody=ImageFont.truetype(FAR if rtl else FM,38)
    for line in wrap(d,body,fbody,W-2*PAD-40):
        lw=d.textlength(line,font=fbody); d.text((W-PAD-lw if rtl else PAD,y),line,font=fbody,fill=(255,255,255,225)); y+=56
    bg.alpha_composite(Image.new("RGBA",(W,130),(0,0,0,60)),(0,H-130)); d=ImageDraw.Draw(bg,"RGBA"); ff=ImageFont.truetype(FM,30); d.text((PAD,H-90),"@factbitee",font=ff,fill=WHITE); pw=d.textlength(page,font=ff); d.text((W-PAD-pw,H-90),page,font=ff,fill=(255,255,255,210)); bg.convert("RGB").save(path,quality=95)
def cta_slide(path,cta):
    bg=canvas(5); d=ImageDraw.Draw(bg,"RGBA"); d._image=bg; d.text((PAD,300),"FACTBITE",font=ImageFont.truetype(FB,76),fill=WHITE); d.text((PAD,410),"✨ HER GÜN YENİ BİR ŞEY ÖĞREN",font=ImageFont.truetype(FS,38),fill=WHITE); y=540
    rows=[("🇹🇷",cta.get("tr","Her gün yeni bir şey öğren.")),("🇬🇧",cta.get("en","Learn something new every day.")),("🇪🇸",cta.get("es","Aprende algo nuevo cada día.")),("🇸🇦",cta.get("ar","تعلم شيئًا جديدًا كل يوم."))]
    for flag,text in rows:
        f=ImageFont.truetype(FAR if flag=="🇸🇦" else FM,34); text=ar(text) if flag=="🇸🇦" else text; d.text((PAD,y),f"{flag}  {text}",font=f,fill=WHITE); y+=76
    d.rounded_rectangle((PAD,y+20,W-PAD,y+105),radius=40,fill=(255,255,255,235)); f=ImageFont.truetype(FB,38); label="Daha fazlası için takip et  @factbitee"; lw=d.textlength(label,font=f); d.text(((W-lw)/2,y+42),label,font=f,fill=NAVY); bg.convert("RGB").save(path,quality=95)
def main():
    fact=json.load(open("fact.json",encoding="utf-8")); cat=fact.get("_category","general"); out=os.path.join("posts",f"{datetime.date.today().isoformat()}_{datetime.datetime.now().strftime('%H%M')}_{cat}"); os.makedirs(out,exist_ok=True)
    for i,(code,label,ey,rtl) in enumerate(LANGS,1):
        e=fact[code]; fact_slide(os.path.join(out,f"slide_{i}.png"),ar(label) if rtl else label,ey,e["headline"] if not rtl else ar(e["headline"]),e["body"] if not rtl else ar(e["body"]),f"{i} / 5",rtl,i)
    cta_slide(os.path.join(out,"slide_5.png"),fact.get("cta",{}))
    flags={"tr":"🇹🇷","en":"🇬🇧","es":"🇪🇸","ar":"🇸🇦"}; caption="\n\n".join(f"{flags[k]} {fact[k]['headline']}\n{fact[k]['body']}" for k in ["tr","en","es","ar"])+"\n\n"+" ".join(fact.get("hashtags",[])); open(os.path.join(out,"caption.txt"),"w",encoding="utf-8").write(caption)
    json.dump({"question":fact.get("story_question",{}),"options":fact.get("story_options",[])},open(os.path.join(out,"story_question.json"),"w",encoding="utf-8"),ensure_ascii=False)
    json.dump({"hook":fact.get("reel_hook",{}),"cta":fact.get("cta",{})},open(os.path.join(out,"reel_meta.json"),"w",encoding="utf-8"),ensure_ascii=False)
    open("latest_post_dir.txt","w").write(out)
if __name__=="__main__": main()
