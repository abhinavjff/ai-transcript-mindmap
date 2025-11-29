# 📝 Changelog

This document summarizes the modifications, enhancements, and new files added as part of the assignment tasks.

---

## 📅 Version 1.1 — Assignment Submission Release

### 🔧 Added

- **New CLI Feature**

  - `execute.py` — root-level entry point for running the mind-map workflow.
  - `backend/cli_mindmap.py` — orchestrates PDF extraction, transcript cleaning, and mind-map generation.
  - `backend/pdf_extractor.py` — extracts paragraph-level text from PDF documents.
  - `backend/mindmap_service.py` — generates structured JSON and HTML mind-maps.
  - `backend/transcript_service.py` — reused cleaning logic for both voice and PDF pipelines.

- **Documentation**

  - `architecture.md` — full architecture overview including both pipelines.
  - `dfd.md` — Data Flow Diagrams (voice→transcript and paragraph→mind-map).
  - `sequence.md` — detailed sequence diagrams for both workflows.
  - `README.md` — updated with setup steps, usage instructions, and feature details.

- **Logging**

  - Implemented detailed runtime logging for extraction, validation, inference, and visual output generation.
  - Added `performance.log` containing real sample execution logs (metadata, timing, memory usage, and output status).

- **Output Artifacts**
  - `mindmap.html` — generated example mind-map output for reviewer reference.

---

### 🛠 Improved

- Integrated transcript sanitization flow into the new PDF pipeline using existing LLM interface.
- Extended environment configuration support for multi-model backends (Ollama / LM Studio / OpenAI API compatible).
- Ensured consistent error handling and safe fallback behavior during failed inference.

---

### 🗂 Restructured

- Maintained project structure alignment with the base repository.
- Introduced separation of concerns between:
  - PDF extraction
  - Text cleaning
  - Mind-map generation
  - API functionality

---

### 🧪 Tested

- Verified functionality using:

````bash
uv run --project backend python execute.py backend/data/why-llm-cant-develop-software.pdf 1 15 --output mindmap.html```
````
