"""
publish_instagram.py
Publishes the rendered carousel (posts/<date>/slide_1..4.png) to Instagram
using the Graph API. Images must already be pushed to the GitHub repo
(this script builds their public raw.githubusercontent.com URLs) since
the Graph API needs a public image URL, not a file upload.

Requires env vars:
  IG_ACCESS_TOKEN   - long-lived Instagram access token
  IG_USER_ID        - Instagram business account id (e.g. 178414374...)
  GITHUB_REPOSITORY - owner/repo (set automatically by GitHub Actions)
"""
import json
import os
import time
import urllib.request
import urllib.parse

ACCESS_TOKEN = os.environ["IG_ACCESS_TOKEN"]
IG_USER_ID = os.environ["IG_USER_ID"]
REPO = os.environ["GITHUB_REPOSITORY"]  # e.g. "sefa/factbite-bot"
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")

GRAPH_URL = "https://graph.instagram.com/v21.0"


def api_post(path, params):
    url = f"{GRAPH_URL}/{path}"
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def raw_url(path):
    path = path.replace(os.sep, "/")
    return f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{path}"


def main():
    with open("latest_post_dir.txt") as f:
        post_dir = f.read().strip()

    with open(os.path.join(post_dir, "caption.txt"), encoding="utf-8") as f:
        caption = f.read()

    slide_files = sorted(
        p for p in os.listdir(post_dir) if p.startswith("slide_") and p.endswith(".png")
    )

    # 1. Create a media container for each image (carousel item)
    item_ids = []
    for fname in slide_files:
        img_url = raw_url(os.path.join(post_dir, fname))
        print("creating item for", img_url)
        resp = api_post(f"{IG_USER_ID}/media", {
            "image_url": img_url,
            "is_carousel_item": "true",
            "access_token": ACCESS_TOKEN,
        })
        if "id" not in resp:
            raise RuntimeError(f"Failed to create item: {resp}")
        item_ids.append(resp["id"])
        time.sleep(1)

    # 2. Create the carousel container
    resp = api_post(f"{IG_USER_ID}/media", {
        "media_type": "CAROUSEL",
        "caption": caption,
        "children": ",".join(item_ids),
        "access_token": ACCESS_TOKEN,
    })
    if "id" not in resp:
        raise RuntimeError(f"Failed to create carousel: {resp}")
    creation_id = resp["id"]
    print("carousel creation id:", creation_id)

    # give Instagram a moment to process the container
    time.sleep(5)

    # 3. Publish it
    resp = api_post(f"{IG_USER_ID}/media_publish", {
        "creation_id": creation_id,
        "access_token": ACCESS_TOKEN,
    })
    print("publish result:", resp)
    if "id" not in resp:
        raise RuntimeError(f"Failed to publish: {resp}")

    print("Published! media id:", resp["id"])


if __name__ == "__main__":
    main()
