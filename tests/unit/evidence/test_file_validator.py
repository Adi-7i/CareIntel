"""
Tests for FileValidator.
"""

import io

import pytest

from careintel.application.evidence.file_validator import FileValidator
from careintel.core.errors import FileTooLargeError, MimeMismatchError, UnsupportedFileTypeError


def test_validate_extension() -> None:
    validator = FileValidator([".pdf", ".txt"], 1024)

    assert validator.validate_extension("document.pdf") == "document.pdf"
    assert validator.validate_extension("path/to/doc.PDF") == "doc.PDF"

    with pytest.raises(UnsupportedFileTypeError):
        validator.validate_extension("image.png")

    with pytest.raises(UnsupportedFileTypeError):
        validator.validate_extension("..")


def test_validate_magic_signature() -> None:
    validator = FileValidator([".pdf"], 1024)

    # Fake PDF magic bytes
    pdf_bytes = b"%PDF-1.4\n"
    assert "pdf" in validator.validate_magic_signature(pdf_bytes).lower()

    # Random bytes
    with pytest.raises(MimeMismatchError):
        validator.validate_magic_signature(b"\x00\x01\x02\x03\x04")


def test_validate_mime_consistency() -> None:
    validator = FileValidator([".pdf"], 1024)

    validator.validate_mime_consistency(
        filename="synthetic.pdf",
        declared_mime="application/pdf",
        detected_mime="application/pdf",
    )

    with pytest.raises(MimeMismatchError):
        validator.validate_mime_consistency(
            filename="synthetic.pdf",
            declared_mime="application/pdf",
            detected_mime="application/x-dosexec",
        )


@pytest.mark.asyncio
async def test_stream_and_validate() -> None:
    validator = FileValidator([".txt"], 15)  # Max 15 bytes

    data = b"Hello, World!"  # 13 bytes
    stream = io.BytesIO(data)

    sha256, magic_mime, size = await validator.stream_and_validate(stream)
    assert size == 13
    assert magic_mime == "text/plain"
    assert len(sha256) == 64

    # Test oversized
    stream2 = io.BytesIO(b"This is way too long for the limit.")
    with pytest.raises(FileTooLargeError):
        await validator.stream_and_validate(stream2)
