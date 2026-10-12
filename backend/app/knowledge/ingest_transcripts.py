
import re
from pathlib import Path

from sqlalchemy import delete

from app.db.models import TranscriptChunk
from app.db.session import SessionLocal


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TRANSCRIPTS_DIR = PROJECT_ROOT / "data" / "podcasts"

CHUNK_SIZE = 1800
CHUNK_OVERLAP = 250


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extract simple YAML-style metadata without extra dependencies."""
    metadata = {}
    match = re.match(r"\A---\s*\r?\n(.*?)\r?\n---\s*\r?\n?", text, re.DOTALL)

    if not match:
        return metadata, text

    for line in match.group(1).splitlines():
        key, separator, value = line.partition(":")
        if not separator:
            continue

        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]

        metadata[key.strip()] = value

    return metadata, text[match.end():]


def split_text(text: str) -> list[str]:
    """Split transcript text into overlapping, searchable chunks."""
    text = text.replace("\r\n", "\n").strip()
    if not text:
        return []

    paragraphs = re.split(r"\n\s*\n", text)
    chunks = []
    current = ""

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        # Break unusually long paragraphs into smaller pieces.
        while len(paragraph) > CHUNK_SIZE:
            if current:
                chunks.append(current)
                current = ""

            chunks.append(paragraph[:CHUNK_SIZE].strip())
            paragraph = paragraph[CHUNK_SIZE - CHUNK_OVERLAP:].strip()

        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph

        if len(candidate) <= CHUNK_SIZE:
            current = candidate
        else:
            if current:
                chunks.append(current)

            overlap = current[-CHUNK_OVERLAP:] if current else ""
            current = f"{overlap}\n\n{paragraph}".strip()

            if len(current) > CHUNK_SIZE:
                current = current[-CHUNK_SIZE:]

    if current:
        chunks.append(current)

    return chunks


def main() -> None:
    if not TRANSCRIPTS_DIR.is_dir():
        raise FileNotFoundError(
            f"Transcript directory not found: {TRANSCRIPTS_DIR}"
        )

    files = sorted(TRANSCRIPTS_DIR.glob("*.md"))
    if not files:
        raise RuntimeError(f"No Markdown transcripts found in {TRANSCRIPTS_DIR}")

    records = []

    for file_path in files:
        # utf-8-sig handles files that contain a UTF-8 byte-order mark.
        raw_text = file_path.read_text(encoding="utf-8-sig", errors="replace")
        metadata, transcript = parse_frontmatter(raw_text)

        title = metadata.get("title", file_path.stem)
        guest = metadata.get("guest") or None
        episode_date = metadata.get("date") or None

        for index, chunk in enumerate(split_text(transcript)):
            records.append(
                TranscriptChunk(
                    episode_title=title,
                    guest=guest,
                    episode_date=episode_date,
                    source_file=file_path.name,
                    chunk_index=index,
                    content=chunk,
                )
            )

    if not records:
        raise RuntimeError("No transcript chunks were generated.")

    # Replace the indexed dataset in one transaction, avoiding duplicate
    # chunks when the ingestion script is run again.
    with SessionLocal() as db:
        with db.begin():
            db.execute(delete(TranscriptChunk))
            db.add_all(records)

    print(f"Transcript files processed: {len(files)}")
    print(f"Transcript chunks stored: {len(records)}")


if __name__ == "__main__":
    main()
