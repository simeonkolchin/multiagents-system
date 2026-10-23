import io

from pypdf import PdfReader


def extract_text(data: bytes, filename: str, content_type: str) -> str:
    name = filename.lower()
    if content_type == "application/pdf" or name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(data))
        parts = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(parts).strip()
    return data.decode("utf-8", errors="ignore").strip()
