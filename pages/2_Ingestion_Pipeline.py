"""
Page 2 — Ingestion Pipeline
Shows the full RAG data ingestion pipeline with live metrics:
Documents → Pages → Chunks → Embeddings → Vector DB
"""
import streamlit as st, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="Ingestion Pipeline | RAG QPG", page_icon="🔬", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.ph{background:linear-gradient(135deg,#0F4C75,#1B6CA8);padding:1.4rem 2rem;border-radius:14px;margin-bottom:1.5rem;box-shadow:0 4px 20px rgba(15,76,117,.35);}
.ph h1{color:#fff;font-size:1.7rem;margin:0;font-weight:800;}
.ph p{color:rgba(255,255,255,.78);margin:.3rem 0 0;font-size:.88rem;}
.pipe-box{display:flex;align-items:stretch;gap:0;flex-wrap:nowrap;overflow-x:auto;margin:1.2rem 0;}
.pnode{flex:1;min-width:130px;background:#12121f;border:1px solid rgba(27,108,168,.3);border-radius:12px;padding:1.2rem .8rem;text-align:center;}
.pnode.done{border-color:rgba(16,185,129,.5);background:rgba(16,185,129,.06);}
.pnode .icon{font-size:1.8rem;}
.pnode .lbl{font-size:.65rem;font-weight:700;color:rgba(232,232,240,.5);text-transform:uppercase;letter-spacing:.05em;margin:.3rem 0 .15rem;}
.pnode .val{font-size:1.3rem;font-weight:800;color:#E8E8F0;}
.pnode .sub{font-size:.7rem;color:rgba(232,232,240,.4);margin-top:.15rem;}
.pnode.done .lbl{color:#10B981;}
.arrow{display:flex;align-items:center;padding:0 .4rem;color:rgba(232,232,240,.2);font-size:1.3rem;flex-shrink:0;}
.chunk-card{background:#12121f;border:1px solid rgba(27,108,168,.2);border-left:3px solid #1B6CA8;border-radius:0 8px 8px 0;padding:.7rem 1rem;margin:.35rem 0;font-size:.78rem;color:rgba(232,232,240,.8);line-height:1.5;}
.chunk-meta{font-size:.68rem;color:rgba(232,232,240,.4);margin-top:.3rem;}
.emb-row{display:flex;gap:.3rem;flex-wrap:wrap;margin:.5rem 0;}
.emb-cell{background:rgba(27,108,168,.15);color:#60A5FA;border-radius:4px;padding:.15rem .4rem;font-size:.68rem;font-family:monospace;}
</style>""", unsafe_allow_html=True)

st.markdown("""<div class="ph"><h1>🔬 Step 2 — Ingestion Pipeline</h1>
<p>Documents → Pages → Text Chunks → Embeddings → ChromaDB Vector Store</p></div>""",
unsafe_allow_html=True)

if not st.session_state.get("indexed"):
    st.warning("⚠️ No documents indexed yet. Go to **Step 1 → Upload** first.")
    st.stop()

from src.vectorstore.store import collection_stats, get_collection

sm   = st.session_state.get("sm_docs",  [])
syl  = st.session_state.get("syl_docs", [])
cks  = st.session_state.get("all_chunks", [])
n_ec = st.session_state.get("emb_count", len(cks))
edim = st.session_state.get("emb_dim", 384)
cs   = collection_stats()

n_docs  = len({c["source"] for c in sm+syl})
n_pages = len(sm) + len(syl)
n_cks   = len(cks)

# ── Pipeline diagram ──────────────────────────────────────────────────────────
st.markdown("### 📊 Pipeline Overview")

def _node(icon, lbl, val, sub=""):
    return f"""<div class="pnode done">
<div class="icon">{icon}</div>
<div class="lbl">{lbl}</div>
<div class="val">{val}</div>
<div class="sub">{sub}</div>
</div>"""

arr = '<div class="arrow">→</div>'

st.markdown(f"""<div class="pipe-box">
{_node("📂","Documents",n_docs,f"SM:{len({c['source'] for c in sm})} · Syl:{len({c['source'] for c in syl})}")}
{arr}
{_node("📄","Pages / Sections",n_pages,"raw extracted")}
{arr}
{_node("✂️","Text Chunks",n_cks,"500 words, 50 overlap")}
{arr}
{_node("🔢","Embeddings",n_ec,f"dim = {edim}")}
{arr}
{_node("💾","ChromaDB",cs['total_chunks'],"cosine similarity index")}
</div>""", unsafe_allow_html=True)

st.markdown("---")

# ── Document breakdown ────────────────────────────────────────────────────────
st.markdown("### 📁 Document Breakdown")
tab_sm, tab_syl = st.tabs(["📚 Study Material", "📋 Syllabus"])

def _show_docs(docs):
    sources = sorted({c["source"] for c in docs})
    for src in sources:
        src_chunks = [c for c in docs if c["source"]==src]
        with st.expander(f"**{src}** — {len(src_chunks)} pages/sections"):
            for c in src_chunks[:5]:
                st.markdown(
                    f'<div class="chunk-card">{c["text"][:250]}…'
                    f'<div class="chunk-meta">Page {c.get("page","?")} · {c["metadata"].get("char_count","?")} chars · {c["metadata"].get("source_type","")}</div></div>',
                    unsafe_allow_html=True)
            if len(src_chunks) > 5:
                st.caption(f"… and {len(src_chunks)-5} more pages")

with tab_sm:  _show_docs(sm)
with tab_syl: _show_docs(syl)

st.markdown("---")

# ── Chunk browser ─────────────────────────────────────────────────────────────
st.markdown("### ✂️ Text Chunks")
col_f1, col_f2 = st.columns([2,1])
with col_f1:
    search = st.text_input("🔍 Filter chunks by keyword", key="ck_search", label_visibility="collapsed",
                            placeholder="Search chunks…")
with col_f2:
    show_n = st.selectbox("Show", [5,10,20,50], key="ck_n", label_visibility="collapsed")

disp_chunks = cks
if search.strip():
    disp_chunks = [c for c in cks if search.lower() in c["text"].lower()]
    st.caption(f"{len(disp_chunks)} chunks match '{search}'")

for c in disp_chunks[:show_n]:
    src  = c.get("source","?")
    pg   = c.get("page","?")
    meta = c.get("metadata",{})
    wc   = meta.get("word_count", len(c["text"].split()))
    stype= meta.get("source_type","")
    st.markdown(
        f'<div class="chunk-card">{c["text"][:300]}…'
        f'<div class="chunk-meta">📄 {src} · §{pg} · {wc} words · {stype}</div></div>',
        unsafe_allow_html=True)

if len(disp_chunks) > show_n:
    st.caption(f"Showing {show_n} of {len(disp_chunks)} chunks")

st.markdown("---")

# ── Embedding preview ─────────────────────────────────────────────────────────
st.markdown("### 🔢 Embedding Preview")
st.caption(f"Each chunk is encoded into a **{edim}-dimensional** vector for semantic similarity search.")

try:
    col_data = get_collection()
    sample   = col_data.get(limit=3, include=["documents","embeddings"])
    if sample and sample.get("embeddings") is not None:
        embs = [list(map(float, e)) for e in sample["embeddings"]]
        for i,(doc,emb) in enumerate(zip(sample["documents"], embs)):
            with st.expander(f"Chunk {i+1}: *{doc[:60]}…*"):
                st.markdown(f"**Vector** (first 20 of {len(emb)} dims):")
                cells = "".join(f'<span class="emb-cell">{v:.4f}</span>' for v in emb[:20])
                st.markdown(f'<div class="emb-row">{cells}</div>…({len(emb)-20} more)', unsafe_allow_html=True)
except Exception as e:
    st.info("Embedding preview unavailable.")

st.markdown("---")
st.markdown("### ✅ ChromaDB Summary")
cc1,cc2,cc3 = st.columns(3)
cc1.metric("Total Chunks Stored", cs["total_chunks"])
cc2.metric("Embedding Dimension", edim)
cc3.metric("Similarity Metric", "Cosine")
st.success("✅ Ingestion complete! Proceed to **Step 3 → Paper Structure**")
