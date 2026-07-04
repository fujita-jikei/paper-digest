"""PubMed E-utilities から新着論文を収集するモジュール."""
import time
import xml.etree.ElementTree as ET

import requests

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
TOOL_PARAMS = {"tool": "paper-digest", "email": "digest@example.com"}


def build_query(cfg: dict) -> str:
    """config.yaml の設定から PubMed 検索クエリを組み立てる."""
    s = cfg["search"]
    kw = " OR ".join(f'"{k}"[Title/Abstract] OR "{k}"[MeSH Terms]' for k in s["keywords"])

    # 専門誌: 新着をそのまま拾う / 総合誌: キーワード合致のみ
    general = {"N Engl J Med", "Lancet", "JAMA", "BMJ", "Ann Intern Med", "JAMA Intern Med"}
    specialty_j = [j for j in s["journals"] if j not in general]
    general_j = [j for j in s["journals"] if j in general]

    parts = []
    if specialty_j:
        parts.append("(" + " OR ".join(f'"{j}"[Journal]' for j in specialty_j) + ")")
    if general_j and kw:
        gj = " OR ".join(f'"{j}"[Journal]' for j in general_j)
        parts.append(f"(({gj}) AND ({kw}))")
    if not parts and kw:
        parts.append(f"({kw})")

    query = "(" + " OR ".join(parts) + ") AND hasabstract[text]"
    for t in s.get("exclude_types", []):
        query += f' NOT "{t}"[Publication Type]'
    return query


def search_pmids(cfg: dict) -> list[str]:
    """esearch で直近の新着 PMID を取得する."""
    s = cfg["search"]
    params = {
        "db": "pubmed",
        "term": build_query(cfg),
        "reldate": s["days_back"],
        "datetype": "edat",
        "retmax": s["max_papers"] * 3,  # 除外・重複を見込んで多めに取る
        "sort": "date",
        "retmode": "json",
        **TOOL_PARAMS,
    }
    r = requests.get(f"{EUTILS}/esearch.fcgi", params=params, timeout=30)
    r.raise_for_status()
    return r.json()["esearchresult"].get("idlist", [])


def _text(elem) -> str:
    """要素配下の全テキストを結合(<i>タグ等の入れ子対策)."""
    return "".join(elem.itertext()).strip() if elem is not None else ""


def fetch_details(pmids: list[str]) -> list[dict]:
    """efetch で論文詳細(タイトル・抄録・DOI等)を取得する."""
    if not pmids:
        return []
    params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml", **TOOL_PARAMS}
    r = requests.get(f"{EUTILS}/efetch.fcgi", params=params, timeout=60)
    r.raise_for_status()
    root = ET.fromstring(r.content)

    papers = []
    for art in root.findall(".//PubmedArticle"):
        pmid = _text(art.find(".//PMID"))
        title = _text(art.find(".//ArticleTitle"))

        # 抄録(ラベル付きセクションを結合)
        abst_parts = []
        for ab in art.findall(".//Abstract/AbstractText"):
            label = ab.get("Label")
            txt = _text(ab)
            abst_parts.append(f"{label}: {txt}" if label else txt)
        abstract = "\n".join(abst_parts)

        journal = _text(art.find(".//Journal/ISOAbbreviation")) or _text(
            art.find(".//Journal/Title")
        )
        year = _text(art.find(".//JournalIssue/PubDate/Year"))

        authors = []
        for au in art.findall(".//AuthorList/Author")[:3]:
            last, init = _text(au.find("LastName")), _text(au.find("Initials"))
            if last:
                authors.append(f"{last} {init}".strip())
        n_authors = len(art.findall(".//AuthorList/Author"))
        author_str = ", ".join(authors) + (" ほか" if n_authors > 3 else "")

        doi = pmc = ""
        for aid in art.findall(".//ArticleIdList/ArticleId"):
            if aid.get("IdType") == "doi":
                doi = _text(aid)
            elif aid.get("IdType") == "pmc":
                pmc = _text(aid)

        pub_types = [_text(pt) for pt in art.findall(".//PublicationType")]

        if not (title and abstract):
            continue
        papers.append(
            {
                "pmid": pmid,
                "title": title,
                "abstract": abstract,
                "journal": journal,
                "year": year,
                "authors": author_str,
                "doi": doi,
                "pmc": pmc,
                "pub_types": pub_types,
                "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "doi_url": f"https://doi.org/{doi}" if doi else "",
                "pmc_url": f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc}/" if pmc else "",
            }
        )
    return papers


def collect(cfg: dict, seen_pmids: set[str]) -> list[dict]:
    """新着論文を収集し、既読(アーカイブ済み)を除外して返す."""
    pmids = [p for p in search_pmids(cfg) if p not in seen_pmids]
    time.sleep(0.4)  # E-utilities のレート制限(3req/s)への配慮
    papers = fetch_details(pmids)
    return papers[: cfg["search"]["max_papers"]]
