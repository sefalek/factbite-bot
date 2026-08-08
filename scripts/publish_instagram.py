"""
publish_instagram.py
Publishes the rendered carousel to Instagram and, when enabled, publishes
slide 1 as an Instagram Story as an automatic follow-up.
"""
import json
import os
import time
import urllib.request
import urllib.parse

ACCESS_TOKEN = os.environ["IG_ACCESS_TOKEN"]
IG_USER_ID = os.environ["IG_USER_ID"]
REPO = os.environ["GITHUB_REPOSITORY"]
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


def clean_hashtags(values):
    result = []
    for value in values or []:
        value = str(value).strip().replace(" ", "")
        if not value:
            continue
        if not value.startswith("#"):
            value = "#" + value
        if value.lower() not in {x.lower() for x in result}:
            result.append(value)
    if not any(x.lower() == "#factbite" for x in result):
        result.insert(0, "#FactBite")
    return result[:8]


def publish_story(story_image_url):
    """Publish the first carousel slide as a Story.

    This is a new Story containing the post artwork; Instagram's API does not
    expose the consumer-app 'Share this feed post to Story' button directly.
    """
    print("creating Instagram Story")
    resp = api_post(f"{IG_USER_ID}/media", {
        "image_url": story_image_url,
        "media_type": "STORIES",
        "access_token": ACCESS_TOKEN,
    })
    if "id" not in resp:
        raise RuntimeError(f"Failed to create story container: {resp}")
    story_id = resp["id"]
    time.sleep(5)
    resp = api_post(f"{IG_USER_ID}/media_publish", {
        "creation_id": story_id,
        "access_token": ACCESS_TOKEN,
    })
    if "id" not in resp:
        raise RuntimeError(f"Failed to publish story: {resp}")
    print("Story published! media id:", resp["id"])


def main():
    with open("latest_post_dir.txt") as f:
        post_dir = f.read().strip()
    with open(os.path.join(post_dir, "caption.txt"), encoding="utf-8") as f:
        caption = f.read()

    # Ensure every post gets topic-specific hashtags from fact.json.
    try:
        with open("fact.json", encoding="utf-8") as f:
            fact = json.load(f)
        hashtags = clean_hashtags(fact.get("hashtags"))
        if hashtags:
            caption = caption.rstrip() + "\n\n" + " ".join(hashtags)
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    slide_files = sorted(
        p for p in os.listdir(post_dir) if p.startswith("slide_") and p.endswith(".png")
    )
    if not slide_files:
        raise RuntimeError(f"No carousel slides found in {post_dir}")

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
    time.sleep(5)

    resp = api_post(f"{IG_USER_ID}/media_publish", {
        "creation_id": creation_id,
        "access_token": ACCESS_TOKEN,
    })
    print("publish result:", resp)
    if "id" not in resp:
        raise RuntimeError(f"Failed to publish: {resp}")

    print("Published! media id:", resp["id"])

    # Publish slide 1 as a Story after the feed post succeeds.
    if os.environ.get("PUBLISH_STORY", "true").lower() == "true":
        story_url = raw_url(os.path.join(post_dir, slide_files[0]))
        try:
            publish_story(story_url)
        except Exception as exc:
            # Do not mark the feed post as failed just because the optional story failed.
            print("WARNING: Story publishing failed:", exc)


if __name__ == "__main__":
    main()
