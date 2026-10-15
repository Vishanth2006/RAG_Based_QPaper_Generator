# Implementation Plan: Agentic RAG Question Paper Generator

## Project Summary

Build an Agentic AI system that:
1. Ingests study materials, syllabi, and sample papers (PDF/DOCX/PPTX/TXT)
2. Builds a persistent, searchable knowledge base using ChromaDB
3. Generates validated, Bloom's Taxonomy-aligned descriptive question papers
4. Exports professional DOCX and PDF documents
5. Provides a clean Streamlit-based user interface

---

## Stage-by-Stage Plan

---

### Stage 0 — Requirement Analysis and Development Plan [CURRENT]
**Goal**: Understand requirements, define architecture, create plan.
**Deliverables**: `docs/architecture.md`, `docs/implementation_plan.md`
**Acceptance**: Both documents created, directory structure defined.

---

### Stage 1 — Environment and Project Skeleton
**Goal**: Working virtual environment, installed dependencies, minimal Streamlit app.

**Tasks**:
- Create `.venv` using `python -m venv .venv`
- Create `requirements.txt` with all pinned dependencies
- Install all packages into `.venv`
- Create `.env.example` with API key template
- Create `.gitignore`
- Create `src/` package structure (empty `__init__.py` files)
- Create `app.py` — minimal Streamlit dashboard placeholder
- Create `data/` subdirectories

**Acceptance Criteria**:
- `.venv\Scripts\activate` works
- All packages install without conflict
- `streamlit run app.py` launches without error
- Browser shows the dashboard placeholder page

---

### Stage 2 — Document Ingestion (PDF, DOCX, PPTX, TXT)
**Goal**: Extract clean, structured text with metadata from all supported formats.

**Tasks**:
- `src/ingestion/pdf_processor.py` — PyMuPDF extraction + Tesseract OCR fallback
- `src/ingestion/docx_processor.py` — headings, paragraphs, tables via python-docx
- `src/ingestion/pptx_processor.py` — slide text, notes via python-pptx
- `src/ingestion/txt_processor.py` — plain text with encoding detection
- `src/ingestion/__init__.py` — unified `process_file(path)` dispatch function
- Error handling: empty, corrupted, unsupported, duplicate files
- Partial batch failure isolation

**Acceptance Criteria**:
- Each format returns `[{"text": ..., "source": ..., "page": ..., "metadata": {...}}]`
- Corrupt/empty files raise documented exceptions, not silent failures
- Batch processing: one failed file does not stop others

---

### Stage 3 — Syllabus and Sample Paper Parsing
**Goal**: Extract structured course and examination blueprint from documents.

**Tasks**:
- `src/parsing/schemas.py` — Pydantic models: `Unit`, `CourseOutcome`, `Section`, `Blueprint`
- `src/parsing/syllabus_parser.py` — regex + LLM-assisted structured extraction
- Fields: course code/title, units/topics, COs, weightages, duration, marks, sections
- Expose uncertain fields for user review in UI
- Do not fabricate missing fields — mark as `None` or `unknown`

**Acceptance Criteria**:
- Real syllabus document produces a `Blueprint` object
- Unit list, CO list, marks per section are correctly extracted
- Fields not found are clearly marked as missing

---

### Stage 4 — Chunking, Embeddings, and ChromaDB
**Goal**: Index all processed documents into a persistent, queryable vector store.

**Tasks**:
- `src/vectorstore/chunker.py` — 500–800 token chunks, configurable overlap (10%)
- `src/vectorstore/embedder.py` — `all-MiniLM-L6-v2` wrapper, batch encoding
- `src/vectorstore/chromadb_store.py` — collection CRUD, metadata storage, dedup
- Metadata stored per chunk: source_file, source_type, page/slide, unit_hint, chunk_id
- Persistence: ChromaDB stored in `data/chromadb/`
- Duplicate detection by content hash
- Safe deletion of one source without affecting others

**Acceptance Criteria**:
- Insert 10 chunks → query → receive correct top-k results
- Metadata (source, page) preserved in results
- Restart app → existing chunks still retrievable
- Delete one source → other sources unaffected

---

### Stage 5 — Retrieval Pipeline
**Goal**: Retrieve relevant, filtered, deduplicated context for question generation.

**Tasks**:
- `src/retrieval/retriever.py` — semantic search + metadata filters
- Source-type filters: `study_material`, `syllabus`, `sample_paper`
- Unit filters, topic filters, multi-source retrieval
- Provenance tracking (which chunk, which document, which page)
- Duplicate chunk removal in result set
- Insufficient evidence detection (< threshold similarity)

**Acceptance Criteria**:
- Topic in KB → retrieved with correct provenance
- Synonym/paraphrase query → still retrieved
- Topic restricted to unit 2 → only unit 2 chunks returned
- Topic absent → no results or low-similarity flag
- Two books indexed → both returned for broad query

---

### Stage 6 — Grok API Integration
**Goal**: Reliable, safe, configurable connection to xAI Grok API.

**Tasks**:
- `src/llm/grok_client.py` — OpenAI-compatible client using `XAI_API_KEY`
- Model: configured via `XAI_MODEL` in `.env`
- Features: timeout, retry (max 3), rate-limit backoff, error reporting
- Structured JSON response parsing
- Secret-safe logging (key never printed)
- Connection smoke test function

**Acceptance Criteria**:
- With valid key: smoke test returns a response
- Invalid key: clear authentication error, not a crash
- Timeout: handled gracefully
- API key never appears in logs or console output

---

### Stage 7 — Question Generation
**Goal**: Generate Bloom's Taxonomy-aligned descriptive questions from retrieved evidence.

**Tasks**:
- `src/generation/schemas.py` — `Question`, `Section`, `QuestionPaper` Pydantic models
- `src/generation/prompts.py` — per-Bloom-level prompt templates
- `src/generation/question_generator.py` — full generation pipeline
- Support: descriptive + short-answer, marks distribution, Bloom level + difficulty (separate)
- CO mapping per question
- Source references per question
- Reject malformed LLM output

**Acceptance Criteria**:
- Generate 5 questions from actual indexed study material
- Each question has: text, marks, Bloom level, CO, source reference
- Malformed JSON from LLM → retry, not crash
- Out-of-syllabus question → flagged

---

### Stage 8 — Validation and Controlled Regeneration
**Goal**: Deterministically enforce all blueprint constraints on the generated paper.

**Tasks**:
- `src/validation/validator.py` — all deterministic checks
- Checks: marks totals, section sums, question counts, CO coverage, Bloom distribution,
  difficulty spread, duplicate detection, out-of-syllabus detection
- Repair loop: max 3 attempts, targeted repair of failing sections
- If repair fails: explain unmet constraints, do not produce invalid paper

**Acceptance Criteria**:
- Invalid paper (wrong marks, missing unit) → rejected with clear reason
- Valid paper → passes all checks
- Repair: one invalid question → replaced, not full regeneration
- Max 3 repair attempts enforced

---

### Stage 9 — Agentic Orchestrator
**Goal**: Connect all modules into a single, robust, observable pipeline.

**Tasks**:
- `src/orchestrator.py` — 7-stage state machine
- Stages: INPUT_VALIDATION → PLANNING → RETRIEVAL → GENERATION → VALIDATION → REPAIR → FINAL
- Progress reporting at each stage
- Intermediate state preservation (can resume after interruption)
- API call counter with configurable cap
- Safe termination on repeated failure

**Acceptance Criteria**:
- Full pipeline run produces a validated paper from real documents
- Failure at generation stage → does not produce falsely successful output
- Repair loop bounded at 3 attempts
- All stage transitions logged

---

### Stage 10 — Professional Streamlit UI
**Goal**: Complete, usable 8-page Streamlit application.

**Pages**:
1. `app.py` — Dashboard (stats, recent papers, quick actions)
2. `pages/1_Document_Library.py` — Upload, status, manage files
3. `pages/2_Syllabus_Blueprint.py` — Editable course structure
4. `pages/3_Knowledge_Base.py` — Search, chunk count, source management
5. `pages/4_Generate_Paper.py` — Configuration form + generation trigger
6. `pages/5_Review_Validation.py` — Review questions, edit, validation summary
7. `pages/6_Export_History.py` — Download DOCX/PDF, history
8. `pages/7_Settings.py` — API config, model, chunking params

**Acceptance Criteria**:
- All pages navigate correctly
- File upload shows per-file status
- Generation form validates inputs before submitting
- Validation results displayed clearly
- Questions editable before export

---

### Stage 11 — DOCX and PDF Export
**Goal**: Generate professional, print-ready examination documents.

**Tasks**:
- `src/export/docx_exporter.py` — python-docx with Word styles
- `src/export/pdf_exporter.py` — ReportLab with headers, footers, page numbers
- Content: institution name, course, duration, marks, instructions, sections, questions
- Optional answer key / marking scheme
- Consistent typography, margins, spacing

**Acceptance Criteria**:
- DOCX opens in Word, text is editable
- PDF renders correctly, question count matches
- Marks total on paper matches blueprint
- Page breaks between sections

---

### Stage 12 — Edge Cases and Regression
**Goal**: Test all documented edge cases, confirm no regressions.

**Edge Cases**:
- Corrupted/empty files, scanned PDFs, duplicate uploads, large files
- Missing API key, rate limiting, malformed LLM output
- Impossible paper configuration (marks don't add up)
- Prompt injection in uploaded documents
- Interrupted processing

**Deliverable**: Test report with pass/fail/blocked status per case.

---

### Stage 13 — Documentation and Final Delivery
**Goal**: Complete, self-contained project with setup guide.

**Deliverables**:
- `README.md` with full setup, usage, troubleshooting
- `docs/architecture.md` (updated)
- `docs/implementation_plan.md` (updated)
- `.env.example`
- `requirements.txt` (final)
- Sample synthetic dataset
- Example generated paper

---

## Dependency Map

```
Stage 0  (plan)
  |
Stage 1  (env + skeleton)
  |
Stage 2  (ingestion)
  |
Stage 3  (parsing/syllabus)
  |
Stage 4  (chunking + ChromaDB)
  |
Stage 5  (retrieval)
  |
Stage 6  (Grok API)
  |
Stage 7  (question generation)   <-- depends on 5 + 6
  |
Stage 8  (validation)            <-- depends on 7
  |
Stage 9  (orchestrator)          <-- depends on 2-8
  |
Stage 10 (UI)                    <-- depends on 9
  |
Stage 11 (export)                <-- depends on 8 + 10
  |
Stage 12 (edge cases)            <-- depends on all
  |
Stage 13 (docs + delivery)
```

---

## Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Tesseract not installed | OCR fallback fails | Document installation steps, graceful skip |
| Grok API rate limits | Generation blocked | Exponential backoff, configurable delay |
| ChromaDB version conflicts | Vector store fails | Pin compatible versions |
| Large PDF memory usage | OOM on laptop | Stream processing, page-by-page extraction |
| LLM hallucination | Wrong questions | Mandatory source citation + validation layer |
| Pydantic v1 vs v2 API changes | Schema errors | Pin Pydantic version, use v2 throughout |

---

## Minimum Documents for First End-to-End Test

To test Stage 7 (generation) end-to-end, we need:
1. **One study material PDF** — any textbook chapter (even 10 pages)
2. **One syllabus document** — course outline with units and marks
3. **One sample question paper** — shows expected format

Synthetic versions can be created if real documents are unavailable.

---

## Progress Checklist

- [x] Stage 0  — Requirements Analysis and Plan
- [ ] Stage 1  — Environment and Project Skeleton
- [ ] Stage 2  — Document Ingestion
- [ ] Stage 3  — Syllabus Parsing
- [ ] Stage 4  — Chunking + ChromaDB
- [ ] Stage 5  — Retrieval Pipeline
- [ ] Stage 6  — Grok API Integration
- [ ] Stage 7  — Question Generation
- [ ] Stage 8  — Validation
- [ ] Stage 9  — Agentic Orchestrator
- [ ] Stage 10 — Streamlit UI
- [ ] Stage 11 — DOCX + PDF Export
- [ ] Stage 12 — Edge Cases + Regression
- [ ] Stage 13 — Documentation + Delivery
