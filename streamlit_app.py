"""Inventory & Sales assistant — a simple chat interface.

A minimal Streamlit chat over the RAG pipeline in the `rag/` package:
title, suggestion chips on first load, streamed answers, that's it.

Run with:  streamlit run streamlit_app.py
"""

import streamlit as st

from rag.config import DATA_FILE_PATH, ConfigError
from rag.pipeline import Pipeline, ask_assistant, build_pipeline, stream_answer

st.set_page_config(
    page_title="ACME Sales Bot",
    page_icon="📦",
    layout="centered",
)

# ---------------------------------------------------------------------------
# Session state (initialized in one clear place)
# ---------------------------------------------------------------------------
st.session_state.setdefault("messages", [])

ASSISTANT_AVATAR = ":material/inventory_2:"

SUGGESTIONS = {
    ":blue[:material/help:] Returns": (
        "How many days do I have to return an item, and what about "
        "opened electronics?"
    ),
    ":green[:material/sell:] Bulk discounts": (
        "How many units do I need to order to get a bulk discount?"
    ),
    ":orange[:material/local_shipping:] Late delivery": (
        "My order arrived late — can I get a refund on the whole order?"
    ),
    ":violet[:material/handyman:] Warranty": (
        "My laptop stopped working after 8 months — is it still covered?"
    ),
}

WELCOME = (
    "Ask me anything about **returns, bulk discounts, supplier terms, "
    "shipping, warranties, or gift cards** — answers come straight from "
    "the store's policy documents."
)


def new_chat() -> None:
    st.session_state.messages = []


# ---------------------------------------------------------------------------
# Pipeline (built once per server process, rebuilt automatically if
# `data/policies.txt` changes — the file hash is part of the cache key)
# ---------------------------------------------------------------------------
def policies_file_hash() -> str:
    """Cheap fingerprint of the policy file, used as the cache key."""
    return f"{DATA_FILE_PATH.stat().st_mtime_ns}-{DATA_FILE_PATH.stat().st_size}"


@st.cache_resource(max_entries=2)
def get_pipeline(file_hash: str) -> Pipeline:
    return build_pipeline()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
head_left, head_right = st.columns([0.85, 0.15], vertical_alignment="center")
head_left.markdown("## :material/inventory_2: Inventory assistant")
head_right.button("New chat", on_click=new_chat)

try:
    with st.spinner("Waking the assistant…"):
        pipeline = get_pipeline(policies_file_hash())
except ConfigError as e:
    st.error(str(e), title="Missing API keys", icon=":material/key_off:")
    st.stop()
except Exception as e:
    st.error(
        f"{e.__class__.__name__}: {e}",
        title="Could not start the assistant",
        icon=":material/error:",
    )
    st.stop()


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------
def render_message(message: dict) -> None:
    """Replay one chat message from history."""
    avatar = ASSISTANT_AVATAR if message["role"] == "assistant" else None
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])


def generate_reply(pipeline: Pipeline, question: str, history: list[dict]) -> str:
    """Stream the answer, with a tiny 'searching' indicator while it works."""
    box = st.empty()
    parts: list[str] = []

    with st.status(":shimmer[Searching policies…]", type="compact") as status:
        for piece in stream_answer(pipeline, question, history):
            parts.append(piece)
            box.markdown("".join(parts))
        answer = "".join(parts)
        status.update(label="Searched the policies", state="complete")

    if not answer:
        # Streaming yielded nothing for this model — fall back to one-shot.
        answer = ask_assistant(pipeline, question, history)
        box.markdown(answer)

    return answer


prompt = st.chat_input(
    "Ask about returns, bulk discounts, suppliers, shipping…",
    submit_mode="disable",
)

if not st.session_state.messages:
    suggestions = st.container()
    suggestions.markdown(WELCOME)
    selected = suggestions.pills(
        "Try asking:", list(SUGGESTIONS), label_visibility="collapsed"
    )
    if selected:
        prompt = SUGGESTIONS[selected]
    if prompt:
        suggestions.empty()

for message in st.session_state.messages:
    render_message(message)

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
        history = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages[:-1]
        ]
        try:
            answer = generate_reply(pipeline, prompt, history)
        except Exception as e:
            st.error(
                f"The assistant hit a problem: {e.__class__.__name__}: {e}",
                title="Something went wrong",
                icon=":material/error:",
            )
            answer = None

    if answer:
        st.session_state.messages.append(
            {"role": "assistant", "content": answer}
        )
