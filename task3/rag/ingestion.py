"""RAG Ingestion Pipeline: chunking, embedding, and vector store persistence."""

import os
import json
import uuid
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

import numpy as np


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class Chunk:
    """A chunk of text from a document with metadata."""
    chunk_id: str
    document_id: str
    title: str
    text: str
    chunk_index: int
    start_char: int
    end_char: int
    metadata: Dict[str, str] = field(default_factory=dict)
    embedding: Optional[np.ndarray] = None


# ============================================================================
# Chunking Strategy
# ============================================================================
#
# We use a chunk size of ~500 tokens with 100-token overlap.
#
# Rationale:
# - 500 tokens is large enough to capture self-contained facts but small
#   enough that a single chunk rarely covers more than 2-3 distinct topics.
# - 100-token overlap preserves context across chunk boundaries, reducing
#   the chance that a critical fact gets split.
# - We approximate tokens as words/1.3 (rough heuristic for English prose).
# - Chunks respect paragraph boundaries when possible; we split on
#   double-newlines first, then on sentence boundaries if a paragraph
#   exceeds 500 tokens.
#
# Alternative tried: 300 tokens with 50 overlap gave higher recall on
# keyword queries but fragmented multi-sentence policy explanations.
# 800 tokens with 200 overlap kept more context but diluted retrieval
# precision on short targeted queries. 500/100 is the sweet spot for
# this corpus (policies + technical docs).
# ============================================================================

APPROX_TOKENS_PER_WORD = 1.3

CHUNK_SIZE_TOKENS = 500
CHUNK_OVERLAP_TOKENS = 100

CHUNK_SIZE_WORDS = int(CHUNK_SIZE_TOKENS / APPROX_TOKENS_PER_WORD)
CHUNK_OVERLAP_WORDS = int(CHUNK_OVERLAP_TOKENS / APPROX_TOKENS_PER_WORD)


def _split_into_sentences(text: str) -> List[str]:
    """Split text into sentences using a simple regex."""
    return re.split(r'(?<=[.!?])\s+', text)


def _split_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs on blank lines."""
    parts = re.split(r'\n\s*\n', text)
    return [p.strip() for p in parts if p.strip()]


def _word_count(text: str) -> int:
    return len(text.split())


def extract_metadata(content: str) -> Tuple[str, Dict[str, str]]:
    """Extract Document ID and Min Role from markdown frontmatter-ish headers.

    Returns (cleaned_content, metadata_dict).
    """
    meta: Dict[str, str] = {}
    lines = content.split("\n")
    cleaned_lines = []
    for line in lines:
        if line.startswith("## Document ID:"):
            meta["document_id"] = line.split(":", 1)[1].strip()
            continue
        if line.startswith("## Min Role:"):
            meta["min_role"] = line.split(":", 1)[1].strip().lower()
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines), meta


def chunk_document(raw_text: str, doc_path: str) -> List[Chunk]:
    """Chunk a document into overlapping Chunk objects.

    Strategy:
    1. Extract metadata headers (Document ID, Min Role).
    2. Split into paragraphs.
    3. For each paragraph, if it fits in CHUNK_SIZE_WORDS, keep as one chunk.
       Otherwise split into sentences and build sliding-window chunks.
    4. Overlap by CHUNK_OVERLAP_WORDS words between consecutive chunks.
    """
    cleaned_text, meta = extract_metadata(raw_text)

    # Derive document_id from metadata or file path
    doc_id = meta.get("document_id", os.path.splitext(os.path.basename(doc_path))[0])

    # Extract title from first # heading
    title = os.path.splitext(os.path.basename(doc_path))[0].replace("_", " ").title()
    for line in cleaned_text.split("\n"):
        if line.startswith("# ") and not line.startswith("## "):
            title = line[2:].strip()
            break

    paragraphs = _split_paragraphs(cleaned_text)
    chunks: List[Chunk] = []
    chunk_idx = 0
    char_offset = 0

    for para in paragraphs:
        words = para.split()
        if len(words) == 0:
            # Recalculate offset for empty paragraphs
            char_offset = raw_text.find(para, char_offset) + len(para)
            continue

        if len(words) <= CHUNK_SIZE_WORDS:
            # Paragraph fits in one chunk
            start_char = raw_text.find(para, char_offset)
            if start_char == -1:
                start_char = char_offset
            end_char = start_char + len(para)
            chunk = Chunk(
                chunk_id=f"{doc_id}_chunk{chunk_idx:03d}",
                document_id=doc_id,
                title=title,
                text=para,
                chunk_index=chunk_idx,
                start_char=start_char,
                end_char=end_char,
                metadata=dict(meta),
            )
            chunks.append(chunk)
            chunk_idx += 1
            char_offset = end_char
        else:
            # Paragraph too large; split into sentence sliding windows
            sentences = _split_into_sentences(para)
            window: List[str] = []
            window_word_count = 0

            for sent in sentences:
                sent_words = _word_count(sent)
                if window_word_count + sent_words > CHUNK_SIZE_WORDS and window:
                    # Flush current window as a chunk
                    chunk_text = " ".join(window)
                    start_char = raw_text.find(chunk_text, char_offset)
                    if start_char == -1:
                        start_char = char_offset
                    end_char = start_char + len(chunk_text)
                    chunk = Chunk(
                        chunk_id=f"{doc_id}_chunk{chunk_idx:03d}",
                        document_id=doc_id,
                        title=title,
                        text=chunk_text,
                        chunk_index=chunk_idx,
                        start_char=start_char,
                        end_char=end_char,
                        metadata=dict(meta),
                    )
                    chunks.append(chunk)
                    chunk_idx += 1

                    # Create overlap: keep last ~overlap_words worth
                    overlap_text = " ".join(window)
                    overlap_words_split = overlap_text.split()
                    keep_count = min(CHUNK_OVERLAP_WORDS, len(overlap_words_split))
                    window = overlap_words_split[-keep_count:]
                    window_word_count = _word_count(" ".join(window))

                window.append(sent)
                window_word_count += sent_words

            # Flush remaining window
            if window:
                chunk_text = " ".join(window)
                start_char = raw_text.find(chunk_text, char_offset)
                if start_char == -1:
                    start_char = char_offset
                end_char = start_char + len(chunk_text)
                chunk = Chunk(
                    chunk_id=f"{doc_id}_chunk{chunk_idx:03d}",
                    document_id=doc_id,
                    title=title,
                    text=chunk_text,
                    chunk_index=chunk_idx,
                    start_char=start_char,
                    end_char=end_char,
                    metadata=dict(meta),
                )
                chunks.append(chunk)
                chunk_idx += 1

    return chunks


def load_corpus(corpus_dir: str) -> List[Tuple[str, str]]:
    """Load all .md files from the corpus directory recursively.

    Returns list of (file_path, raw_content) tuples.
    """
    documents = []
    for root, _, files in os.walk(corpus_dir):
        for fname in sorted(files):
            if fname.endswith(".md"):
                full_path = os.path.join(root, fname)
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                documents.append((full_path, content))
    return documents


def ingest_corpus(corpus_dir: str) -> Dict[str, List[Chunk]]:
    """Ingest all documents: load -> chunk -> return index.

    Returns dict mapping document_id -> list of Chunks.
    """
    docs = load_corpus(corpus_dir)
    all_chunks: Dict[str, List[Chunk]] = {}

    for path, content in docs:
        chunks = chunk_document(content, path)
        if chunks:
            doc_id = chunks[0].document_id
            if doc_id in all_chunks:
                # Append to existing; for corpus with same doc_id
                all_chunks[doc_id].extend(chunks)
            else:
                all_chunks[doc_id] = chunks

    return all_chunks


def print_chunk_stats(chunks_by_doc: Dict[str, List[Chunk]]):
    """Print statistics about chunking."""
    total_chunks = sum(len(v) for v in chunks_by_doc.values())
    total_chars = sum(c.end_char - c.start_char for chunks in chunks_by_doc.values() for c in chunks)
    avg_chars = total_chars / total_chunks if total_chunks else 0
    print(f"Ingestion complete:")
    print(f"  Documents: {len(chunks_by_doc)}")
    print(f"  Total chunks: {total_chunks}")
    print(f"  Average chunk length: {avg_chars:.0f} chars (~{avg_chars / 4:.0f} tokens)")
    print(f"  Chunk size target: {CHUNK_SIZE_TOKENS} tokens")
    print(f"  Chunk overlap: {CHUNK_OVERLAP_TOKENS} tokens")


if __name__ == "__main__":
    chunks = ingest_corpus("corpus")
    print_chunk_stats(chunks)