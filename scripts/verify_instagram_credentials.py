#!/usr/bin/env python3
"""INSTAGRAM_USER_ID / INSTAGRAM_ACCESS_TOKEN の疎通確認用スクリプト。

投稿は一切行わず、GET /me を叩いてトークンが有効か確認するだけ。
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

GRAPH_API_BASE = "https://graph.instagram.com/v21.0"


def main():
    user_id = os.environ.get("INSTAGRAM_USER_ID")
    access_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")

    if not user_id:
        print("NG: INSTAGRAM_USER_ID が空です。Secretsの登録名・登録先(Repository secrets)を確認してください。", file=sys.stderr)
        sys.exit(1)
    if not access_token:
        print("NG: INSTAGRAM_ACCESS_TOKEN が空です。Secretsの登録名・登録先(Repository secrets)を確認してください。", file=sys.stderr)
        sys.exit(1)

    query = urllib.parse.urlencode({"fields": "id,username", "access_token": access_token})
    url = f"{GRAPH_API_BASE}/me?{query}"

    try:
        with urllib.request.urlopen(url) as res:
            data = json.loads(res.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"NG: Instagram APIがトークンを拒否しました (HTTP {e.code}): {body}", file=sys.stderr)
        sys.exit(1)

    print(f"OK: トークンは有効です。API上のアカウント: id={data.get('id')}, username={data.get('username')}")

    if str(data.get("id")) != str(user_id):
        print(
            f"警告: INSTAGRAM_USER_ID ({user_id}) と、トークンから解決されたid ({data.get('id')}) が一致しません。"
            " 投稿先アカウントを取り違えている可能性があります。",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
