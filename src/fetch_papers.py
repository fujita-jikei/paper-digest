"""毎朝の論文ダイジェスト・パイプライン本体.

流れ: PubMed収集 → Claude要約 → メール送信 → アーカイブ保存
GitHub Actions から毎朝実行される。
"""
import os
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))

import archive
import fetch_papers
import notify
import summarize


def main() -> None:
    cfg = yaml.safe_load(
        (Path(__file__).parent.parent / "config.yaml").read_text(encoding="utf-8")
    )
    archive_url = os.environ.get("ARCHIVE_URL", "")

    print("=== 論文収集 ===")
    papers = fetch_papers.collect(cfg, archive.seen_pmids())
    if not papers:
        print("本日の新着はありませんでした。終了します。")
        return
    print(f"{len(papers)}本の新着を取得")

    print("=== 要約生成 ===")
    papers = summarize.summarize_all(papers, cfg)

    print("=== メール送信 ===")
    notify.send_email(papers, cfg, archive_url)

    print("=== アーカイブ更新 ===")
    archive.append(papers)

    print("完了 ✅")


if __name__ == "__main__":
    main()
