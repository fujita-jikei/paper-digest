"""要約テキストを読み上げ音声(mp3)に変換するモジュール(edge-tts使用)."""
import asyncio

import edge_tts


def build_script(papers: list[dict], cfg: dict) -> str:
    """メールの要約内容を、読み上げ用の台本テキストに組み立てる."""
    lines = [
        f"おはようございます。本日の{cfg['specialty_name']}論文ダイジェストです。"
        f"新着は{len(papers)}本です。"
    ]
    for i, p in enumerate(papers, 1):
        title = p.get("title_ja") or p["title"]
        lines.append(f"{i}本目。{title}。{p['journal']}より。")
        if p.get("study_type"):
            lines.append(f"研究デザインは{p['study_type']}です。")
        if p.get("summary"):
            lines.append(p["summary"])
        if p.get("key_points"):
            lines.append("重要ポイントです。")
            lines.extend(p["key_points"])
        if p.get("clinical_relevance"):
            lines.append(f"臨床的な意義としては、{p['clinical_relevance']}")
        lines.append("続いて。" if i < len(papers) else "")
    lines.append("以上、本日のダイジェストでした。詳細はメール本文のリンクからご確認ください。")
    return "\n".join(filter(None, lines))


def generate_mp3(papers: list[dict], cfg: dict, out_path: str = "digest.mp3") -> str:
    """台本をmp3に変換して保存し、ファイルパスを返す."""
    audio_cfg = cfg.get("audio", {})
    voice = audio_cfg.get("voice", "ja-JP-NanamiNeural")  # 男声なら ja-JP-KeitaNeural
    rate = audio_cfg.get("rate", "+10%")  # 読み上げ速度(+20%等で速く)

    text = build_script(papers, cfg)

    async def _run():
        await edge_tts.Communicate(text, voice=voice, rate=rate).save(out_path)

    asyncio.run(_run())
    print(f"音声生成完了: {out_path}")
    return out_path
