import json, os, time, urllib.parse, urllib.request
ACCESS_TOKEN=os.environ["IG_ACCESS_TOKEN"]; USER=os.environ["IG_USER_ID"]; REPO=os.environ["GITHUB_REPOSITORY"]; BRANCH=os.environ.get("GITHUB_REF_NAME","main"); BASE="https://graph.instagram.com/v21.0"
def post(path,p):
    req=urllib.request.Request(f"{BASE}/{path}",data=urllib.parse.urlencode(p).encode(),method="POST")
    with urllib.request.urlopen(req) as r:return json.loads(r.read())
def get(path,p):
    q=urllib.parse.urlencode(p); req=urllib.request.Request(f"{BASE}/{path}?{q}")
    with urllib.request.urlopen(req) as r:return json.loads(r.read())
def raw(path): return f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{path.replace(os.sep,'/')}"
def wait(cid,tries=30):
    for _ in range(tries):
        x=get(cid,{"fields":"status_code","access_token":ACCESS_TOKEN}); s=x.get("status_code")
        if s=="FINISHED": return
        if s in ("ERROR","EXPIRED"): raise RuntimeError(f"Instagram container failed: {x}")
        time.sleep(5)
    raise RuntimeError("Instagram container processing timeout")
def story(url):
    x=post(f"{USER}/media",{"image_url":url,"media_type":"STORIES","access_token":ACCESS_TOKEN}); wait(x["id"]); post(f"{USER}/media_publish",{"creation_id":x["id"],"access_token":ACCESS_TOKEN})
def reel(url,caption):
    x=post(f"{USER}/media",{"media_type":"REELS","video_url":url,"caption":caption,"access_token":ACCESS_TOKEN}); wait(x["id"]); y=post(f"{USER}/media_publish",{"creation_id":x["id"],"access_token":ACCESS_TOKEN}); return y.get("id")
def main():
    d=open("latest_post_dir.txt",encoding="utf-8").read().strip(); caption=open(os.path.join(d,"caption.txt"),encoding="utf-8").read(); files=sorted([x for x in os.listdir(d) if x.startswith("slide_") and x.endswith(".png")],key=lambda x:int(x.split("_")[1].split(".")[0]))
    ids=[]
    for f in files:
        x=post(f"{USER}/media",{"image_url":raw(os.path.join(d,f)),"is_carousel_item":"true","access_token":ACCESS_TOKEN}); ids.append(x["id"]); time.sleep(1)
    x=post(f"{USER}/media",{"media_type":"CAROUSEL","caption":caption,"children":",".join(ids),"access_token":ACCESS_TOKEN}); wait(x["id"]); feed=post(f"{USER}/media_publish",{"creation_id":x["id"],"access_token":ACCESS_TOKEN}); print("Carousel:",feed)
    try: story(raw(os.path.join(d,"slide_5.png"))); print("CTA Story published")
    except Exception as e: print("Story warning:",e)
    reel_path=os.path.join(d,"factbite_reel.mp4")
    if os.path.exists(reel_path):
        try: print("Reel:",reel(raw(reel_path),caption))
        except Exception as e: print("Reel warning:",e)
if __name__=="__main__": main()
