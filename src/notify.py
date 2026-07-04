"""Claude API で論文の日本語要約を生成するモジュール."""
import json
import os
import time

import requests

API_URL = "https://api.anthropic.com/v1/messages"

PROMPT_TEMPLATE = """あなたは医学論文を要約する専門家です。以下の論文抄録を、{audience}向けに日本語で要約してください。

# 論文情報
タイトル: {title}
ジャーナル: {journal} ({year})
論文タイプ: {pub_types}

# 抄録
{abstract}

# 出力形式
以下のJSON形式のみで出力してください。前置きやMarkdownのコードブロックは不要です。

{{
  "title_ja": "タイトルの自然な日本語訳",
  "summary": "3〜4文の要約。研究デザイン・対象・主要結果(具体的な数値を含める)・結論を含める",
  "key_points": ["臨床的に重要なポイント(2〜3個、各1文)"],
  "clinical_relevance": "日常臨床や専門研修にどう関わるか1〜2文",
  "study_type": "RCT / メタ解析 / コホート / 症例対照 / ガイドライン / 総説 / その他 のいずれか",
  "tags": ["トピックタグ2〜4個(例: IBD, 内視鏡, 肝細胞癌)"]
}}

注意: 抄録に書かれている内容のみを使い、数値や結論を創作しないこと。"""


def summarize_paper(paper: dict, cfg: dict) -> dict:
    """1本の論文を要約し、paper に要約フィールドを追加して返す."""
    prompt = PROMPT_TEMPLATE.format(
        audience=cfg["summary"]["audience"],
        title=paper["title"],
        journal=paper["journal"],
        year=paper["year"],
        pub_types=", ".join(paper["pub_types"]),
        abstract=paper["abstract"][:6000],
    )
    body = {
        "model": cfg["summary"]["model"],
        "max_tokens": 1500,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "x-api-key": os.environ["ANTHROPIC_API_KEY"],
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    for attempt in range(3):
        try:
            r = requests.post(API_URL, headers=headers, json=body, timeout=120)
            r.raise_for_status()
            text = "".join(
                b.get("text", "") for b in r.json()["content"] if b.get("type") == "text"
            )
            clean = text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)
            return {**paper, **data}
        except (requests.RequestException, json.JSONDecodeError, KeyError) as e:
            print(f"  要約リトライ {attempt + 1}/3 (PMID {paper['pmid']}): {e}")
            time.sleep(5 * (attempt + 1))

    # 3回失敗したら要約なしで返す(パイプライン全体は止めない)
    return {
        **paper,
        "title_ja": paper["title"],
        "summary": "(要約の生成に失敗しました。原文をご確認ください)",
        "key_points": [],
        "clinical_relevance": "",
        "study_type": "その他",
        "tags": [],
    }


def summarize_all(papers: list[dict], cfg: dict) -> list[dict]:
    out = []
    for i, p in enumerate(papers, 1):
        print(f"要約中 {i}/{len(papers)}: {p['title'][:60]}...")
        out.append(summarize_paper(p, cfg))
        time.sleep(1)
    return out
