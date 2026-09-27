#!/usr/bin/env python3
"""Instagram自動投稿スクリプト。

content/instagram_queue.jsonl の先頭1行(画像パス+キャプション)を
Instagram (Graph API / Instagram Login) に投稿し、成功したら
そのキューから当該行を削除する。

画像はこのリポジトリ内のファイルを、GitHub上の生ファイルURL
(raw.githubusercontent.com)経由でInstagramに参照させる。
そのためリポジトリはpublicで、画像は事前にmainブランチへ
pushされている必要がある。

必要な環境変数:
  INSTAGRAM_USER_ID       投稿先のInstagramユーザーID
  INSTAGRAM_ACCESS_TOKEN  長期アクセストークン(instagram_business_content_publish権限)
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

GRAPH_API_BASE = "https://graph.instagram.com/v21.0"
RAW_BASE = "https://raw.githubusercontent.com/makotone7-max/abc/main"
QUEUE_PATH = os.path.join(os.path.dirname(__file__), "..", "content", "instagram_queue.jsonl")


def api_request(url, data=None, method="GET"):
    if data is not None and method != "GET":
        req = urllib.request.Request(url, method=method, data=urllib.parse.urlencode(data).encode())
    else:
        if data is not None:
            url = f"{url}?{urllib.parse.urlencode(data)}"
        req = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"Instagram API error {e.code}: {body}") from e


def read_queue():
    if not os.path.exists(QUEUE_PATH):
        return []
    with open(QUEUE_PATH, encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f if line.strip()]


def write_queue(lines):
    with open(QUEUE_PATH, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")


def create_and_publish(user_id, access_token, image_url, caption):
    container = api_request(
        f"{GRAPH_API_BASE}/{user_id}/media",
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": access_token,
        },
        method="POST",
    )
    creation_id = container["id"]

    # Instagramは公開前にコンテナが処理されるまで少し待つ必要がある
    time.sleep(10)

    result = api_request(
        f"{GRAPH_API_BASE}/{user_id}/media_publish",
        data={
            "creation_id": creation_id,
            "access_token": access_token,
        },
        method="POST",
    )
    return result


def main():
    user_id = os.environ.get("INSTAGRAM_USER_ID")
    access_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")
    if not user_id or not access_token:
        print("INSTAGRAM_USER_ID / INSTAGRAM_ACCESS_TOKEN が設定されていません", file=sys.stderr)
        sys.exit(1)

    queue = read_queue()
    if not queue:
        print("投稿キューが空です。content/instagram_queue.jsonl に投稿内容を追加してください。")
        return

    entry = json.loads(queue[0])
    image_url = f"{RAW_BASE}/{entry['image']}"
    caption = entry["caption"]

    print(f"投稿します: image={image_url!r}")
    result = create_and_publish(user_id, access_token, image_url, caption)
    print(f"投稿成功: {result}")

    write_queue(queue[1:])


if __name__ == "__main__":
    main()
