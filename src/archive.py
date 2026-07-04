"""アーカイブ(docs/data/papers.json)の読み書きモジュール.

GitHub Pages で docs/ フォルダを公開する前提。
docs/index.html が papers.json を読み込んで一覧表示する。
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

JST = timezone(timedelta(hours=9))
DATA_PATH = Path(__file__).parent.parent / "docs" / "data" / "papers.json"


def load_archive() -> list[dict]:
    if DATA_PATH.exists():
        return json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return []


def seen_pmids() -> set[str]:
    return {p["pmid"] for p in load_archive()}


def append(papers: list[dict]) -> None:
    """今日の論文をアーカイブ先頭に追加して保存する."""
    archive = load_archive()
    today = datetime.now(JST).strftime("%Y-%m-%d")
    new_entries = []
    for p in papers:
        entry = {
            "date": today,
            "pmid": p["pmid"],
            "title": p["title"],
            "title_ja": p.get("title_ja", ""),
            "journal": p["journal"],
            "year": p["year"],
            "authors": p["authors"],
            "summary": p.get("summary", ""),
            "key_points": p.get("key_points", []),
            "clinical_relevance": p.get("clinical_relevance", ""),
            "study_type": p.get("study_type", ""),
            "tags": p.get("tags", []),
            "pubmed_url": p["pubmed_url"],
            "doi_url": p.get("doi_url", ""),
            "pmc_url": p.get("pmc_url", ""),
        }
        new_entries.append(entry)

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(
        json.dumps(new_entries + archive, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    print(f"アーカイブ更新: +{len(new_entries)}本 (累計 {len(new_entries) + len(archive)}本)")
