"""要約結果をHTMLメールで送信するモジュール(Gmail SMTP)."""
import os
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.audio import MIMEAudio
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

JST = timezone(timedelta(hours=9))

STYLE = """
  body { font-family: 'Hiragino Sans', 'Noto Sans JP', sans-serif; color: #1a2421;
         max-width: 640px; margin: 0 auto; padding: 16px; line-height: 1.7; }
  .head { border-bottom: 3px solid #0f6b5c; padding-bottom: 8px; margin-bottom: 20px; }
  .head h1 { font-size: 20px; margin: 0; }
  .head p { color: #667; font-size: 13px; margin: 4px 0 0; }
  .paper { border: 1px solid #dde3e0; border-radius: 10px; padding: 16px 18px; margin-bottom: 18px; }
  .badge { display: inline-block; background: #0f6b5c; color: #fff; font-size: 11px;
           border-radius: 4px; padding: 2px 8px; margin-right: 6px; }
  .tag { display: inline-block; background: #f2ede2; color: #8a5a1e; font-size: 11px;
         border-radius: 4px; padding: 2px 8px; margin-right: 4px; }
  .title-ja { font-size: 16px; font-weight: 700; margin: 8px 0 2px; }
  .title-en { font-size: 12px; color: #667; margin: 0 0 8px; }
  .meta { font-size: 12px; color: #556; margin-bottom: 10px; }
  .summary { font-size: 14px; margin: 0 0 10px; }
  ul.kp { margin: 0 0 10px; padding-left: 20px; font-size: 13px; }
  .rel { font-size: 13px; background: #f0f7f5; border-left: 3px solid #0f6b5c;
         padding: 8px 12px; margin-bottom: 12px; }
  .links a { font-size: 13px; color: #0f6b5c; margin-right: 14px; }
  .foot { font-size: 12px; color: #778; border-top: 1px solid #dde3e0; padding-top: 12px; }
"""


def build_html(papers: list[dict], cfg: dict, archive_url: str) -> str:
    today = datetime.now(JST).strftime("%Y年%m月%d日")
    cards = []
    for p in papers:
        kp = "".join(f"<li>{k}</li>" for k in p.get("key_points", []))
        tags = "".join(f'<span class="tag">{t}</span>' for t in p.get("tags", []))
        links = f'<a href="{p["pubmed_url"]}">PubMed</a>'
        if p.get("doi_url"):
            links += f'<a href="{p["doi_url"]}">本文 (DOI)</a>'
        if p.get("pmc_url"):
            links += f'<a href="{p["pmc_url"]}">無料全文 (PMC)</a>'
        rel = (
            f'<div class="rel">{p["clinical_relevance"]}</div>'
            if p.get("clinical_relevance")
            else ""
        )
        cards.append(f"""
        <div class="paper">
          <div><span class="badge">{p.get("study_type", "")}</span>{tags}</div>
          <p class="title-ja">{p.get("title_ja", p["title"])}</p>
          <p class="title-en">{p["title"]}</p>
          <p class="meta">{p["journal"]} ({p["year"]}) — {p["authors"]}</p>
          <p class="summary">{p.get("summary", "")}</p>
          <ul class="kp">{kp}</ul>
          {rel}
          <div class="links">{links}</div>
        </div>""")

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{STYLE}</style></head>
<body>
  <div class="head">
    <h1>{cfg["specialty_name"]} 論文ダイジェスト</h1>
    <p>{today} / {len(papers)}本の新着</p>
  </div>
  {"".join(cards)}
  <div class="foot">
    <p>📚 過去の論文は <a href="{archive_url}">アーカイブ</a> でいつでも見返せます。</p>
    <p>🎧 じっくり聴きたい論文は、上の「無料全文 (PMC)」や「本文 (DOI)」のリンクを
       NotebookLM に貼り付けると対談形式の音声概要が作れます。</p>
  </div>
</body></html>"""


def send_email(
    papers: list[dict], cfg: dict, archive_url: str, attachment: str | None = None
) -> None:
    sender = os.environ["GMAIL_ADDRESS"]
    password = os.environ["GMAIL_APP_PASSWORD"]
    to = os.environ.get("MAIL_TO") or cfg["email"]["to"] or sender

    today = datetime.now(JST).strftime("%-m/%-d")
    msg = MIMEMultipart("mixed")
    msg["Subject"] = f'{cfg["email"]["subject_prefix"]}{today} {cfg["specialty_name"]} 新着{len(papers)}本'
    msg["From"] = sender
    msg["To"] = to
    msg.attach(MIMEText(build_html(papers, cfg, archive_url), "html", "utf-8"))

    # 音声ファイルを添付(生成に失敗していた場合はスキップ)
    if attachment and Path(attachment).exists():
        part = MIMEAudio(Path(attachment).read_bytes(), _subtype="mpeg")
        fname = f"digest_{datetime.now(JST).strftime('%Y%m%d')}.mp3"
        part.add_header("Content-Disposition", "attachment", filename=fname)
        msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.send_message(msg)
    print(f"メール送信完了: {to}")
