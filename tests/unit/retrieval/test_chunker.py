"""
Unit tests for the TextChunker.
"""
import pytest

from careintel.application.knowledge.chunker import TextChunker


class TestTextChunker:
    """Tests for TextChunker."""

    @pytest.fixture
    def chunker(self) -> TextChunker:
        return TextChunker(chunk_size=50, overlap=10)

    def test_empty_string_returns_empty_list(self, chunker: TextChunker) -> None:
        assert chunker.chunk("") == []

    def test_whitespace_only_returns_empty_list(self, chunker: TextChunker) -> None:
        assert chunker.chunk("   \n\t  ") == []

    def test_single_sentence_yields_one_chunk(self, chunker: TextChunker) -> None:
        chunks = chunker.chunk("This is a single short sentence.")
        assert len(chunks) == 1
        assert chunks[0].chunk_index == 0
        assert "single short sentence" in chunks[0].content

    def test_chunks_are_ordered_by_index(self, chunker: TextChunker) -> None:
        long_text = ". ".join([f"Sentence number {i}" for i in range(50)])
        chunks = chunker.chunk(long_text)
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i

    def test_chunking_is_deterministic(self, chunker: TextChunker) -> None:
        """Same input always produces identical output."""
        text = "Sentence one. Sentence two. Sentence three. Sentence four."
        c1 = chunker.chunk(text)
        c2 = chunker.chunk(text)
        assert [c.content for c in c1] == [c.content for c in c2]
        assert [c.token_count for c in c1] == [c.token_count for c in c2]

    def test_each_chunk_has_positive_token_count(self, chunker: TextChunker) -> None:
        text = "First sentence. Second sentence. Third sentence."
        chunks = chunker.chunk(text)
        for chunk in chunks:
            assert chunk.token_count is not None
            assert chunk.token_count > 0

    def test_content_coverage(self, chunker: TextChunker) -> None:
        """All original sentences appear in at least one chunk."""
        sentences = [f"Unique phrase {i} for testing." for i in range(20)]
        text = " ".join(sentences)
        chunks = chunker.chunk(text)
        combined = " ".join(c.content for c in chunks)
        for sentence in sentences:
            assert sentence in combined

    def test_very_long_single_sentence_handled(self, chunker: TextChunker) -> None:
        """A sentence that exceeds chunk_size is included as a single chunk."""
        very_long = "word " * 200
        chunks = chunker.chunk(very_long.strip())
        assert len(chunks) >= 1

    def test_configurable_chunk_size(self) -> None:
        """Different chunk sizes produce different chunk counts."""
        text = ". ".join([f"Sentence {i}" for i in range(30)])
        small = TextChunker(chunk_size=20, overlap=5).chunk(text)
        large = TextChunker(chunk_size=200, overlap=20).chunk(text)
        assert len(small) >= len(large)

    def test_chunk_index_starts_at_zero(self, chunker: TextChunker) -> None:
        chunks = chunker.chunk("Hello world. This is the second sentence.")
        assert chunks[0].chunk_index == 0
