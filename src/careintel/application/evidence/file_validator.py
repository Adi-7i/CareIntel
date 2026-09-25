"""
File validator for evidence intake.
"""

import hashlib
import os
from typing import IO

try:
    import magic
except (ImportError, Exception):
    magic = None

from careintel.core.errors import FileTooLargeError, MimeMismatchError, UnsupportedFileTypeError


def _detect_mime_from_bytes(header_bytes: bytes) -> str | None:
    if header_bytes.startswith(b"%PDF-"):
        return "application/pdf"
    if header_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if header_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if header_bytes.startswith(b"RIFF") and len(header_bytes) >= 12 and header_bytes[8:12] == b"WEBP":
        return "image/webp"
    if header_bytes.startswith(b"II*\x00") or header_bytes.startswith(b"MM\x00*"):
        return "image/tiff"
    if header_bytes.startswith(b"RIFF") and len(header_bytes) >= 12 and header_bytes[8:12] == b"WAVE":
        return "audio/wav"
    if header_bytes.startswith(b"ID3") or (len(header_bytes) >= 2 and header_bytes[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2")):
        return "audio/mpeg"
    if len(header_bytes) >= 8 and header_bytes[4:8] == b"ftyp":
        return "audio/mp4"
    if header_bytes.startswith(b"OggS"):
        return "audio/ogg"
    if header_bytes.startswith(b"fLaC"):
        return "audio/flac"
    if b"\x00" in header_bytes:
        return None
    try:
        decoded = header_bytes.decode("utf-8")
        if decoded.isprintable() or any(c in "\r\n\t" for c in decoded):
            return "text/plain"
        return None
    except UnicodeDecodeError:
        return None


class FileValidator:
    """
    Validates uploaded files for Evidence intake.
    """

    def __init__(
        self,
        allowed_extensions: list[str],
        max_size_bytes: int,
    ) -> None:
        self.allowed_extensions = allowed_extensions
        self.max_size_bytes = max_size_bytes

    def validate_extension(self, filename: str) -> str:
        """
        Validate the file extension against the configured allowlist.
        Returns the sanitized filename.
        Raises UnsupportedFileTypeError if invalid.
        """
        if not filename:
            raise UnsupportedFileTypeError("Filename is missing.")

        # Basic path traversal prevention
        basename = os.path.basename(filename).replace("\x00", "")
        if not basename or basename in (".", ".."):
            raise UnsupportedFileTypeError("Invalid filename.")

        _, ext = os.path.splitext(basename)
        if ext.lower() not in self.allowed_extensions:
            raise UnsupportedFileTypeError(f"Extension '{ext}' is not supported.")
        return basename

    def validate_magic_signature(self, header_bytes: bytes) -> str:
        """
        Check the magic bytes to determine the MIME type.
        Raises MimeMismatchError if it cannot be determined.
        """
        mime_type = None
        if magic is not None:
            try:
                mime_type = magic.from_buffer(header_bytes, mime=True)
            except Exception:
                mime_type = None

        if not mime_type or mime_type == "application/octet-stream":
            mime_type = _detect_mime_from_bytes(header_bytes)

        if not mime_type or mime_type == "application/octet-stream":
            raise MimeMismatchError("Could not determine valid MIME type from file signature.")
        return mime_type

    async def stream_and_validate(self, file_stream: IO[bytes]) -> tuple[str, str, int]:
        """
        Stream the file to compute SHA-256 and enforce size limits.
        Since we need the magic bytes to validate the file type, we read the first chunk,
        validate it, and then stream the rest.
        Returns a tuple of (sha256_hex, magic_mime, total_size).
        """
        hasher = hashlib.sha256()
        total_size = 0
        chunk_size = 65536

        # Read first chunk for magic bytes
        first_chunk = file_stream.read(chunk_size)
        if not first_chunk:
            raise UnsupportedFileTypeError("File is empty.")

        magic_mime = self.validate_magic_signature(first_chunk)
        hasher.update(first_chunk)
        total_size += len(first_chunk)

        if total_size > self.max_size_bytes:
            raise FileTooLargeError(
                f"File exceeds maximum allowed size of {self.max_size_bytes} bytes."
            )

        # Stream the rest
        while True:
            chunk = file_stream.read(chunk_size)
            if not chunk:
                break

            total_size += len(chunk)
            if total_size > self.max_size_bytes:
                raise FileTooLargeError(
                    f"File exceeds maximum allowed size of {self.max_size_bytes} bytes."
                )

            hasher.update(chunk)

        file_stream.seek(0)
        return hasher.hexdigest(), magic_mime, total_size
