import json, os, urllib.parse, urllib.request
BASE="https://graph.facebook.com/v23.0"
TOKEN=os.environ.get("FB_PAGE_ACCESS_TOKEN","")
def call(path,params):
    req=urllib.request.Request(f"{BASE}/{path}",data=urllib.parse.urlencode(params).encode(),method="POST")
    with urllib.request.urlopen(req) as r:return json.loads(r.read())
def main():
    if not TOKEN:
        print("FB_PAGE_ACCESS_TOKEN not configured; Facebook step skipped.")
        return
    d=open("latest_post_dir.txt",encoding="utf-8").read().strip(); caption=open(os.path.join(d,"caption.txt"),encoding="utf-8").read(); repo=os.environ["GITHUB_REPOSITORY"]; branch=os.environ.get("GITHUB_REF_NAME","main")
    req=urllib.request.Request(f"{BASE}/me?fields=id,name&access_token={urllib.parse.quote(TOKEN)}")
    with urllib.request.urlopen(req) as r: page=json.loads(r.read())
    page_id=page["id"]
    files=sorted([x for x in os.listdir(d) if x.startswith("slide_") and x.endswith(".png")],key=lambda x:int(x.split("_")[1].split(".")[0]))
    media=[]
    for f in files:
        url=f"https://raw.githubusercontent.com/{repo}/{branch}/{d.replace(os.sep,'/')}/{f}"
        x=call(f"{page_id}/photos",{"url":url,"published":"false","access_token":TOKEN}); media.append(x["id"])
    params={"message":caption,"access_token":TOKEN}
    for i,mid in enumerate(media): params[f"attached_media[{i}]"]=json.dumps({"media_fbid":mid})
    print("Facebook published:",call(f"{page_id}/feed",params),"page:",page.get("name"))
if __name__=="__main__": main()
