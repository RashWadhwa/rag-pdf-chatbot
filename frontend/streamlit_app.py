"""
Streamlit frontend for the RAG PDF Chatbot.

Features:
- FastAPI connection status
- Multiple PDF upload
- Uploaded document listing
- Document deletion
- Vector index rebuilding
- Clear-all functionality
- Chat history
- Source citations
- Backend error handling
"""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote

import requests
import streamlit as st
from dotenv import load_dotenv


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

load_dotenv()

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://127.0.0.1:8000",
).rstrip("/")

REQUEST_TIMEOUT = 120
HEALTH_TIMEOUT = 5


# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------

st.set_page_config(
    page_title="RAG PDF Chatbot",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------
# Session state
# ---------------------------------------------------------

def initialize_session_state() -> None:
    """Initialize values that should survive Streamlit reruns."""

    defaults: dict[str, Any] = {
        "messages": [],
        "documents": [],
        "backend_available": False,
        "upload_key": 0,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


initialize_session_state()


# ---------------------------------------------------------
# Backend API client helpers
# ---------------------------------------------------------

def extract_error(response: requests.Response) -> str:
    """Extract a useful error message from a backend response."""

    try:
        payload = response.json()

        detail = payload.get("detail")

        if isinstance(detail, str):
            return detail

        if detail:
            return str(detail)

    except ValueError:
        pass

    if response.text:
        return response.text

    return f"Backend returned HTTP {response.status_code}."


def check_backend_health() -> bool:
    """Check whether the FastAPI backend is available."""

    try:
        response = requests.get(
            f"{BACKEND_URL}/health/",
            timeout=HEALTH_TIMEOUT,
        )

        return response.ok

    except requests.RequestException:
        return False


def fetch_documents() -> list[dict[str, Any]]:
    """Retrieve the uploaded document list from FastAPI."""

    try:
        response = requests.get(
            f"{BACKEND_URL}/documents/",
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        payload = response.json()

        return payload.get("documents", [])

    except requests.RequestException as exc:
        st.error(f"Unable to load documents: {exc}")
        return []


def upload_document(
    uploaded_file: Any,
) -> dict[str, Any]:
    """Upload one Streamlit file object to FastAPI."""

    files = {
        "file": (
            uploaded_file.name,
            uploaded_file.getvalue(),
            "application/pdf",
        )
    }

    response = requests.post(
        f"{BACKEND_URL}/upload/",
        files=files,
        timeout=REQUEST_TIMEOUT,
    )

    if not response.ok:
        raise RuntimeError(extract_error(response))

    return response.json()


def delete_document(filename: str) -> dict[str, Any]:
    """Delete one document through the backend."""

    encoded_filename = quote(filename, safe="")

    response = requests.delete(
        f"{BACKEND_URL}/documents/{encoded_filename}",
        timeout=REQUEST_TIMEOUT,
    )

    if not response.ok:
        raise RuntimeError(extract_error(response))

    return response.json()


def rebuild_index() -> dict[str, Any]:
    """Request a complete vector-index rebuild."""

    response = requests.post(
        f"{BACKEND_URL}/documents/rebuild",
        timeout=REQUEST_TIMEOUT,
    )

    if not response.ok:
        raise RuntimeError(extract_error(response))

    return response.json()


def clear_all_documents() -> dict[str, Any]:
    """Delete all PDFs and clear the vector index."""

    response = requests.delete(
        f"{BACKEND_URL}/documents/",
        timeout=REQUEST_TIMEOUT,
    )

    if not response.ok:
        raise RuntimeError(extract_error(response))

    return response.json()


def ask_backend(question: str) -> dict[str, Any]:
    """Send a RAG question to FastAPI."""

    response = requests.post(
        f"{BACKEND_URL}/query/",
        json={"question": question},
        timeout=REQUEST_TIMEOUT,
    )

    if not response.ok:
        raise RuntimeError(extract_error(response))

    return response.json()


# ---------------------------------------------------------
# Display helpers
# ---------------------------------------------------------

def format_file_size(size_bytes: int) -> str:
    """Convert bytes into a readable file size."""

    size = float(size_bytes)

    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"

        size /= 1024

    return f"{size:.1f} TB"


def render_sources(
    sources: list[dict[str, Any]],
) -> None:
    """Render retrieved source citations."""

    if not sources:
        return

    with st.expander(
        f"Sources used ({len(sources)})",
        expanded=False,
    ):
        for index, source in enumerate(sources, start=1):
            filename = source.get("source", "Unknown document")
            page = source.get("page")
            chunk_id = source.get("chunk_id")

            citation_parts = [f"**{index}. {filename}**"]

            if page is not None:
                citation_parts.append(f"Page {page}")

            if chunk_id is not None:
                citation_parts.append(f"Chunk {chunk_id}")

            st.markdown(" — ".join(citation_parts))


def render_chat_history() -> None:
    """Display all existing chat messages."""

    for message in st.session_state.messages:
        role = message.get("role", "assistant")
        content = message.get("content", "")
        sources = message.get("sources", [])

        with st.chat_message(role):
            st.markdown(content)

            if role == "assistant":
                render_sources(sources)

# Backend status
st.session_state.backend_available = check_backend_health()

# Sidebar
with st.sidebar:
    st.title("📚 Document Library")

    st.caption(f"Backend: `{BACKEND_URL}`")

    if st.session_state.backend_available:
        st.success("Backend connected")
    else:
        st.error("Backend unavailable")
        st.caption(
            "Start FastAPI with:\n\n"
            "`uvicorn backend.app:app --reload`"
        )

    st.divider()

    # Multiple PDF uploader

    st.subheader("Upload PDFs")

    uploaded_files = st.file_uploader(
        "Choose one or more PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        key=f"pdf_uploader_{st.session_state.upload_key}",
        disabled=not st.session_state.backend_available,
    )

    if st.button(
        "Process selected PDFs",
        type="primary",
        use_container_width=True,
        disabled=(
            not st.session_state.backend_available
            or not uploaded_files
        ),
    ):
        successful_uploads = 0

        progress_bar = st.progress(0)
        status_placeholder = st.empty()

        for index, uploaded_file in enumerate(uploaded_files):
            status_placeholder.info(
                f"Processing {uploaded_file.name}..."
            )

            try:
                result = upload_document(uploaded_file)

                successful_uploads += 1

                st.success(
                    f"{result['filename']}: "
                    f"{result['pages']} pages, "
                    f"{result['chunks']} chunks"
                )

            except requests.RequestException as exc:
                st.error(
                    f"{uploaded_file.name}: connection error — {exc}"
                )

            except RuntimeError as exc:
                st.error(f"{uploaded_file.name}: {exc}")

            progress_bar.progress(
                (index + 1) / len(uploaded_files)
            )

        status_placeholder.empty()

        if successful_uploads:
            st.session_state.documents = fetch_documents()
            st.session_state.upload_key += 1

            st.toast(
                f"{successful_uploads} PDF(s) indexed successfully."
            )

            st.rerun()

    st.divider()

    # Document listing
    document_header, refresh_column = st.columns(
        [4, 1],
        vertical_alignment="center",
    )

    with document_header:
        st.subheader("Indexed documents")

    with refresh_column:
        if st.button(
            "↻",
            help="Refresh document list",
            disabled=not st.session_state.backend_available,
        ):
            st.session_state.documents = fetch_documents()
            st.rerun()

    if (
        st.session_state.backend_available
        and not st.session_state.documents
    ):
        st.session_state.documents = fetch_documents()

    documents = st.session_state.documents

    if not documents:
        st.info("No PDFs have been uploaded yet.")

    for document in documents:
        filename = document.get("filename", "Unknown")
        size = document.get("size", 0)

        with st.container(border=True):
            st.markdown(f"**📄 {filename}**")
            st.caption(format_file_size(size))

            if st.button(
                "Delete",
                key=f"delete_{filename}",
                use_container_width=True,
            ):
                try:
                    with st.spinner(
                        f"Deleting {filename} and rebuilding index..."
                    ):
                        result = delete_document(filename)

                    st.session_state.documents = fetch_documents()

                    st.success(result["message"])
                    st.rerun()

                except requests.RequestException as exc:
                    st.error(f"Connection error: {exc}")

                except RuntimeError as exc:
                    st.error(str(exc))

    st.divider()

    # Knowledge-base controls
    st.subheader("Knowledge base")

    if st.button(
        "Rebuild vector index",
        use_container_width=True,
        disabled=(
            not st.session_state.backend_available
            or not documents
        ),
    ):
        try:
            with st.spinner("Rebuilding the FAISS index..."):
                result = rebuild_index()

            st.success(
                f"Indexed {result['documents']} document(s), "
                f"{result['pages']} page(s), and "
                f"{result['chunks']} chunk(s)."
            )

        except requests.RequestException as exc:
            st.error(f"Connection error: {exc}")

        except RuntimeError as exc:
            st.error(str(exc))

    with st.expander("Danger zone"):
        st.warning(
            "This removes every uploaded PDF and clears the "
            "entire FAISS index."
        )

        confirm_clear = st.checkbox(
            "I understand that this cannot be undone.",
            key="confirm_clear_documents",
        )

        if st.button(
            "Clear all documents",
            type="secondary",
            use_container_width=True,
            disabled=(
                not confirm_clear
                or not st.session_state.backend_available
            ),
        ):
            try:
                with st.spinner(
                    "Clearing documents and vector data..."
                ):
                    result = clear_all_documents()

                st.session_state.documents = []
                st.session_state.messages = []

                st.success(
                    f"Removed "
                    f"{result['deleted_documents']} document(s)."
                )

                st.rerun()

            except requests.RequestException as exc:
                st.error(f"Connection error: {exc}")

            except RuntimeError as exc:
                st.error(str(exc))

# Main application
st.title("💬 RAG PDF Chatbot")

st.markdown(
    "Upload PDF documents in the sidebar, then ask questions "
    "about their contents."
)

if not st.session_state.backend_available:
    st.warning(
        "The FastAPI backend is not available. Start the backend "
        "before using the chatbot."
    )

elif not st.session_state.documents:
    st.info(
        "Upload at least one PDF from the sidebar to begin."
    )

# Chat controls
chat_title_column, clear_chat_column = st.columns(
    [5, 1],
    vertical_alignment="center",
)

with chat_title_column:
    st.subheader("Conversation")

with clear_chat_column:
    if st.button(
        "Clear chat",
        use_container_width=True,
        disabled=not st.session_state.messages,
    ):
        st.session_state.messages = []
        st.rerun()

# Existing messages
render_chat_history()

# Chat input
question = st.chat_input(
    "Ask a question about your uploaded PDFs...",
    disabled=(
        not st.session_state.backend_available
        or not st.session_state.documents
    ),
)

if question:
    cleaned_question = question.strip()

    if cleaned_question:
        user_message = {
            "role": "user",
            "content": cleaned_question,
        }

        st.session_state.messages.append(user_message)

        with st.chat_message("user"):
            st.markdown(cleaned_question)

        with st.chat_message("assistant"):
            with st.spinner("Searching your documents..."):
                try:
                    result = ask_backend(cleaned_question)

                    answer = result.get(
                        "answer",
                        "No answer was returned.",
                    )

                    sources = result.get("sources", [])

                    st.markdown(answer)
                    render_sources(sources)

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": answer,
                            "sources": sources,
                        }
                    )

                except requests.Timeout:
                    error_message = (
                        "The request timed out. The document may be "
                        "large, or the model may still be processing."
                    )

                    st.error(error_message)

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": error_message,
                            "sources": [],
                        }
                    )

                except requests.ConnectionError:
                    error_message = (
                        "The frontend could not connect to the "
                        "FastAPI backend."
                    )

                    st.error(error_message)

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": error_message,
                            "sources": [],
                        }
                    )

                except RuntimeError as exc:
                    error_message = str(exc)

                    st.error(error_message)

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": error_message,
                            "sources": [],
                        }
                    )

                except requests.RequestException as exc:
                    error_message = (
                        f"An unexpected network error occurred: {exc}"
                    )

                    st.error(error_message)

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": error_message,
                            "sources": [],
                        }
                    )

                    
