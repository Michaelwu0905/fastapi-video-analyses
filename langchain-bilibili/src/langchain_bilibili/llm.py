from __future__ import annotations

from langchain_core.documents import Document
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from .config import load_settings


def is_llm_configured() -> bool:
    return bool(load_settings().api_key)


def get_chat_model() -> ChatOpenAI | None:
    settings = load_settings()
    if not settings.api_key:
        return None
    return ChatOpenAI(
        api_key=settings.api_key,
        base_url=settings.base_url,
        model=settings.model,
        temperature=0.2,
    )


def render_context(documents: list[Document]) -> str:
    return "\n".join(f"- {doc.page_content}" for doc in documents)


def llm_summarize(documents: list[Document]) -> str:
    model = get_chat_model()
    if model is None:
        raise RuntimeError("Moonshot API key is not configured.")

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content=(
                    "你是一个视频内容分析助手。"
                    "请基于转写片段输出简明中文摘要，"
                    "包含主题和关键点。"
                )
            ),
            (
                "human",
                "请总结以下视频转写内容：\n\n{context}",
            ),
        ]
    )
    response = (prompt | model).invoke({"context": render_context(documents)})
    return response.content if isinstance(response.content, str) else str(response.content)


def llm_answer(question: str, documents: list[Document]) -> str:
    model = get_chat_model()
    if model is None:
        raise RuntimeError("Moonshot API key is not configured.")

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content=(
                    "你是一个视频内容问答助手。"
                    "只能根据提供的转写片段回答。"
                    "如果证据不足，要明确说信息不足。"
                    "回答时直接引用相关内容，不要编造时间点。"
                )
            ),
            (
                "human",
                "问题：{question}\n\n相关片段：\n{context}",
            ),
        ]
    )
    response = (prompt | model).invoke(
        {
            "question": question,
            "context": render_context(documents),
        }
    )
    return response.content if isinstance(response.content, str) else str(response.content)


def llm_extract_tags(documents: list[Document]) -> list[str]:
    model = get_chat_model()
    if model is None:
        raise RuntimeError("Moonshot API key is not configured.")

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content=(
                    "你是一个视频内容标签提取助手。"
                    "请基于转写片段提取 3 到 6 个中文标签。"
                    "只返回 JSON 数组，不要输出额外文字。"
                )
            ),
            ("human", "请提取标签：\n\n{context}"),
        ]
    )
    response = (prompt | model).invoke({"context": render_context(documents)})
    content = response.content if isinstance(response.content, str) else str(response.content)
    return [item.strip() for item in content.strip().strip("[]").replace("\"", "").split(",") if item.strip()]
