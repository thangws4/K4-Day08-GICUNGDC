"""Chatbot RAG — hỏi đáp về luật giao thông đường bộ Việt Nam."""

import html
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from src.task4_chunking_indexing import EMBEDDING_MODEL, embed_texts, get_collection
from src.task10_generation import (
    LLM_MODEL,
    LLM_PROVIDER,
    TOP_K,
    generate_with_citation,
)


load_dotenv()

st.set_page_config(
    page_title="Chatbot luật giao thông",
    page_icon=":material/traffic:",
    layout="centered",
)

ASSETS_DIR = Path(__file__).parent / "assets"

# Nhãn hiển thị cho từng loại nguồn và từng cách truy xuất.
DOC_TYPE_LABEL = {"legal": "Văn bản luật", "news": "Tin bài"}
DOC_TYPE_MODIFIER = {"legal": "legal", "news": "news"}
# Mỗi retrieval method có thang điểm riêng; ghi rõ tên thang để không so nhầm.
SCORE_LABEL = {
    "hybrid": "RRF",
    "dense": "cosine",
    "bm25": "BM25",
    "pageindex": "rank",
}

SNIPPET_CHARS = 400
SAFE_URL_PREFIXES = ("https://", "http://")

SUGGESTIONS = {
    ":blue[:material/local_bar:] Nồng độ cồn": (
        "Mức phạt vi phạm nồng độ cồn đối với người lái ô tô là bao nhiêu?"
    ),
    ":green[:material/badge:] Giấy phép lái xe": (
        "Sau khi đạt kỳ sát hạch thì bao lâu được cấp giấy phép lái xe?"
    ),
    ":orange[:material/local_shipping:] Kinh doanh vận tải": (
        "Xe ô tô kinh doanh vận tải phải lắp những thiết bị gì?"
    ),
}

REFUSAL_HINT = "không thể xác minh"


@st.cache_data(show_spinner=False)
def load_asset(name: str) -> str:
    """Đọc file CSS/JS trong assets/."""
    return (ASSETS_DIR / name).read_text(encoding="utf-8")


@st.cache_resource(show_spinner="Đang nạp model embedding và mở ChromaDB...")
def warm_up() -> int:
    """Nạp sẵn model và collection để câu hỏi đầu tiên không bị chờ lâu."""
    embed_texts(["khởi động"])
    return get_collection().count()


def safe_url(value: object) -> str:
    """Chỉ chấp nhận URL http(s); chặn javascript: từ metadata."""
    url = str(value or "").strip()
    return url if url.startswith(SAFE_URL_PREFIXES) else ""


def source_card_html(order: int, item: dict) -> str:
    """Dựng thẻ nguồn. Mọi giá trị đến từ corpus nên phải escape trước khi nhúng."""
    metadata = item.get("metadata", {})
    doc_type = str(metadata.get("doc_type", ""))
    method = str(item.get("retrieval_method", ""))

    title = html.escape(str(metadata.get("title") or item.get("id", "")))
    origin = html.escape(str(metadata.get("source", "")))
    chunk_index = html.escape(str(metadata.get("chunk_index", "")))
    doc_label = html.escape(DOC_TYPE_LABEL.get(doc_type, "Khác"))
    modifier = DOC_TYPE_MODIFIER.get(doc_type, "neutral")
    score_label = html.escape(SCORE_LABEL.get(method, "score"))
    score_value = f"{float(item.get('score', 0)):.4f}"

    content = str(item.get("content", ""))
    if content:
        snippet = content[:SNIPPET_CHARS] + ("…" if len(content) > SNIPPET_CHARS else "")
        body = f'<p class="ds-source__snippet">{html.escape(snippet)}</p>'
    else:
        body = '<p class="ds-source__empty">Đoạn này không có nội dung văn bản.</p>'

    url = safe_url(metadata.get("url"))
    link = ""
    if url:
        link = (
            f'<a class="ds-link" href="{html.escape(url, quote=True)}" '
            f'target="_blank" rel="noopener noreferrer">Xem văn bản gốc</a>'
        )

    citation = f"[{order}] {metadata.get('title', '')} — {metadata.get('source', '')}, đoạn {metadata.get('chunk_index', '')}."
    if url:
        citation += f" Nguồn: {url}"

    return f"""
<article class="ds-source" aria-label="Nguồn {order}: {doc_label}">
  <div class="ds-source__meta">
    <span class="ds-badge ds-badge--{modifier}">{doc_label}</span>
    <span class="ds-badge">{html.escape(method)}</span>
    <span class="ds-score">{score_label} {score_value}</span>
  </div>
  <h3 class="ds-source__title">[{order}] {title}</h3>
  <p class="ds-source__origin">{origin} · đoạn {chunk_index}</p>
  {body}
  <div class="ds-source__actions">
    {link}
    <button type="button" class="ds-action"
            data-ds-copy="{html.escape(citation, quote=True)}">Sao chép trích dẫn</button>
  </div>
</article>
"""


def render_sources(sources: list[dict], retrieval_source: str) -> None:
    """Hiển thị các đoạn đã dùng kèm điểm, cách truy xuất và link nguồn gốc."""
    if not sources:
        return

    label = f"Nguồn đã dùng ({len(sources)} đoạn · {retrieval_source})"
    cards = "".join(
        source_card_html(order, item) for order, item in enumerate(sources, 1)
    )
    with st.expander(label, icon=":material/menu_book:"):
        st.html(cards)


# CSS và JS nạp một lần ở đầu script, trước khi có element nào được vẽ.
st.html(f"<style>{load_asset('design-system.css')}</style>")
st.html(
    '<div id="ds-copy-status" role="status" aria-live="polite" class="ds-sr-only"></div>'
    f"<script>{load_asset('citation.js')}</script>",
    unsafe_allow_javascript=True,
)

with st.sidebar:
    st.header("Luật giao thông", icon=":material/traffic:")
    st.caption(
        "Chatbot chỉ trả lời dựa trên văn bản quy phạm pháp luật và tin bài "
        "đã thu thập trong corpus. Ngoài phạm vi đó, bot sẽ từ chối thay vì đoán."
    )

    top_k = st.slider(
        "Số đoạn trích dùng để trả lời",
        min_value=3,
        max_value=10,
        value=TOP_K,
        help="Nhiều đoạn thì bao phủ rộng hơn nhưng context dài và dễ nhiễu hơn.",
    )

    if st.button("Hội thoại mới", icon=":material/refresh:", width="stretch"):
        st.session_state.messages = []
        st.rerun()

    corpus_slot = st.container()

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("Hỏi đáp luật giao thông đường bộ")
st.caption(
    "Mỗi câu trả lời đều kèm các đoạn văn bản đã dùng, điểm số và link tới "
    "nguồn công khai để bạn tự kiểm chứng."
)

chunk_count = warm_up()
with corpus_slot:
    st.caption(f"Corpus: {chunk_count:,} đoạn đã index")
    st.caption(f"Embedding: {EMBEDDING_MODEL}")
    st.caption(f"LLM: {LLM_PROVIDER} · {LLM_MODEL or 'chưa cấu hình'}")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            render_sources(
                message.get("sources", []),
                message.get("retrieval_source", ""),
            )

# Gợi ý chỉ xuất hiện khi chưa có hội thoại nào.
if not st.session_state.messages:
    picked = st.pills(
        "Thử hỏi:",
        list(SUGGESTIONS),
        label_visibility="collapsed",
        key="suggestion",
    )
    if picked:
        st.session_state.pending_query = SUGGESTIONS[picked]
        st.rerun()

typed = st.chat_input("Nhập câu hỏi về luật giao thông...", submit_mode="disable")
query = typed or st.session_state.pop("pending_query", None)

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        result = None
        failure = None

        with st.status(":shimmer[Đang tra cứu văn bản]", type="compact") as status:
            try:
                result = generate_with_citation(query, top_k=top_k)
                found = len(result["sources"])
                status.update(
                    label=f"Đã đọc {found} đoạn · {result['retrieval_source']}",
                    state="complete",
                )
            except Exception as error:  # provider lỗi không được làm sập UI
                failure = error
                status.update(label="Tra cứu thất bại", state="error")

        if failure is not None:
            answer = (
                "Không gọi được mô hình sinh câu trả lời. Kiểm tra lại "
                "`LLM_PROVIDER`, `LLM_MODEL` và API key trong `.env`."
            )
            st.error(answer, icon=":material/error:")
            st.caption(f"Chi tiết: {type(failure).__name__}: {failure}")
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                    "sources": [],
                    "retrieval_source": "none",
                }
            )
        else:
            st.markdown(result["answer"])
            if REFUSAL_HINT in result["answer"].lower() and not result["sources"]:
                st.caption("Câu hỏi nằm ngoài phạm vi corpus nên bot từ chối trả lời.")
            render_sources(result["sources"], result["retrieval_source"])
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": result["answer"],
                    "sources": result["sources"],
                    "retrieval_source": result["retrieval_source"],
                }
            )
