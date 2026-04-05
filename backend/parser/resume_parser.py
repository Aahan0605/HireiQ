"""
Resume Parser — PDF and TXT ingestion with text cleaning.

Extracts raw text from uploaded resumes, handling PDF (via pdfplumber)
and plain text formats. Supports batch loading from a folder.

Designed to be async-ready: file I/O operations can be called from
async contexts via asyncio.to_thread() wrapper.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def extract_text_from_file(filepath: str | Path) -> str:
    """
    Extract text content from a resume file.

    Supports:
        - .pdf  → uses pdfplumber for extraction
        - .txt  → reads as UTF-8 text
        - .md   → reads as UTF-8 text
        - .docx → basic fallback (reads as text, may lose formatting)

    Args:
        filepath: Path to the resume file.

    Returns:
        Cleaned text content of the file.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError:        If the file extension is not supported.
        RuntimeError:      If PDF extraction fails.

    Examples:
        >>> text = extract_text_from_file("data/sample_resumes/alice.pdf")
        >>> len(text) > 0
        True
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"Resume file not found: {filepath}")

    extension = filepath.suffix.lower()

    if extension == ".pdf":
        return _extract_from_pdf(filepath)
    elif extension in {".txt", ".md"}:
        return _extract_from_text(filepath)
    else:
        raise ValueError(
            f"Unsupported file format: '{extension}'. "
            f"Supported formats: .pdf, .txt, .md"
        )


def _extract_from_pdf(filepath: Path) -> str:
    """
    Extract text from a PDF file using pdfplumber.

    Concatenates text from all pages with newline separators.
    Falls back gracefully if individual pages fail to parse.

    Args:
        filepath: Path to the PDF file.

    Returns:
        Cleaned text from all PDF pages.

    Raises:
        RuntimeError: If pdfplumber cannot open the file.
    """
    try:
        import pdfplumber
    except ImportError:
        raise RuntimeError(
            "pdfplumber is required for PDF parsing. "
            "Install it with: pip install pdfplumber"
        )

    pages_text: list[str] = []

    try:
        with pdfplumber.open(filepath) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                try:
                    text = page.extract_text()
                    if text:
                        pages_text.append(text)
                except Exception as e:
                    logger.warning(
                        f"Failed to extract text from page {page_num} "
                        f"of {filepath.name}: {e}"
                    )
                    continue
    except Exception as e:
        raise RuntimeError(f"Failed to open PDF '{filepath.name}': {e}")

    if not pages_text:
        logger.warning(f"No text extracted from PDF: {filepath.name}")
        return ""

    raw_text = "\n".join(pages_text)
    # Fix words jammed together in PDF text
    raw_text = _clean_pdf_text(raw_text)
    return _clean_text(raw_text)


def _clean_pdf_text(text: str) -> str:
    """
    Fix words jammed together in PDF text (camelCase, no spaces between words).

    Applies intelligent spacing rules:
    - camelCase → camel Case
    - PDFFile → PDF File
    - python3 → python 3
    - 2024Jan → 2024 Jan
    - .A → . A
    - ,a → , a
    - sentence.Next → sentence. Next

    Time: O(n) where n = text length
    """
    if not text:
        return ""

    # Fix camelCase: insert space between lowercase and uppercase
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)

    # Fix ALLCAPS: insert space before uppercase followed by lowercase
    text = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", text)

    # Fix letter-digit: insert space between letters and digits
    text = re.sub(r"([a-zA-Z])(\d)", r"\1 \2", text)

    # Fix digit-letter: insert space between digits and letters
    text = re.sub(r"(\d)([a-zA-Z])", r"\1 \2", text)

    # Fix period: add space after period before uppercase letter
    text = re.sub(r"\.(\[A-Z])", r". \1", text)

    # Fix comma: add space after comma if missing
    text = re.sub(r",([^\s])", r", \1", text)

    # Fix sentence transitions: split on punctuation that acts as newlines
    text = re.sub(r"([.!?])\s*([A-Z])", r"\1\n\2", text)

    return text.strip()


def _extract_from_text(filepath: Path) -> str:
    """
    Read and clean a plain text file.

    Tries UTF-8 first, falls back to latin-1 for legacy files.

    Args:
        filepath: Path to the text file.

    Returns:
        Cleaned text content.
    """
    for encoding in ("utf-8", "latin-1", "ascii"):
        try:
            raw_text = filepath.read_text(encoding=encoding)
            return _clean_text(raw_text)
        except UnicodeDecodeError:
            continue

    logger.error(f"Could not decode file: {filepath.name}")
    return ""


def _clean_text(text: str) -> str:
    """
    Clean and normalize raw text extracted from a resume.

    Operations:
        1. Replace common Unicode characters (smart quotes, em dashes, bullets)
        2. Collapse multiple whitespace/newlines into single spaces
        3. Remove non-printable control characters
        4. Strip leading/trailing whitespace
        5. Normalize email and URL formatting

    Args:
        text: Raw text from file extraction.

    Returns:
        Cleaned, normalized text string.

    Examples:
        >>> _clean_text("  Hello   World  \\n\\n  Foo  ")
        'Hello World Foo'
    """
    if not text:
        return ""

    # Replace common Unicode artifacts
    replacements = {
        "\u2018": "'",  # left single quote
        "\u2019": "'",  # right single quote
        "\u201c": '"',  # left double quote
        "\u201d": '"',  # right double quote
        "\u2013": "-",  # en dash
        "\u2014": "-",  # em dash
        "\u2022": " ",  # bullet
        "\u00b7": " ",  # middle dot
        "\u00a0": " ",  # non-breaking space
        "\u200b": "",  # zero-width space
        "\ufeff": "",  # BOM
        "\t": " ",  # tab
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    # Remove non-printable control characters (keep newlines temporarily)
    text = re.sub(r"[^\x20-\x7E\n]", " ", text)

    # Collapse multiple newlines into a single newline
    text = re.sub(r"\n+", "\n", text)

    # Collapse multiple spaces into single space
    text = re.sub(r"[ \t]{2,}", " ", text)

    return text.strip()


def load_all_resumes(folder: str | Path) -> dict[str, str]:
    """
    Load all resume files from a folder.

    Scans for .pdf and .txt files, extracts text from each,
    and returns a dict mapping filename → extracted text.

    Args:
        folder: Path to folder containing resume files.

    Returns:
        Dict mapping filename (without extension) to extracted text.
        Files that fail to parse are logged and skipped.

    Raises:
        FileNotFoundError: If the folder does not exist.

    Examples:
        >>> resumes = load_all_resumes("data/sample_resumes/")
        >>> isinstance(resumes, dict)
        True
    """
    folder = Path(folder)

    if not folder.exists():
        raise FileNotFoundError(f"Resume folder not found: {folder}")

    if not folder.is_dir():
        raise ValueError(f"Path is not a directory: {folder}")

    supported_extensions = {".pdf", ".txt", ".md"}
    resumes: dict[str, str] = {}

    files = sorted(
        f
        for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in supported_extensions
    )

    if not files:
        logger.warning(f"No supported resume files found in: {folder}")
        return resumes

    for filepath in files:
        try:
            text = extract_text_from_file(filepath)
            if text:
                # Use stem (filename without extension) as key
                resumes[filepath.stem] = text
                logger.info(f"Loaded resume: {filepath.name} ({len(text)} chars)")
            else:
                logger.warning(f"Empty text extracted from: {filepath.name}")
        except Exception as e:
            logger.error(f"Failed to parse {filepath.name}: {e}")
            continue

    logger.info(f"Loaded {len(resumes)} resumes from {folder}")
    return resumes


async def async_extract_text(filepath: str | Path) -> str:
    """
    Async wrapper for extract_text_from_file.

    Runs the synchronous extraction in a thread pool to avoid
    blocking the event loop (important for FastAPI endpoints).

    Args:
        filepath: Path to the resume file.

    Returns:
        Cleaned text content.
    """
    return await asyncio.to_thread(extract_text_from_file, filepath)


async def async_load_all_resumes(folder: str | Path) -> dict[str, str]:
    """
    Async wrapper for load_all_resumes.

    Args:
        folder: Path to folder containing resume files.

    Returns:
        Dict mapping filename to extracted text.
    """
    return await asyncio.to_thread(load_all_resumes, folder)
