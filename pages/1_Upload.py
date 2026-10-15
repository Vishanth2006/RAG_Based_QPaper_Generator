"""
Page 1 — Upload Documents & Syllabus
Upload study material (PDF/DOCX/PPTX/TXT) and syllabus files.
"""
import streamlit as st, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="Upload | RAG QPG", page_icon="📂", layout="wide")

# ── shared style ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.ph{background:linear-gradient(135deg,#6C63FF,#3B82F6);padding:1.4rem 2rem;border-radius:14px;margin-bottom:1.5rem;box-shadow:0 4px 20px rgba(108,99,255,.3);}
.ph h1{color:#fff;font-size:1.7rem;margin:0;font-weight:800;}
.ph p{color:rgba(255,255,255,.78);margin:.3rem 0 0;font-size:.88rem;}
.fc{background:#12121f;border:1px solid rgba(108,99,255,.2);border-radius:9px;padding:.65rem 1rem;margin:.3rem 0;display:flex;justify-content:space-between;align-items:center;}
.fc span{color:#E8E8F0;font-size:.82rem;}
.ok{background:rgba(16,185,129,.15);color:#10B981;border:1px solid rgba(16,185,129,.3);border-radius:20px;padding:.1rem .65rem;font-size:.7rem;font-weight:700;}
.info-box{background:#12121f;border:1px solid rgba(108,99,255,.2);border-radius:10px;padding:1rem 1.2rem;margin:.5rem 0;}
.stat{text-align:center;padding:.8rem;}
.stat-n{font-size:2rem;font-weight:800;color:#6C63FF;}
.stat-l{font-size:.72rem;color:rgba(232,232,240,.5);text-transform:uppercase;letter-spacing:.05em;}
</style>""", unsafe_allow_html=True)

st.markdown("""<div class="ph"><h1>📂 Step 1 — Upload Documents & Syllabus</h1>
<p>Upload your study material and course syllabus to build the knowledge base</p></div>""",
unsafe_allow_html=True)

# ── session init ──────────────────────────────────────────────────────────────
for k,v in [("sm_docs",[]),("syl_docs",[]),("all_chunks",[]),
            ("indexed",False),("emb_count",0),("emb_dim",384)]:
    if k not in st.session_state: st.session_state[k] = v

from src.ingestion import process_file
from src.vectorstore.chunker import rechunk_documents
from src.vectorstore.embedder import get_embeddings
from src.vectorstore import store as vector_store

upsert_chunks = vector_store.upsert_chunks
collection_stats = vector_store.collection_stats
clear_collection = vector_store.clear_collection


def collection_sources():
    """Read persisted sources even when an older Streamlit module is cached."""
    if hasattr(vector_store, "collection_sources"):
        return vector_store.collection_sources()
    try:
        data = vector_store.get_collection().get(include=["metadatas"])
        counts = {}
        for metadata in data.get("metadatas", []) or []:
            metadata = metadata or {}
            key = (metadata.get("source", "Unknown source"), metadata.get("source_type", ""))
            counts[key] = counts.get(key, 0) + 1
        return [
            {"source": source, "source_type": source_type, "chunks": chunks}
            for (source, source_type), chunks in sorted(counts.items())
        ]
    except Exception:
        return []

# ── stats row ─────────────────────────────────────────────────────────────────
cs = collection_stats()
stored_sources = collection_sources()
c1,c2,c3,c4 = st.columns(4)
for col,n,lbl in [
    (c1, len({c["source"] for c in st.session_state.sm_docs}),  "Study Files"),
    (c2, len({c["source"] for c in st.session_state.syl_docs}), "Syllabus Files"),
    (c3, len(st.session_state.all_chunks),                       "Text Chunks"),
    (c4, cs["total_chunks"],                                     "Stored Chunks"),
]:
    col.markdown(f'<div class="stat"><div class="stat-n">{n}</div><div class="stat-l">{lbl}</div></div>',
                 unsafe_allow_html=True)

st.markdown("---")

if stored_sources and not st.session_state.indexed:
    st.info("Stored ChromaDB data remains available after refresh. The current upload lists reset because they are session-only.")
    st.markdown("### Persisted documents")
    for source in stored_sources:
        source_type = source["source_type"].replace("_", " ") or "unknown type"
        st.markdown(f"- **{source['source']}** · {source_type} · {source['chunks']} chunks")

# ── upload zones ──────────────────────────────────────────────────────────────
left, right = st.columns(2)

with left:
    st.markdown("### 📚 Study Material")
    st.caption("Lecture notes, textbook chapters, reference material")
    sm_files = st.file_uploader("Upload study material", type=["pdf","docx","pptx","txt"],
                                 accept_multiple_files=True, key="up_sm", label_visibility="collapsed")
    if st.session_state.sm_docs:
        for src in sorted({c["source"] for c in st.session_state.sm_docs}):
            n = len([c for c in st.session_state.sm_docs if c["source"]==src])
            st.markdown(f'<div class="fc"><span>📄 {src}</span><span class="ok">✓ {n} pages</span></div>',
                        unsafe_allow_html=True)

with right:
    st.markdown("### 📋 Syllabus")
    st.caption("Course syllabus, unit plan, course outcomes")
    syl_files = st.file_uploader("Upload syllabus", type=["pdf","docx","txt"],
                                  accept_multiple_files=True, key="up_syl", label_visibility="collapsed")
    if st.session_state.syl_docs:
        for src in sorted({c["source"] for c in st.session_state.syl_docs}):
            n = len([c for c in st.session_state.syl_docs if c["source"]==src])
            st.markdown(f'<div class="fc"><span>📋 {src}</span><span class="ok">✓ {n} pages</span></div>',
                        unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── action buttons ─────────────────────────────────────────────────────────────
b1, b2, b3 = st.columns([2,2,1])
with b1:
    proc = st.button("⚡ Process & Index All Files", type="primary", key="btn_proc",
                     disabled=not (sm_files or syl_files), use_container_width=True)
with b2:
    if st.session_state.indexed:
        st.success(f"✅ {cs['total_chunks']} chunks indexed in ChromaDB — proceed to **Step 2 →**")
with b3:
    if st.button("🗑️ Reset All", key="btn_reset", use_container_width=True):
        clear_collection()
        for k in ["sm_docs","syl_docs","all_chunks","indexed","emb_count","emb_dim",
                  "sections","paper_config","retrieval_results","generated_paper","edited_questions"]:
            if k in st.session_state: del st.session_state[k]
        st.rerun()

# ── processing ────────────────────────────────────────────────────────────────
if proc:
    clear_collection()
    st.session_state.sm_docs = []; st.session_state.syl_docs = []
    st.session_state.all_chunks = []; st.session_state.indexed = False

    def _ingest(files, stype, label):
        chunks = []
        prog = st.progress(0, f"Reading {label}…")
        for i, uf in enumerate(files):
            prog.progress((i+1)/len(files), f"{label}: {uf.name}")
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uf.name).suffix) as t:
                t.write(uf.read()); tp = Path(t.name)
            try:
                raw = process_file(tp)
                for c in raw:
                    c["source"] = uf.name
                    c["metadata"]["source_type"] = stype
                chunks.extend(raw)
                st.success(f"✅ **{uf.name}** → {len(raw)} pages extracted")
            except Exception as e:
                st.error(f"❌ {uf.name}: {e}")
            finally:
                tp.unlink(missing_ok=True)
        prog.empty()
        return chunks

    if sm_files:  st.session_state.sm_docs  = _ingest(sm_files,  "study_material", "Study Material")
    if syl_files: st.session_state.syl_docs = _ingest(syl_files, "syllabus",        "Syllabus")

    all_raw = st.session_state.sm_docs + st.session_state.syl_docs
    st.info(f"Chunking {len(all_raw)} pages into 500-word overlapping chunks…")
    chunks = rechunk_documents(all_raw, chunk_size=500, overlap=50)
    st.session_state.all_chunks = chunks

    with st.spinner(f"Generating embeddings for {len(chunks)} chunks…"):
        embs = get_embeddings([c["text"] for c in chunks])
        st.session_state.emb_count = len(embs)
        st.session_state.emb_dim   = len(embs[0]) if embs else 384

    with st.spinner("Storing in ChromaDB…"):
        upsert_chunks(chunks, embs)
        st.session_state.indexed = True
        st.session_state.retrieval_results = []
        st.session_state.pop("generated_paper", None)
        st.session_state.pop("edited_questions", None)
        st.session_state.pop("generation_request", None)

    st.balloons()
    st.success(f"🎉 Done! {len(chunks)} chunks embedded (dim {st.session_state.emb_dim}) and stored. Go to **Step 2 → Ingestion Pipeline**")
    st.rerun()
