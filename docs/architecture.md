# Architecture: Agentic AI-Based Descriptive Question Paper Generator

## Overview

An agentic RAG system that ingests academic documents (PDFs, DOCX, PPTX, TXT),
builds a persistent vector knowledge base, and generates validated,
Bloom's Taxonomy-aligned descriptive question papers using the Grok LLM API.

---

## High-Level Architecture

```
+----------------------------------------------------------------------+
|                        STREAMLIT UI LAYER                            |
|  Dashboard | Doc Library | Syllabus | KB | Generate | Export         |
+-------------------------------+--------------------------------------+
                                |
+-------------------------------v--------------------------------------+
|                    AGENTIC ORCHESTRATOR                              |
|  Input Validation -> Planning -> Retrieval -> Generation ->          |
|  Validation -> Repair -> Final Validation                            |
+--+----------+-----------+-------------+-----------------------+------+
   |          |           |             |                       |
+--v--+  +----v---+  +----v-----+  +---v--------+  +----------v-----+
| DOC |  |SYLLAB. |  | VECTOR   |  |  QUESTION  |  |  VALIDATOR &   |
|PROC.|  |PARSER  |  |    DB    |  | GENERATOR  |  |   EXPORTER     |
+--+--+  +----+---+  +----+-----+  +---+--------+  +----------------+
   |          |           |             |
   |     +----v----+  +---v-----+  +---v------+
   |     |Pydantic |  |ChromaDB |  | Grok API |
   |     |Schemas  |  |Persist. |  |  (xAI)   |
   +-----> sentence|  +---------+  +----------+
         |transform|
         +---------+
```

---

## Module Breakdown

### 1. Document Processor (src/ingestion/)
- Input  : PDF, DOCX, PPTX, TXT files
- Tools  : PyMuPDF (text PDFs), Tesseract OCR (scanned), python-docx, python-pptx
- Output : List of Document objects with {text, source, page, metadata}

### 2. Syllabus & Blueprint Parser (src/parsing/)
- Input  : Syllabus PDF/DOCX + Sample Question Papers
- Tools  : Structured extraction (LLM + regex)
- Output : SyllabusSchema (units, COs, marks, sections, duration)

### 3. Chunking & Embedding Engine (src/vectorstore/)
- Input  : Processed documents
- Tools  : 500-800 token chunks, sentence-transformers/all-MiniLM-L6-v2
- Output : Vectors stored in ChromaDB (persistent, local)

### 4. Retrieval Pipeline (src/retrieval/)
- Input  : Query + filters (unit, source type, topic)
- Tools  : Semantic search + metadata filtering
- Output : Ranked, deduplicated context passages with provenance

### 5. Grok API Client (src/llm/)
- Provider : xAI Grok API (OpenAI-compatible)
- Config   : .env file (XAI_API_KEY, XAI_MODEL)
- Features : Retry, rate-limit handling, structured JSON output

### 6. Question Generator (src/generation/)
- Input  : Retrieved context + blueprint constraints
- Tools  : Prompt engineering for all 6 Bloom's Taxonomy levels
- Output : QuestionPaper Pydantic model

### 7. Validator (src/validation/)
- Checks : Marks totals, question counts, CO mapping, Bloom distribution, duplicates
- Repair : Bounded retry loop (max 3 repair attempts)

### 8. Agentic Orchestrator (src/orchestrator.py)
- Flow   : 7-stage explicit state machine
- Safety : Max iteration limits, error recovery, intermediate state preservation

### 9. Exporter (src/export/)
- Formats : PDF (ReportLab), DOCX (python-docx)
- Content : Header, instructions, sections, questions, marks, answer key

### 10. Streamlit UI (app.py, pages/)
- Pages  : Dashboard, Doc Library, Syllabus, KB, Generate, Review, Export, Settings

---

## Directory Structure

```
RAG_Question_Paper_Generator/
|-- app.py                        # Streamlit entry point
|-- .env                          # API keys (not committed)
|-- .env.example                  # Template
|-- .gitignore
|-- requirements.txt
|-- docs/
|   |-- architecture.md
|   +-- implementation_plan.md
|-- src/
|   |-- __init__.py
|   |-- config.py                 # Settings, env loading
|   |-- ingestion/
|   |   |-- __init__.py
|   |   |-- pdf_processor.py      # PyMuPDF + OCR fallback
|   |   |-- docx_processor.py     # python-docx
|   |   |-- pptx_processor.py     # python-pptx
|   |   +-- txt_processor.py      # Plain text
|   |-- parsing/
|   |   |-- __init__.py
|   |   |-- syllabus_parser.py    # Structured syllabus extraction
|   |   +-- schemas.py            # Pydantic models for syllabus
|   |-- vectorstore/
|   |   |-- __init__.py
|   |   |-- chunker.py            # Structure-aware chunking
|   |   |-- embedder.py           # sentence-transformers wrapper
|   |   +-- chromadb_store.py     # ChromaDB CRUD operations
|   |-- retrieval/
|   |   |-- __init__.py
|   |   +-- retriever.py          # Semantic search + metadata filters
|   |-- llm/
|   |   |-- __init__.py
|   |   +-- grok_client.py        # xAI Grok API client
|   |-- generation/
|   |   |-- __init__.py
|   |   |-- question_generator.py # Bloom's + CO-aligned generation
|   |   |-- prompts.py            # Prompt templates
|   |   +-- schemas.py            # Question, Paper Pydantic models
|   |-- validation/
|   |   |-- __init__.py
|   |   +-- validator.py          # Deterministic + semantic checks
|   |-- export/
|   |   |-- __init__.py
|   |   |-- pdf_exporter.py       # ReportLab PDF generation
|   |   +-- docx_exporter.py      # python-docx export
|   +-- orchestrator.py           # Agentic pipeline state machine
|-- pages/
|   |-- 1_Document_Library.py
|   |-- 2_Syllabus_Blueprint.py
|   |-- 3_Knowledge_Base.py
|   |-- 4_Generate_Paper.py
|   |-- 5_Review_Validation.py
|   |-- 6_Export_History.py
|   +-- 7_Settings.py
|-- data/
|   |-- uploads/                  # Temporary uploaded files
|   |-- chromadb/                 # Persistent vector store
|   +-- exports/                  # Generated papers
+-- .venv/                        # Virtual environment (not committed)
```

---

## Technology Stack

| Component         | Technology                        | Reason                        |
|-------------------|-----------------------------------|-------------------------------|
| UI                | Streamlit                         | Rapid academic app UI         |
| LLM               | Grok API (xAI)                    | Primary & only LLM provider   |
| Embeddings        | all-MiniLM-L6-v2                  | CPU-friendly local embeddings |
| Vector DB         | ChromaDB                          | Persistent local storage      |
| PDF processing    | PyMuPDF + Tesseract OCR           | Text + scanned PDF support    |
| DOCX processing   | python-docx                       | Word document support         |
| PPTX processing   | python-pptx                       | PowerPoint support            |
| Schemas           | Pydantic v2                       | Structured validation         |
| PDF export        | ReportLab                         | Programmatic PDF creation     |
| Env config        | python-dotenv                     | Safe secret management        |

## Key Constraints

- No GPU required — all-MiniLM-L6-v2 runs on CPU (~100ms/query)
- Grok API key loaded via .env — never hardcoded or logged
- Grok is the only LLM — no silent fallback to another provider
- ChromaDB stored on local disk — persists across restarts
- Max 3 repair attempts per paper generation cycle
