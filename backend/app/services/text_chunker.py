from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    chunk_index: int
    content: str
    character_count: int
    start_character: int
    end_character: int


class TextChunkingError(Exception):
    """Raised when document text cannot be chunked."""


def find_chunk_end(
    text: str,
    start: int,
    maximum_end: int,
) -> int:
    """
    Prefer ending a chunk at a paragraph, sentence, or space boundary.
    """
    if maximum_end >= len(text):
        return len(text)

    minimum_boundary = start + int(
        (maximum_end - start) * 0.6
    )

    boundary_options = [
        text.rfind("\n\n", minimum_boundary, maximum_end),
        text.rfind(". ", minimum_boundary, maximum_end),
        text.rfind("? ", minimum_boundary, maximum_end),
        text.rfind("! ", minimum_boundary, maximum_end),
        text.rfind(" ", minimum_boundary, maximum_end),
    ]

    best_boundary = max(boundary_options)

    if best_boundary == -1:
        return maximum_end

    return best_boundary + 1


def split_text_into_chunks(
    text: str,
    chunk_size: int = 1200,
    chunk_overlap: int = 200,
) -> list[TextChunk]:
    """
    Split text into overlapping chunks.

    chunk_size:
        Maximum approximate number of characters in each chunk.

    chunk_overlap:
        Number of characters repeated between consecutive chunks.
    """
    cleaned_text = text.strip()

    if not cleaned_text:
        raise TextChunkingError(
            "The document does not contain text to chunk."
        )

    if chunk_size <= 0:
        raise TextChunkingError(
            "Chunk size must be greater than zero."
        )

    if chunk_overlap < 0:
        raise TextChunkingError(
            "Chunk overlap cannot be negative."
        )

    if chunk_overlap >= chunk_size:
        raise TextChunkingError(
            "Chunk overlap must be smaller than chunk size."
        )

    chunks: list[TextChunk] = []
    start = 0
    chunk_index = 0

    while start < len(cleaned_text):
        maximum_end = min(
            start + chunk_size,
            len(cleaned_text),
        )

        end = find_chunk_end(
            text=cleaned_text,
            start=start,
            maximum_end=maximum_end,
        )

        chunk_content = cleaned_text[start:end].strip()

        if chunk_content:
            chunks.append(
                TextChunk(
                    chunk_index=chunk_index,
                    content=chunk_content,
                    character_count=len(chunk_content),
                    start_character=start,
                    end_character=end,
                )
            )

            chunk_index += 1

        if end >= len(cleaned_text):
            break

        next_start = end - chunk_overlap

        # Prevent an infinite loop if a boundary creates no progress.
        if next_start <= start:
            next_start = end

        start = next_start

    if not chunks:
        raise TextChunkingError(
            "No document chunks could be created."
        )

    return chunks