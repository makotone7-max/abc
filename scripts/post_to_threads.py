#!/usr/bin/env python3
"""Threads自動投稿スクリプト。

content/queue.txt の先頭1行を Threads (公式 Graph API) に投稿し、
成功したらそのキューから当該行を削除する。

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
QUEUE_PATH = os.path.join(os.path.dirname(__file__), "..", "content", "queue.txt")


def api_request(url, data=None, method="GET"):
    if data is not None:
        url = f"{url}?{urllib.parse.urlencode(data)}" if method == "GET" else url
    req = urllib.request.Request(url, method=method)
    if data is not None and method != "GET":
        req.data = urllib.parse.urlencode(data).encode()
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


def create_and_publish(user_id, access_token, text):
    container = api_request(
        f"{GRAPH_API_BASE}/{user_id}/threads",
        data={
            "media_type": "TEXT",
            "text": text,
            "access_token": access_token,
        },
        method="POST",
    )
    creation_id = container["id"]

    # Threadsは公開前にコンテナが処理されるまで少し待つ必要がある
    time.sleep(5)

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
        print("投稿キューが空です。content/queue.txt に投稿内容を追加してください。")
        return

    text = queue[0]
    print(f"投稿します: {text!r}")
    result = create_and_publish(user_id, access_token, text)
    print(f"投稿成功: {result}")

    write_queue(queue[1:])


if __name__ == "__main__":
    main()
