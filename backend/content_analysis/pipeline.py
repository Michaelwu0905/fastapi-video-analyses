from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .loaders import read_transcript, resolve_source
from .llm import is_llm_configured, llm_answer, llm_extract_tags, llm_summarize


def parse_segments(raw_text: str) -> list[Document]:
    pattern = re.compile(r"^\[(?P<ts>\d{2}:\d{2})\]\s*(?P<text>.+)$")
    documents: list[Document] = []

    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        matched = pattern.match(line)
        if matched:
            content = matched.group("text")
        else:
            content = line
        documents.append(
            Document(
                page_content=content,
                metadata={
                    "source": "transcript",
                },
            )
        )
    return documents


def split_documents(documents: Iterable[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=120,
        chunk_overlap=20,
        separators=["\n", "。", "，", " ", ""],
    )
    return splitter.split_documents(list(documents))


def tokenize(text: str) -> set[str]:
    lowered = text.lower()
    tokens: set[str] = set()

    for part in re.findall(r"[a-zA-Z0-9_]+", lowered):
        if len(part) > 1:
            tokens.add(part)

    for part in re.findall(r"[\u4e00-\u9fff]{2,}", lowered):
        tokens.add(part)
        tokens.update(part[index : index + 2] for index in range(len(part) - 1))

    return tokens


def score(query: str, document: Document) -> int:
    query_tokens = tokenize(query)
    content_tokens = tokenize(document.page_content)
    overlap = query_tokens & content_tokens
    return len(overlap)


def retrieve(question: str, documents: list[Document], top_k: int = 3) -> list[Document]:
    ranked = sorted(
        documents,
        key=lambda doc: (score(question, doc), len(doc.page_content)),
        reverse=True,
    )
    best = [doc for doc in ranked if score(question, doc) > 0]
    return best[:top_k] if best else ranked[:top_k]


def summarize(documents: list[Document], max_items: int = 4) -> str:
    picked = documents[:max_items]
    lines = [f"- {doc.page_content}" for doc in picked]
    return "视频内容摘要：\n" + "\n".join(lines)


def answer_question(question: str, documents: list[Document]) -> str:
    evidence = retrieve(question, documents)
    snippets = [f"- {doc.page_content}" for doc in evidence]
    return (
        f"问题：{question}\n"
        "基于检索到的片段，最相关内容如下：\n"
        + "\n".join(snippets)
    )


def extract_tags(documents: list[Document], limit: int = 5) -> list[str]:
    phrase_scores: dict[str, int] = {}
    keyword_whitelist = {
        "LangChain",
        "B站",
        "视频内容识别",
        "Whisper",
        "FunASR",
        "向量检索",
        "摘要生成",
        "问答接口",
        "OCR",
        "抽帧",
        "多模态大模型",
    }
    stopwords = {"大家好", "这期视频", "第一部分", "第二部分", "第三部分", "实际项目", "用户提问", "后续"}

    for document in documents:
        content = document.page_content
        for keyword in keyword_whitelist:
            if keyword in content:
                phrase_scores[keyword] = phrase_scores.get(keyword, 0) + 2

        for phrase in re.findall(r"[\u4e00-\u9fffA-Za-z]{2,12}", content):
            if phrase in stopwords:
                continue
            if phrase.endswith(("的是", "可以", "我们")):
                continue
            if len(phrase) < 2:
                continue
            if phrase in keyword_whitelist or 2 < len(phrase) <= 8:
                phrase_scores[phrase] = phrase_scores.get(phrase, 0) + 1

    ranked = sorted(phrase_scores.items(), key=lambda item: (-item[1], item[0]))
    return [token for token, _score in ranked[:limit]]


def build_highlights(documents: list[Document], max_items: int = 3) -> list[str]:
    return [document.page_content for document in documents[:max_items]]


def generate_summary(documents: list[Document], use_llm: bool) -> tuple[str, str]:
    if use_llm and is_llm_configured():
        return llm_summarize(documents), "llm"
    return summarize(documents), "fallback"


def generate_answer(question: str, documents: list[Document], use_llm: bool) -> tuple[str, str]:
    evidence = retrieve(question, documents)
    if use_llm and is_llm_configured():
        return llm_answer(question, evidence), "llm"
    return answer_question(question, documents), "fallback"


def generate_tags(documents: list[Document], use_llm: bool) -> tuple[list[str], str]:
    if use_llm and is_llm_configured():
        return llm_extract_tags(documents), "llm"
    return extract_tags(documents), "fallback"


def build_pipeline():
    load_chain = RunnableLambda(
        lambda payload: parse_segments(read_transcript(Path(payload["path"])))
    )
    split_chain = RunnableLambda(split_documents)
    return load_chain | split_chain


def run_demo(
    input_path: Path | None = None,
    bv: str | None = None,
    url: str | None = None,
    question: str | None = None,
    use_llm: bool = True,
    use_real_bilibili: bool = False,
) -> dict[str, object]:
    source = resolve_source(
        input_path=input_path,
        bv=bv,
        url=url,
        use_real_bilibili=use_real_bilibili,
    )
    pipeline = build_pipeline()
    documents = pipeline.invoke({"path": str(source.transcript_path)})
    summary, summary_mode = generate_summary(documents, use_llm)
    tags, tags_mode = generate_tags(documents, use_llm)
    payload: dict[str, object] = {
        "source": {
            "type": source.source_type,
            "title": source.title,
            "identifier": source.identifier,
            "uploader": source.uploader,
            "description": source.description,
            "transcript_path": str(source.transcript_path),
            "url": source.url,
        },
        "summary": summary,
        "summary_mode": summary_mode,
        "tags": tags,
        "tags_mode": tags_mode,
        "highlights": build_highlights(documents),
        "chunks": [doc.page_content for doc in documents],
    }
    if question:
        answer, answer_mode = generate_answer(question, documents, use_llm)
        payload["answer"] = answer
        payload["answer_mode"] = answer_mode
    return payload


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Minimal LangChain MVP for understanding Bilibili-like video transcripts.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Path to a timestamped transcript text file.",
    )
    parser.add_argument(
        "--bv",
        type=str,
        default=None,
        help="Bilibili BV id. The current MVP resolves it from the local sample index.",
    )
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="Bilibili video URL. The current MVP extracts the BV id and resolves it from the local sample index.",
    )
    parser.add_argument(
        "--question",
        type=str,
        default=None,
        help="Question to ask against the parsed transcript.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of plain text.",
    )
    parser.add_argument(
        "--disable-llm",
        action="store_true",
        help="Disable Moonshot/Kimi and use local fallback summarization and retrieval.",
    )
    parser.add_argument(
        "--real-bilibili",
        action="store_true",
        help="Use yt-dlp and whisper to download/transcribe a real Bilibili URL or BV id instead of the local sample index.",
    )
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    try:
        result = run_demo(
            input_path=args.input,
            bv=args.bv,
            url=args.url,
            question=args.question,
            use_llm=not args.disable_llm,
            use_real_bilibili=args.real_bilibili,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(f"[source={result['source']['type']}:{result['source']['identifier']}]")
    print(result["source"]["title"])
    print()
    print(f"[summary_mode={result['summary_mode']}]")
    print(result["summary"])
    print()
    print(f"[tags_mode={result['tags_mode']}]")
    print("标签：" + "、".join(result["tags"]))
    if args.question and "answer" in result:
        print()
        print(f"[answer_mode={result['answer_mode']}]")
        print(result["answer"])
