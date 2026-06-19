import os
import uuid
import httpx
import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DataResearchRAG",
    page_icon="📊",
    layout="wide",
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _post_feedback(api_url: str, session_id: str, turn_order: int, rating: int) -> None:
    try:
        httpx.post(
            f"{api_url}/feedback",
            json={"session_id": session_id, "turn_order": turn_order, "rating": rating},
            timeout=50,
        )
    except Exception:
        pass


def _render_assistant_meta(meta: dict, turn: int, api_url: str, session_id: str) -> None:
    """Render SQL expander, result table expander, citation expander, and feedback buttons."""
    col1, col2, col3 = st.columns(3)
    with col1:
        with st.expander("🔍 SQL"):
            st.code(meta.get("sql", ""), language="sql")
    with col2:
        with st.expander(f"📋 Result table ({meta.get('row_count', 0)} rows)"):
            if meta.get("table"):
                st.dataframe(meta["table"], use_container_width=True)
            else:
                st.caption("No rows returned.")
    with col3:
        cit = meta.get("citation", {})
        with st.expander("📌 Citation"):
            st.markdown(f"**Source:** {cit.get('source', '—')}")
            st.markdown(f"**Executed:** {cit.get('executed_at', '—')}")
            st.markdown(f"**Rows:** {cit.get('row_count', 0)}")
            st.markdown(f"**Columns:** {', '.join(cit.get('columns', []))}")

    fb_key = f"fb_{turn}"
    given = st.session_state.get(fb_key)
    if given is None:
        fb_col1, fb_col2, _ = st.columns([1, 1, 8])
        with fb_col1:
            if st.button("👍", key=f"up_{turn}"):
                _post_feedback(api_url, session_id, turn, 1)
                st.session_state[fb_key] = 1
                st.rerun()
        with fb_col2:
            if st.button("👎", key=f"dn_{turn}"):
                _post_feedback(api_url, session_id, turn, -1)
                st.session_state[fb_key] = -1
                st.rerun()
    else:
        st.caption("👍 Rated helpful" if given == 1 else "👎 Rated unhelpful")


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📊 DataResearchRAG")
    st.caption("Conversational analytics over Rossmann Store Sales")

    _default_api_url = os.getenv("API_URL", "http://localhost:8000")
    api_url = st.text_input("API URL", value=_default_api_url)

    st.divider()

    if st.button("🔄 New Session", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    if "session_id" not in st.session_state:
        st.session_state["session_id"] = str(uuid.uuid4())
    session_id = st.session_state["session_id"]
    st.caption(f"Session: `{session_id[:8]}…`")

    st.divider()
    st.markdown("**Try asking:**")
    st.markdown("- Top 5 stores by total sales")
    st.markdown("- How does promo affect sales by store type?")
    st.markdown("- Which month has the highest sales?")
    st.markdown("- And break that down by store type")

# ── Session state init ────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "history" not in st.session_state:
    st.session_state["history"] = []
if "turn_index" not in st.session_state:
    st.session_state["turn_index"] = 0

# ── Render existing chat history ──────────────────────────────────────────────
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and "meta" in msg:
            _render_assistant_meta(msg["meta"], msg["turn"], api_url, session_id)

# ── Chat input ────────────────────────────────────────────────────────────────
if prompt := st.chat_input("Ask a question about Rossmann store sales…"):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            try:
                resp = httpx.post(
                    f"{api_url}/ask",
                    json={
                        "question": prompt,
                        "session_id": session_id,
                        "history": st.session_state["history"],
                    },
                    timeout=1200,
                )
                resp.raise_for_status()
                data = resp.json()
            except httpx.ConnectError:
                st.error(f"Cannot reach API at {api_url}. Is `uvicorn app.api:app` running?")
                st.stop()
            except Exception as exc:
                st.error(f"API error: {exc}")
                st.stop()

        answer = data.get("answer", "")
        turn = st.session_state["turn_index"]
        meta = {
            "sql":       data.get("sql", ""),
            "table":     data.get("table", []),
            "row_count": len(data.get("table", [])),
            "citation":  data.get("citation", {}),
        }

        st.markdown(answer)
        _render_assistant_meta(meta, turn, api_url, session_id)

    st.session_state["messages"].append({
        "role": "assistant",
        "content": answer,
        "meta": meta,
        "turn": turn,
    })
    st.session_state["history"] = data.get("history", [])
    st.session_state["turn_index"] = turn + 1
