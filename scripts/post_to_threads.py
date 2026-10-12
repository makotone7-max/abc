#!/usr/bin/env python3
"""Threads自動投稿スクリプト。

content/queue.jsonl の先頭1行を Threads (公式 Graph API) に投稿し、
成功したらそのキューから当該行を削除する。

キューの各行はJSON形式: {"text": "...", "image": "content/images/xxx.jpg"}
"image"は省略可能で、あればIMAGE投稿、なければTEXT投稿になる。
画像はこのリポジトリが public であることを利用し、
raw.githubusercontent.com 経由でThreadsに参照させる(画像は事前にmain
ブランチへpushされている必要がある)。

必要な環境変数:
  THREADS_USER_ID     投稿先の Threads ユーザーID
  THREADS_ACCESS_TOKEN 長期アクセストークン(threads_basic, threads_content_publish 権限)
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

GRAPH_API_BASE = "https://graph.threads.net/v1.0"
RAW_BASE = "https://raw.githubusercontent.com/makotone7-max/abc/main"
QUEUE_PATH = os.path.join(os.path.dirname(__file__), "..", "content", "queue.jsonl")


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
        raise RuntimeError(f"Threads API error {e.code}: {body}") from e


def read_queue():
    if not os.path.exists(QUEUE_PATH):
        return []
    with open(QUEUE_PATH, encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f if line.strip()]


def write_queue(lines):
    with open(QUEUE_PATH, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")


def create_and_publish(user_id, access_token, text, image_path):
    data = {
        "text": text,
        "access_token": access_token,
    }
    if image_path:
        data["media_type"] = "IMAGE"
        data["image_url"] = f"{RAW_BASE}/{image_path}"
    else:
        data["media_type"] = "TEXT"

    container = api_request(
        f"{GRAPH_API_BASE}/{user_id}/threads",
        data=data,
        method="POST",
    )
    creation_id = container["id"]

    # Threadsは公開前にコンテナが処理されるまで少し待つ必要がある
    time.sleep(10 if image_path else 5)

    result = api_request(
        f"{GRAPH_API_BASE}/{user_id}/threads_publish",
        data={
            "creation_id": creation_id,
            "access_token": access_token,
        },
        method="POST",
    )
    return result


def main():
    user_id = os.environ.get("THREADS_USER_ID")
    access_token = os.environ.get("THREADS_ACCESS_TOKEN")
    if not user_id or not access_token:
        print("THREADS_USER_ID / THREADS_ACCESS_TOKEN が設定されていません", file=sys.stderr)
        sys.exit(1)

    queue = read_queue()
    if not queue:
        print("投稿キューが空です。content/queue.jsonl に投稿内容を追加してください。")
        return

    entry = json.loads(queue[0])
    text = entry["text"]
    image_path = entry.get("image")

    print(f"投稿します: text={text!r} image={image_path!r}")
    result = create_and_publish(user_id, access_token, text, image_path)
    print(f"投稿成功: {result}")

    write_queue(queue[1:])


if __name__ == "__main__":
    main()
