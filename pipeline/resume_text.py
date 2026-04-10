"""
resume_text.py — Deterministic resume text extraction and keyword helpers.
"""

from __future__ import annotations

import io
import re
import zipfile
from collections import Counter

from pypdf import PdfReader


_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "into",
    "is", "it", "of", "on", "or", "that", "the", "their", "to", "with", "using",
    "used", "use", "over", "across", "within", "your", "you", "will", "this",
    "have", "has", "had", "was", "were", "led", "built", "managed", "developed",
    "worked", "work", "experience", "responsible", "including", "other", "than",
}

_PROMPT_INJECTION_PATTERNS = [
    r"ignore (all|any|the) (previous|prior) instructions?",
    r"system prompt",
    r"developer message",
    r"assistant message",
    r"you are chatgpt",
    r"you are claude",
    r"respond only with",
    r"output only",
    r"<system>",
    r"</system>",
]


def extract_resume_text(file_bytes: bytes, file_name: str = "") -> str:
    lower_name = file_name.lower()

    if lower_name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()

    if lower_name.endswith(".docx"):
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as archive:
                xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
            text = re.sub(r"</w:p>", "\n", xml)
            text = re.sub(r"<[^>]+>", " ", text)
            return re.sub(r"\s+", " ", text).strip()
        except Exception:
            return file_bytes.decode("utf-8", errors="ignore").strip()

    return file_bytes.decode("utf-8", errors="ignore").strip()


def extract_resume_keywords(text: str, limit: int = 40) -> list[str]:
    normalized = text.lower()
    normalized = normalized.replace("next.js", "nextjs").replace("node.js", "nodejs")

    tokens = re.findall(r"[a-z0-9+#.]{2,}", normalized)
    words = [token for token in tokens if token not in _STOPWORDS and not token.isdigit()]

    phrases: list[str] = []
    for size in (1, 2, 3):
        for idx in range(len(words) - size + 1):
            phrase = " ".join(words[idx : idx + size]).strip()
            if phrase and not all(part in _STOPWORDS for part in phrase.split()):
                phrases.append(phrase)

    counts = Counter(phrases)
    ranked = [
        phrase
        for phrase, count in counts.most_common()
        if count > 1 or len(phrase.split()) > 1
    ]
    return ranked[:limit]


def sanitize_untrusted_job_text(text: str, max_chars: int = 4000) -> str:
    cleaned_lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        lowered = line.lower()
        if any(re.search(pattern, lowered) for pattern in _PROMPT_INJECTION_PATTERNS):
            continue
        cleaned_lines.append(raw_line)

    cleaned = "\n".join(cleaned_lines)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:max_chars]
