# 📚 毎朝の論文ダイジェスト自動化システム

毎朝6時に消化器関連の新着論文を自動収集し、日本語要約をメールでお届けして、アーカイブサイトに蓄積するシステムです。サーバー不要・GitHub だけで完結します。

## 仕組み

```
毎朝6:00 (GitHub Actions)
  → PubMed E-utilities で新着論文を検索
  → Claude API で日本語要約を生成
  → Gmail でダイジェストメールを送信
  → GitHub Pages のアーカイブサイトに蓄積
```

じっくり聴きたい論文があれば、メール内の「無料全文 (PMC)」や「本文 (DOI)」のリンクを NotebookLM に貼り付ければ、対談形式の高品質な音声概要が作れます(深掘りはNotebookLM、毎日の網羅はこのシステム、という分担です)。

## セットアップ手順(初回のみ・約20分)

### 1. GitHub リポジトリを作成してアップロード

1. GitHub で新しいリポジトリを作成(例: `paper-digest`)。**Public** にすると GitHub Pages が無料で使えます(アーカイブが誰でも閲覧可能になる点に注意。Private にしたい場合は GitHub Pro 等が必要)
2. このフォルダの中身を丸ごとアップロード
   - Web からなら「Add file → Upload files」でドラッグ&ドロップ
   - コマンドなら:
     ```bash
     cd gi-paper-digest
     git init && git add . && git commit -m "initial"
     git remote add origin https://github.com/あなたのユーザー名/paper-digest.git
     git push -u origin main
     ```

### 2. Gmail のアプリパスワードを取得

通常のGoogleパスワードは使えません。専用の「アプリパスワード」を発行します。

1. Google アカウントで **2段階認証** を有効化(必須)
2. https://myaccount.google.com/apppasswords にアクセス
3. アプリ名(例: `paper-digest`)を入力して「作成」
4. 表示された **16桁のパスワード** を控える

### 3. GitHub Secrets を設定

リポジトリの **Settings → Secrets and variables → Actions → New repository secret** から、以下の4つを登録します。

| Secret 名 | 値 |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic の API キー(https://platform.claude.com で取得) |
| `GMAIL_ADDRESS` | 送信元の Gmail アドレス |
| `GMAIL_APP_PASSWORD` | 手順2で取得した16桁のアプリパスワード |
| `MAIL_TO` | 受信したいメールアドレス(Gmail 以外でも可) |

### 4. GitHub Pages を有効化(アーカイブサイト)

1. リポジトリの **Settings → Pages**
2. Source: **Deploy from a branch**
3. Branch: **main**、フォルダ: **/docs** を選択して Save
4. 数分後、`https://あなたのユーザー名.github.io/paper-digest/` でアーカイブが公開されます

### 5. 動作テスト(手動実行)

1. リポジトリの **Actions** タブ → **Daily Paper Digest**
2. **Run workflow** ボタンで手動実行
3. 数分でメールが届き、アーカイブサイトに論文が表示されれば成功 🎉

以降は毎朝6時(JST)に自動実行されます。

## カスタマイズ(`config.yaml` を編集するだけ)

**専門を変える(例: 消化器 → 循環器)** — `specialty_name`、`search.journals`、`search.keywords` を書き換えるだけです。コードの変更は不要です。

**その他の調整** — 1日の論文数上限(`max_papers`)、遡る日数(`days_back`)、読者像(`summary.audience`: 「専門医」に変えると要約の深さが変わります)なども自由に変更できます。

配信時刻を変えたい場合は `.github/workflows/daily.yml` の cron を編集します(UTC表記。JST−9時間。例: 朝5時なら `0 20 * * *`)。

## 運用コスト

- GitHub Actions / Pages: **無料**(Publicリポジトリの場合)
- PubMed E-utilities: **無料**
- Claude API: 1日8本の要約で **数円〜十数円/日** 程度が目安(従量課金。正確な料金は https://docs.claude.com を参照)

## トラブルシューティング

- **メールが届かない** → Actions のログを確認。`Authentication failed` なら アプリパスワードの再確認(スペースは除いて入力)
- **論文が0本** → `days_back` を増やす、またはキーワードを広げる。週末はジャーナルの新着登録が少ないこともあります
- **実行時刻が遅れる** → GitHub Actions の cron は仕様上、混雑時に数十分遅れることがあります
- **要約の質を上げたい** → `config.yaml` の `summary.audience` を具体的に(例: 「消化器内視鏡を専門とする医師」)

## ファイル構成

```
├── config.yaml              # 設定(専門・ジャーナル・キーワード)← ここだけ触ればOK
├── src/
│   ├── main.py              # パイプライン本体
│   ├── fetch_papers.py      # PubMed 収集
│   ├── summarize.py         # Claude API 要約
│   ├── notify.py            # メール送信
│   └── archive.py           # アーカイブ管理
├── docs/
│   ├── index.html           # アーカイブ閲覧ページ(GitHub Pages)
│   └── data/papers.json     # 蓄積データ
└── .github/workflows/daily.yml  # 毎朝の自動実行設定
```
