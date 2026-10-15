"""
Page 4 — Retrieval Pipeline
Takes queries from paper structure, embeds them, runs similarity search,
and shows top similar chunks per section.
"""
import streamlit as st, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="Retrieval Pipeline | RAG QPG", page_icon="🔍", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.ph{background:linear-gradient(135deg,#0F766E,#14B8A6);padding:1.4rem 2rem;border-radius:14px;margin-bottom:1.5rem;box-shadow:0 4px 20px rgba(15,118,110,.35);}
.ph h1{color:#fff;font-size:1.7rem;margin:0;font-weight:800;}
.ph p{color:rgba(255,255,255,.78);margin:.3rem 0 0;font-size:.88rem;}
.pipe-box{display:flex;align-items:stretch;gap:0;margin:1rem 0;flex-wrap:nowrap;overflow-x:auto;}
.pnode{flex:1;min-width:130px;background:#12121f;border:1px solid rgba(20,184,166,.25);border-radius:12px;padding:1.1rem .8rem;text-align:center;}
.pnode.done{border-color:rgba(16,185,129,.5);background:rgba(16,185,129,.06);}
.pnode .icon{font-size:1.7rem;}
.pnode .lbl{font-size:.65rem;font-weight:700;color:rgba(232,232,240,.5);text-transform:uppercase;letter-spacing:.05em;margin:.25rem 0 .1rem;}
.pnode .val{font-size:.9rem;font-weight:700;color:#E8E8F0;}
.pnode .sub{font-size:.68rem;color:rgba(232,232,240,.35);margin-top:.1rem;font-family:monospace;}
.arrow{display:flex;align-items:center;padding:0 .4rem;color:rgba(232,232,240,.2);font-size:1.2rem;flex-shrink:0;}
.sec-card{background:#12121f;border:1px solid rgba(20,184,166,.2);border-radius:12px;padding:1.2rem 1.4rem;margin:.8rem 0;}
.sec-title{font-size:.9rem;font-weight:700;color:#E8E8F0;margin-bottom:.6rem;}
.query-box{background:#0c0c1d;border:1px solid rgba(20,184,166,.2);border-radius:8px;padding:.6rem 1rem;font-size:.82rem;color:#5EEAD4;font-family:monospace;margin:.4rem 0 .8rem;}
.emb-row{display:flex;gap:.25rem;flex-wrap:wrap;margin:.3rem 0 .8rem;}
.emb-cell{background:rgba(20,184,166,.12);color:#5EEAD4;border-radius:4px;padding:.12rem .38rem;font-size:.66rem;font-family:monospace;}
.chunk-card{background:#0c0c1d;border-left:3px solid #14B8A6;border-radius:0 8px 8px 0;padding:.7rem 1rem;margin:.35rem 0;}
.chunk-text{font-size:.8rem;color:rgba(232,232,240,.8);line-height:1.55;}
.chunk-meta{font-size:.68rem;color:rgba(232,232,240,.4);margin-top:.3rem;}
.score-badge{float:right;background:rgba(20,184,166,.15);color:#2DD4BF;border:1px solid rgba(20,184,166,.3);border-radius:20px;padding:.1rem .65rem;font-size:.7rem;font-weight:700;}
</style>""", unsafe_allow_html=True)

st.markdown("""<div class="ph"><h1>🔍 Step 4 — Retrieval Pipeline</h1>
<p>Query embeddings → cosine similarity search → top-K relevant chunks per section</p></div>""",
unsafe_allow_html=True)

if not st.session_state.get("indexed"):
    st.warning("⚠️ Complete **Step 1 → Upload** first."); st.stop()

all_secs = st.session_state.get("sections",{"A":[],"B":[]})
from src.generation.generator import flatten_sections

if isinstance(all_secs, list):
    all_secs_flat = flatten_sections({"sections": all_secs})
else:
    all_secs_flat = flatten_sections({
        "sections": [section for part_sections in all_secs.values() for section in part_sections]
    })
if not all_secs_flat:
    st.warning("⚠️ Complete **Step 3 → Paper Structure** first."); st.stop()

from src.config import MIN_SIMILARITY_THRESHOLD, TOP_K_RESULTS
from src.retrieval.retriever import retrieve_for_sections

if "retrieval_results" not in st.session_state:
    st.session_state.retrieval_results = []

edim = st.session_state.get("emb_dim", 384)

# ── Run retrieval ─────────────────────────────────────────────────────────────
col_btn, col_info = st.columns([1,3])
with col_btn:
    run_ret = st.button("🔍 Run Retrieval for All Sections", type="primary",
                         key="run_ret", use_container_width=True)
with col_info:
    top_k = st.slider("Top-K chunks per section", 2, 8, min(TOP_K_RESULTS, 8), key="topk_slider")

if run_ret:
    results = retrieve_for_sections(all_secs_flat, top_k=top_k, min_similarity=MIN_SIMILARITY_THRESHOLD)
    for result in results:
        result["bloom"] = next((s.get("bloom_level", "") for s in all_secs_flat if s.get("name") == result["section"]), "")
        result["co"] = next((s.get("co", "CO1") for s in all_secs_flat if s.get("name") == result["section"]), "CO1")
        result["query_emb"] = list(map(float, result.get("query_embedding", [])))[:20]
    st.session_state.retrieval_results = results
    st.success(f"✅ Retrieved context for {len(results)} sections!")
    st.rerun()

# ── Show results ──────────────────────────────────────────────────────────────
results = st.session_state.retrieval_results
if not results:
    st.info("Click **Run Retrieval** to embed your section queries and fetch similar chunks.")
    st.stop()

# Summary pipeline per section
st.markdown("### 📊 Retrieval Pipeline (per section)")

for r in results:
    part_label = f"Part {r['part']}"
    with st.expander(f"**{r['section']}** — {part_label} · {r.get('bloom','')} · {len(r['chunks'])} chunks retrieved", expanded=True):

        # mini pipeline
        qemb_preview = r.get("query_emb",[])
        emb_cells = "".join(f'<span class="emb-cell">{v:.4f}</span>' for v in qemb_preview[:12])

        st.markdown(f"""<div class="pipe-box">
<div class="pnode done"><div class="icon">💬</div><div class="lbl">Query</div>
<div class="val">{len(r['query'].split())} words</div></div>
<div class="arrow">→</div>
<div class="pnode done"><div class="icon">🔢</div><div class="lbl">Query Embedding</div>
<div class="val">dim {edim}</div></div>
<div class="arrow">→</div>
<div class="pnode done"><div class="icon">🗄️</div><div class="lbl">ChromaDB Search</div>
<div class="val">cosine similarity</div></div>
<div class="arrow">→</div>
<div class="pnode done"><div class="icon">🎯</div><div class="lbl">Top-K Chunks</div>
<div class="val">{len(r['chunks'])} retrieved</div></div>
</div>""", unsafe_allow_html=True)

        # Query text
        st.markdown("**📝 Query sent for embedding:**")
        st.markdown(f'<div class="query-box">"{r["query"]}"</div>', unsafe_allow_html=True)

        # Embedding preview
        if qemb_preview:
            st.markdown(f"**🔢 Query vector** (first 12 of {edim} dims):")
            st.markdown(f'<div class="emb-row">{emb_cells} <span style="color:rgba(232,232,240,.3);font-size:.7rem">…+{edim-12} more</span></div>', unsafe_allow_html=True)

        # Retrieved chunks
        st.markdown(f"**🎯 Top-{len(r['chunks'])} Similar Chunks:**")
        if r.get("error"):
            st.error(r["error"])
        for j, ch in enumerate(r["chunks"]):
            st.markdown(
                f'<div class="chunk-card">'
                f'<span class="score-badge">similarity: {ch["similarity"]:.4f}</span>'
                f'<div class="chunk-text"><strong>#{j+1}</strong> · {ch.get("source","")} · page {ch.get("page", "?")}<br>'
                f'{ch["text"][:350]}…</div></div>',
                unsafe_allow_html=True)

st.markdown("---")
st.success("✅ Retrieval complete! Proceed to **Step 5 → Generation**")
