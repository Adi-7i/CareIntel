"""
Text chunker for knowledge source content.

Splits source text into overlapping fixed-size chunks suitable for
embedding and retrieval.

Design:
- Chunk size and overlap are configurable (not hardcoded product thresholds).
- Chunks are produced deterministically for identical inputs.
- Token counting uses tiktoken when available; falls back to word count.
- Chunk boundaries avoid splitting mid-sentence where possible.
- All tuning parameters are marked as configurable/TBD and injected,
  not hardcoded as approved business rules.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    """A single chunk of text produced by the chunker."""

    chunk_index: int
    content: str
    # Token count estimate (exact if tiktoken, approximate otherwise)
    token_count: int


class TextChunker:
    """
    Splits text into overlapping chunks for knowledge retrieval.

    Parameters are injected and configurable — they are NOT approved
    clinical or product thresholds.

    Args:
        chunk_size:   Target chunk size in tokens (approximate). TBD: configurable.
        overlap:      Number of tokens to overlap between chunks. TBD: configurable.
    """

    def __init__(self, chunk_size: int = 512, overlap: int = 64) -> None:
        self._chunk_size = chunk_size
        self._overlap = overlap
        self._tiktoken_enc = self._load_tiktoken()

    @staticmethod
    def _load_tiktoken() -> object | None:
        """Attempt to load tiktoken encoder; return None if unavailable."""
        try:
            import tiktoken

            return tiktoken.get_encoding("cl100k_base")
        except Exception:
            return None

    def _count_tokens(self, text: str) -> int:
        """Estimate token count. Uses tiktoken if available, else word count."""
        if self._tiktoken_enc is not None:
            enc: object = self._tiktoken_enc
            tokens: list[object] = enc.encode(text)  # type: ignore[attr-defined]
            return len(tokens)
        # Fallback: approximate via word count (1 word ≈ 1.3 tokens for English)
        return max(1, int(len(text.split()) * 1.3))

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences for boundary-aware chunking."""
        # Split on sentence-ending punctuation followed by whitespace
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        return [s for s in sentences if s]

    def chunk(self, text: str) -> list[TextChunk]:
        """
        Split the input text into overlapping chunks.

        Returns:
            Ordered list of TextChunk objects (0-indexed).
            Empty list if text is blank.
        """
        if not text.strip():
            return []

        sentences = self._split_sentences(text)
        if not sentences:
            return []

        chunks: list[TextChunk] = []
        current_sentences: list[str] = []
        current_tokens = 0
        chunk_index = 0

        for sentence in sentences:
            sentence_tokens = self._count_tokens(sentence)

            # If a single sentence exceeds chunk_size, include it alone
            if sentence_tokens > self._chunk_size and not current_sentences:
                chunk_text = sentence
                chunks.append(
                    TextChunk(
                        chunk_index=chunk_index,
                        content=chunk_text,
                        token_count=sentence_tokens,
                    )
                )
                chunk_index += 1
                continue

            if current_tokens + sentence_tokens > self._chunk_size and current_sentences:
                # Emit the current chunk
                chunk_text = " ".join(current_sentences)
                chunks.append(
                    TextChunk(
                        chunk_index=chunk_index,
                        content=chunk_text,
                        token_count=self._count_tokens(chunk_text),
                    )
                )
                chunk_index += 1

                # Retain overlap sentences for the next chunk
                overlap_sentences: list[str] = []
                overlap_tokens = 0
                for s in reversed(current_sentences):
                    s_tok = self._count_tokens(s)
                    if overlap_tokens + s_tok > self._overlap:
                        break
                    overlap_sentences.insert(0, s)
                    overlap_tokens += s_tok

                current_sentences = overlap_sentences
                current_tokens = overlap_tokens

            current_sentences.append(sentence)
            current_tokens += sentence_tokens

        # Emit the final chunk
        if current_sentences:
            chunk_text = " ".join(current_sentences)
            chunks.append(
                TextChunk(
                    chunk_index=chunk_index,
                    content=chunk_text,
                    token_count=self._count_tokens(chunk_text),
                )
            )

        return chunks
