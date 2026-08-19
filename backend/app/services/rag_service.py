from typing import TypedDict

from openai import OpenAI

from app.core.config import settings

from collections.abc import Iterator

class ConversationMessage(TypedDict):
    role: str
    content: str


class RAGError(Exception):
    """Raised when a grounded AI answer cannot be generated."""


client = OpenAI(
    api_key=settings.openai_api_key.get_secret_value(),
)


def generate_rag_answer(
    question: str,
    context_chunks: list[str],
    conversation_history: list[ConversationMessage] | None = None,
) -> str:
    """
    Generate an answer grounded in retrieved document chunks.

    Conversation history is used only to understand the current
    question. Factual claims must come from the retrieved context.
    """
    if not context_chunks:
        raise RAGError(
            "No document context was provided."
        )

    context = "\n\n---\n\n".join(
        f"[Source {index}]\n{chunk}"
        for index, chunk in enumerate(
            context_chunks,
            start=1,
        )
    )

    recent_history = conversation_history or []

    input_messages: list[dict[str, str]] = [
        {
            "role": message["role"],
            "content": message["content"],
        }
        for message in recent_history
        if message["role"] in {
            "user",
            "assistant",
        }
    ]

    input_messages.append(
        {
            "role": "user",
            "content": (
                "RETRIEVED DOCUMENT CONTEXT:\n\n"
                f"{context}\n\n"
                "CURRENT QUESTION:\n"
                f"{question}"
            ),
        }
    )

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            instructions=(
                "You are an AI document assistant. "
                "Use the conversation history only to understand "
                "references and follow-up questions. "
                "Answer factual questions using only the retrieved "
                "document context in the latest user message. "
                "Do not treat previous assistant answers as factual "
                "evidence. "
                "If the retrieved context does not contain enough "
                "information, clearly say that the available "
                "documents do not contain enough information. "
                "Do not invent facts. "
                "Give a clear and concise answer."
            ),
            input=input_messages,
        )

    except Exception as exc:
        raise RAGError(
            "The AI answer could not be generated."
        ) from exc

    answer = response.output_text.strip()

    if not answer:
        raise RAGError(
            "The AI returned an empty answer."
        )

    return answer


def stream_rag_answer(
    question: str,
    context_chunks: list[str],
    conversation_history: list[ConversationMessage] | None = None,
) -> Iterator[str]:
    if not context_chunks:
        raise RAGError(
            "No document context was provided."
        )

    context = "\n\n---\n\n".join(
        f"[Source {index}]\n{chunk}"
        for index, chunk in enumerate(
            context_chunks,
            start=1,
        )
    )

    recent_history = conversation_history or []

    input_messages: list[dict[str, str]] = [
        {
            "role": message["role"],
            "content": message["content"],
        }
        for message in recent_history
        if message["role"] in {
            "user",
            "assistant",
        }
    ]

    input_messages.append(
        {
            "role": "user",
            "content": (
                "RETRIEVED DOCUMENT CONTEXT:\n\n"
                f"{context}\n\n"
                "CURRENT QUESTION:\n"
                f"{question}"
            ),
        }
    )

    try:
        with client.responses.stream(
            model="gpt-4.1-mini",
            instructions=(
                "You are an AI document assistant. "
                "Use conversation history only to understand "
                "references and follow-up questions. "
                "Answer factual questions using only the retrieved "
                "document context. "
                "Do not invent facts."
            ),
            input=input_messages,
        ) as stream:
            for event in stream:
                if event.type == "response.output_text.delta":
                    yield event.delta

    except Exception as exc:
        raise RAGError(
            "The AI answer could not be generated."
        ) from exc