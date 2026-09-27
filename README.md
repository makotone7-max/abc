# abc

## Threads 自動投稿

Threads公式API (Graph API) を使い、GitHub Actionsの定期実行で `content/queue.txt` の投稿キューを1件ずつ自動投稿する仕組みです。

### 仕組み

- `content/queue.txt`: 1行1投稿。上から順に投稿し、投稿に成功した行はキューから削除してコミットされます。
- `scripts/post_to_threads.py`: キューの先頭を読み取り、Threads APIでコンテナ作成→公開を行うスクリプト。
- `.github/workflows/post-to-threads.yml`: 毎日 JST 9:00 (UTC 0:00) に自動実行するワークフロー。手動実行 (`workflow_dispatch`) にも対応。

### セットアップ手順

1. **Meta for Developersでアプリを作成**
   - https://developers.facebook.com/apps/ で新規アプリ (種類: 「その他」→「Threads API を使用」など) を作成
   - アプリに「Threads API」プロダクトを追加

2. **Threadsアカウントを連携し権限を許可**
   - 投稿したいThreadsアカウントでログインし、アプリの認可フローを実行
   - 必要スコープ: `threads_basic`, `threads_content_publish`

3. **長期アクセストークンを取得**
   - 認可コード→短期トークン→長期トークン(約60日間有効)の順に交換
   - 長期トークンは定期的に (期限が切れる前に) リフレッシュが必要です

4. **Threads User IDを取得**
   - `GET https://graph.threads.net/v1.0/me?fields=id,username&access_token=...` などで自分のIDを確認

5. **GitHub Secretsに登録**
   - このリポジトリの Settings → Secrets and variables → Actions で以下を登録
     - `THREADS_USER_ID`
     - `THREADS_ACCESS_TOKEN`

6. **投稿内容を追加**
   - `content/queue.txt` に投稿したいテキストを1行ずつ追記してpush

7. **Secretsの疎通確認（投稿は消費しません）**
   - Actionsタブから `Verify Threads Credentials` ワークフローを手動実行 (`Run workflow`)
   - `THREADS_USER_ID` / `THREADS_ACCESS_TOKEN` が空でないか、トークンがThreads APIに受理されるかだけを確認します（実際の投稿は行われません）
   - 失敗する場合は Settings → Secrets and variables → **Actions** の **Repository secrets** に、キー名を完全一致で登録できているか確認してください（Environment secretsやCodespaces secretsに登録すると届きません）

8. **実際の投稿で動作確認**
   - 疎通確認がOKになったら、Actionsタブから `Post to Threads` ワークフローを手動実行 (`Run workflow`) して実際に投稿されるか確認

### 注意事項

- 長期アクセストークンには有効期限があるため、失効前に再取得してSecretsを更新してください。
- 画像付き投稿や返信投稿など高度な機能が必要な場合は `scripts/post_to_threads.py` の `media_type` や追加パラメータを拡張してください。