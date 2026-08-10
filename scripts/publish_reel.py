import json, os, time, urllib.parse, urllib.request

ACCESS_TOKEN = os.environ["IG_ACCESS_TOKEN"]
USER = os.environ["IG_USER_ID"]
REPO = os.environ["GITHUB_REPOSITORY"]
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
REEL_FILENAME = os.environ.get("REEL_FILENAME", "factbite_reel.mp4")
BASE = "https://graph.instagram.com/v21.0"


def post(path, params):
    req = urllib.request.Request(f"{BASE}/{path}", data=urllib.parse.urlencode(params).encode(), method="POST")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def get(path, params):
    req = urllib.request.Request(f"{BASE}/{path}?{urllib.parse.urlencode(params)}")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def wait(cid, tries=48):
    for _ in range(tries):
        x = get(cid, {"fields": "status_code", "access_token": ACCESS_TOKEN})
        status = x.get("status_code")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram Reel container failed: {x}")
        time.sleep(5)
    raise RuntimeError("Instagram Reel processing timeout")


def raw(path):
    return f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{path.replace(os.sep, '/')}"


def main():
    d = open("latest_post_dir.txt", encoding="utf-8").read().strip()
    fact = json.load(open("fact.json", encoding="utf-8"))
    category = fact.get("_category", "general")
    print(f"Publishing Reel for actual post category: {category}")

    video = os.path.join(d, REEL_FILENAME)
    if not os.path.exists(video):
        raise RuntimeError(f"Reel file not found: {video}")

    video_url = raw(video)
    print(f"Publishing Reel asset: {video_url}")
    hashtags = " ".join(fact.get("hashtags", [])[:6])
    hook = fact.get("reel_hook", {}).get("tr", "Bunu biliyor muydun?")
    caption = f"{hook}\n\nHer gün kısa, şaşırtıcı ve doğrulanabilir bilgiler. 🧠\n\n{hashtags}"
    x = post(f"{USER}/media", {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "share_to_feed": "true",
        "access_token": ACCESS_TOKEN,
    })
    wait(x["id"])
    published = post(f"{USER}/media_publish", {"creation_id": x["id"], "access_token": ACCESS_TOKEN})
    print("Reel published:", published)


if __name__ == "__main__":
    main()
