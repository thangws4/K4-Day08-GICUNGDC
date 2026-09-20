"""
Task 4 — Chunking, embedding và indexing.

Luồng xử lý:
    data/standardized/**/*.md -> Document -> Chunk -> embedding -> ChromaDB

Metadata lấy từ header mà Task 3 ghi ở đầu mỗi file (title, Source URL, Doc
type) chứ không suy ra từ tên file. Nhờ vậy citation ở Task 10 hiển thị đúng
tên văn bản và URL công khai để người đọc kiểm chứng.

ID chunk = "<đường dẫn tương đối>::chunk-<n>" nên ổn định giữa các lần chạy;
upsert theo ID này thì chạy lại pipeline không tạo bản ghi trùng.

Task 5 phải import embed_texts() từ đây để query và corpus dùng chung model.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

# Giải thích lựa chọn tham số trong báo cáo nhóm.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
EMBEDDING_DIM = 1024
EMBEDDING_BATCH_SIZE = 16

COLLECTION_NAME = "rag_documents"

# Chroma không nhận batch upsert quá lớn.
UPSERT_BATCH_SIZE = 500

# Header do Task 3 ghi: "# <title>", "**Source:** <url>", "**Doc type:** legal".
TITLE_PATTERN = re.compile(r"^#\s+(.+)$", re.MULTILINE)
FIELD_PATTERN = re.compile(r"^\*\*(.+?):\*\*\s*(.*)$", re.MULTILINE)
HEADER_SEPARATOR = "\n---\n"

SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

# Văn bản được cắt theo từng điều trước, rồi mới chia nhỏ trong phạm vi điều đó.
# Mỗi chunk được gắn lại tiêu đề điều luật cha vì nếu không, chunk chứa mức phạt
# ("Phạt tiền từ 6.000.000 đồng...") không còn cho biết nó áp cho loại xe nào —
# LLM buộc phải từ chối trả lời dù bằng chứng nằm ngay trong context.
ARTICLE_PATTERN = re.compile(r"^(Điều\s+\d+[a-zđ]?\..*)$", re.MULTILINE)
HEADING_MAX_CHARS = 150
MIN_BODY_CHARS = 200

_model_cache: dict[str, object] = {}


def _sentence_transformer():
    """Nạp model local một lần rồi dùng lại cho mọi lần gọi embed."""
    if EMBEDDING_MODEL not in _model_cache:
        from sentence_transformers import SentenceTransformer

        print(f"Loading embedding model: {EMBEDDING_MODEL}")
        model = SentenceTransformer(EMBEDDING_MODEL)
        # Chunk 500 ký tự chỉ khoảng 250 token; giới hạn seq length để không
        # trả giá cho context window 8192 của bge-m3 khi chạy trên CPU.
        model.max_seq_length = min(model.max_seq_length, 512)
        _model_cache[EMBEDDING_MODEL] = model
    return _model_cache[EMBEDDING_MODEL]


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed danh sách text bằng provider cấu hình trong .env."""
    if not texts:
        return []

    if EMBEDDING_PROVIDER == "sentence_transformers":
        model = _sentence_transformer()
        vectors = model.encode(
            texts,
            batch_size=EMBEDDING_BATCH_SIZE,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > EMBEDDING_BATCH_SIZE,
        )
        return [vector.tolist() for vector in vectors]

    if EMBEDDING_PROVIDER == "openai":
        from openai import OpenAI

        client = OpenAI()
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
        return [item.embedding for item in response.data]

    if EMBEDDING_PROVIDER == "gemini":
        from google import genai

        client = genai.Client()
        response = client.models.embed_content(model=EMBEDDING_MODEL, contents=texts)
        return [list(item.values) for item in response.embeddings]

    raise ValueError(f"EMBEDDING_PROVIDER không hỗ trợ: {EMBEDDING_PROVIDER}")


def get_collection():
    """Mở Chroma collection dùng cosine distance."""
    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def parse_markdown(text: str) -> tuple[dict[str, str], str]:
    """Tách header metadata và phần nội dung của một file Markdown."""
    header, separator, body = text.partition(HEADER_SEPARATOR)
    if not separator:
        return {}, text.strip()

    fields = {key.strip(): value.strip() for key, value in FIELD_PATTERN.findall(header)}
    title = TITLE_PATTERN.search(header)
    if title:
        fields["Title"] = title.group(1).strip()
    return fields, body.strip()


def load_documents() -> list[dict]:
    """Đọc Markdown đã chuẩn hóa và trả về danh sách Document."""
    documents = []

    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        fields, body = parse_markdown(path.read_text(encoding="utf-8"))
        if not body:
            print(f"Bỏ qua (rỗng): {path.name}")
            continue

        relative = path.relative_to(STANDARDIZED_DIR).as_posix()
        # Fallback cho file thêm tay không có header của Task 3.
        doc_type = fields.get("Doc type") or ("legal" if "legal" in path.parts else "news")
        documents.append(
            {
                "id": relative,
                "content": body,
                "metadata": {
                    "source": path.name,
                    "title": fields.get("Title") or path.stem,
                    "doc_type": doc_type,
                    "url": fields.get("Source") or None,
                },
            }
        )

    return documents


def split_by_article(content: str) -> list[tuple[str | None, str]]:
    """Cắt nội dung thành từng điều luật, trả về (tiêu đề điều, nội dung)."""
    matches = list(ARTICLE_PATTERN.finditer(content))
    if not matches:
        return [(None, content)]

    sections: list[tuple[str | None, str]] = []
    if matches[0].start() > 0:
        # Phần trước Điều 1 (căn cứ ban hành, tiêu đề văn bản) không có điều cha.
        sections.append((None, content[: matches[0].start()]))

    for order, match in enumerate(matches):
        end = matches[order + 1].start() if order + 1 < len(matches) else len(content)
        sections.append((match.group(1).strip(), content[match.start() : end]))

    return sections


def article_prefix(heading: str | None) -> str:
    """Tiêu đề điều luật rút gọn để gắn vào đầu chunk."""
    if not heading:
        return ""
    if len(heading) <= HEADING_MAX_CHARS:
        return heading
    return heading[:HEADING_MAX_CHARS].rstrip() + "…"


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Chia Document thành chunks có id và chunk_index."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    def make_splitter(size: int) -> RecursiveCharacterTextSplitter:
        return RecursiveCharacterTextSplitter(
            chunk_size=size,
            chunk_overlap=min(CHUNK_OVERLAP, size // 4),
            separators=SEPARATORS,
            keep_separator=True,
        )

    chunks = []
    for document in documents:
        index = 0
        for heading, section in split_by_article(document["content"]):
            prefix = article_prefix(heading)
            # Trừ chỗ cho tiêu đề để chunk cuối cùng vẫn nằm trong CHUNK_SIZE.
            body_size = max(CHUNK_SIZE - len(prefix) - 1, MIN_BODY_CHARS)

            for piece in make_splitter(body_size).split_text(section):
                text = piece.strip()
                if not text:
                    continue
                if prefix and not text.startswith("Điều "):
                    text = f"{prefix}\n{text}"

                chunks.append(
                    {
                        "id": f"{document['id']}::chunk-{index}",
                        "content": text,
                        "metadata": {**document["metadata"], "chunk_index": index},
                    }
                )
                index += 1

    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Thêm embedding vào từng chunk."""
    vectors = embed_texts([chunk["content"] for chunk in chunks])
    for chunk, vector in zip(chunks, vectors):
        chunk["embedding"] = vector
    return chunks


def to_chroma_metadata(metadata: dict) -> dict:
    """Chroma không nhận giá trị None nên đổi thành chuỗi rỗng."""
    return {key: ("" if value is None else value) for key, value in metadata.items()}


def index_to_vectorstore(chunks: list[dict]) -> None:
    """Upsert chunks vào ChromaDB và dọn chunk không còn nguồn."""
    collection = get_collection()

    for start in range(0, len(chunks), UPSERT_BATCH_SIZE):
        batch = chunks[start : start + UPSERT_BATCH_SIZE]
        collection.upsert(
            ids=[chunk["id"] for chunk in batch],
            documents=[chunk["content"] for chunk in batch],
            embeddings=[chunk["embedding"] for chunk in batch],
            metadatas=[to_chroma_metadata(chunk["metadata"]) for chunk in batch],
        )
        print(f"  Upserted {start + len(batch)}/{len(chunks)}")

    current_ids = {chunk["id"] for chunk in chunks}
    stale = [item_id for item_id in collection.get(include=[])["ids"] if item_id not in current_ids]
    if stale:
        collection.delete(ids=stale)
        print(f"  Đã xoá {len(stale)} chunk không còn nguồn")


def run_pipeline() -> None:
    """Chạy load, chunk, embed và index."""
    documents = load_documents()
    print(f"Documents: {len(documents)}")

    chunks = chunk_documents(documents)
    print(f"Chunks: {len(chunks)} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")

    embedded_chunks = embed_chunks(chunks)
    index_to_vectorstore(embedded_chunks)
    print(f"Indexed {len(embedded_chunks)} chunks -> {CHROMA_DIR}")


if __name__ == "__main__":
    # Console Windows mặc định là cp1252 nên print tiếng Việt sẽ crash.
    if (sys.stdout.encoding or "").lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    run_pipeline()
