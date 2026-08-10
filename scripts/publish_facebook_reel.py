import json
import os
import sys
import time
import urllib.parse
import urllib.request

PAGE_ID = os.environ.get("FB_PAGE_ID", "").strip()
PAGE_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN", "").strip()
API_VERSION = os.environ.get("FB_GRAPH_VERSION", "v21.0")
BASE = f"https://graph.facebook.com/{API_VERSION}"


def request_json(url, params=None, method="POST", headers=None, data=None):
    body = data
    if params is not None:
        body = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        raise RuntimeError(f"Facebook API HTTP {e.code}: {detail}") from e


def main():
    # Facebook publishing is optional until the Page credentials are added to GitHub Secrets.
    if not PAGE_ID or not PAGE_TOKEN:
        print("Facebook Reel publishing skipped: FB_PAGE_ID / FB_PAGE_ACCESS_TOKEN not configured.")
        return

    post_dir = open("latest_post_dir.txt", encoding="utf-8").read().strip()
    fact = json.load(open("fact.json", encoding="utf-8"))
    filename = os.environ.get("REEL_FILENAME", "factbite_reel.mp4")
    video = os.path.join(post_dir, filename)

    if not os.path.exists(video):
        raise RuntimeError(f"Facebook Reel file not found: {video}")

    hook = fact.get("reel_hook", {}).get("tr", "Bunu biliyor muydun?")
    hashtags = " ".join(fact.get("hashtags", [])[:6])
    description = f"{hook}\n\n{hashtags}".strip()

    print(f"Starting Facebook Reel upload: {video}")

    start = request_json(
        f"{BASE}/{PAGE_ID}/video_reels",
        {
            "upload_phase": "START",
            "access_token": PAGE_TOKEN,
        },
    )
    video_id = start.get("video_id")
    if not video_id:
        raise RuntimeError(f"Facebook Reel START did not return video_id: {start}")

    upload_url = start.get("upload_url") or f"https://rupload.facebook.com/video-upload/{API_VERSION}/{video_id}"
    size = os.path.getsize(video)

    with open(video, "rb") as f:
        upload_req = urllib.request.Request(
            upload_url,
            data=f.read(),
            method="POST",
            headers={
                "Authorization": f"OAuth {PAGE_TOKEN}",
                "offset": "0",
                "file_size": str(size),
                "Content-Type": "application/octet-stream",
            },
        )
        try:
            with urllib.request.urlopen(upload_req, timeout=180) as r:
                upload_result = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")
            raise RuntimeError(f"Facebook Reel upload HTTP {e.code}: {detail}") from e

    if upload_result.get("success") is not True:
        raise RuntimeError(f"Facebook Reel upload failed: {upload_result}")

    finish = request_json(
        f"{BASE}/{PAGE_ID}/video_reels",
        {
            "upload_phase": "FINISH",
            "video_id": video_id,
            "video_state": "PUBLISHED",
            "description": description,
            "access_token": PAGE_TOKEN,
        },
    )

    if finish.get("success") is not True:
        raise RuntimeError(f"Facebook Reel FINISH failed: {finish}")

    print(f"Facebook Reel published successfully: video_id={video_id}")


if __name__ == "__main__":
    main()
