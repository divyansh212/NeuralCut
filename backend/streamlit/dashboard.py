"""NeuralCut · Streamlit ops dashboard.

A lightweight internal console for monitoring the pipeline without the Next.js
frontend: submit a prompt, watch the live Redis event stream, browse recent
jobs, and preview the rendered MP4. Useful for debugging the worker and the
pub/sub plumbing in isolation.

Run locally:   streamlit run streamlit/dashboard.py
It talks to the same FastAPI backend as the web frontend.
"""

import json
import os
import time

import requests
import streamlit as st

API = os.getenv("NEURALCUT_API_URL", "http://localhost:8000")

st.set_page_config(page_title="NeuralCut Ops", page_icon="🎬", layout="wide")
st.markdown(
    "<h1 style='font-family:Georgia,serif;letter-spacing:3px;'>"
    "<span style='color:#cfd2d8'>NEURAL</span><span style='color:#d8b886'>CUT</span>"
    " <span style='font-size:14px;color:#8a7150'>· OPS CONSOLE</span></h1>",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("Auth")
    token = st.text_input("Supabase access token (JWT)", type="password",
                          help="Copy a logged-in user's access_token. The backend rejects unauthenticated calls.")
    st.caption(f"API: {API}")
    health = None
    try:
        health = requests.get(f"{API}/health", timeout=5).json()
        st.success(f"backend up · mode={health.get('mode')}")
    except Exception as e:
        st.error(f"backend unreachable: {e}")

headers = {"Authorization": f"Bearer {token}"} if token else {}

col_new, col_jobs = st.columns([1, 1])

with col_new:
    st.subheader("New job")
    prompt = st.text_area("Prompt", "a lighthouse waking up at dawn over a stormy sea")
    if st.button("Generate", type="primary", disabled=not token):
        try:
            r = requests.post(f"{API}/jobs", json={"prompt": prompt}, headers=headers, timeout=10)
            r.raise_for_status()
            st.session_state["job_id"] = r.json()["job_id"]
            st.session_state["token"] = token
            st.success(f"Queued {st.session_state['job_id']}")
        except Exception as e:
            st.error(f"submit failed: {e}")

with col_jobs:
    st.subheader("Recent jobs")
    if token and st.button("Refresh"):
        try:
            jobs = requests.get(f"{API}/jobs", headers=headers, timeout=10).json()
            for j in jobs:
                st.write(f"`{j['status']}` · {j['prompt'][:50]} · {j['id'][:8]}")
                if j.get("output_url"):
                    st.video(j["output_url"])
        except Exception as e:
            st.error(f"list failed: {e}")

st.divider()
st.subheader("Live stream")
job_id = st.session_state.get("job_id")
if job_id and token:
    st.caption(f"job:{job_id}")
    box = st.empty()
    events = []
    # EventSource-style read of the SSE endpoint (token via query param)
    try:
        with requests.get(f"{API}/jobs/{job_id}/stream", params={"token": token},
                          stream=True, timeout=120) as resp:
            for raw in resp.iter_lines(decode_unicode=True):
                if not raw or not raw.startswith("data:"):
                    continue
                evt = json.loads(raw[5:].strip())
                events.append(evt)
                box.code("\n".join(
                    f"› {e['stage']} — {e['status']} {json.dumps(e.get('detail') or {})}"
                    for e in events), language="text")
                if evt.get("stage") == "done":
                    url = (evt.get("detail") or {}).get("url")
                    if url:
                        st.success("Render complete")
                        st.video(url)
                    break
                if evt.get("status") == "failed":
                    st.error("Job failed")
                    break
    except Exception as e:
        st.warning(f"stream ended: {e}")
else:
    st.info("Submit a job (with a token) to watch its events here.")
