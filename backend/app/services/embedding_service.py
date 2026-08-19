from openai import OpenAI

from app.core.config import settings


class EmbeddingError(Exception):
    """Raised when text embeddings cannot be generated."""


client = OpenAI(
    api_key=settings.openai_api_key.get_secret_value(),
)


def generate_embedding(
    text: str,
) -> list[float]:
    cleaned_text = text.strip()

    if not cleaned_text:
        raise EmbeddingError(
            "Cannot create an embedding for empty text."
        )

    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=cleaned_text,
        )

    except Exception as exc:
        raise EmbeddingError(
            "The text embedding could not be generated."
        ) from exc

    return response.data[0].embedding
