### A. Web App — Audio Transcription Flow (Original System)

This flow handles the user-facing voice-to-transcript workflow.

```mermaid
sequenceDiagram
    participant User
    participant Frontend as React Frontend
    participant Backend as FastAPI Backend
    participant Whisper as Whisper Module
    participant LLM as LLM Client

    User->>Frontend: Record/Upload audio
    Frontend->>Backend: POST /api/transcribe (audio)
    Backend->>Whisper: Run inference (transcribe_audio)
    Whisper-->>Backend: Return Raw Transcript

    Backend->>LLM: Clean transcript (clean_transcript)
    LLM-->>Backend: Return Refined Text

    Backend-->>Frontend: Return JSON {original, cleaned}
    Frontend-->>User: Display Side-by-Side View
```

#### **A. Web App: Audio Transcription Workflow**

This workflow describes how recorded or uploaded audio is converted into readable text.

| Step | Action                                                   | Component Responsible       |
| ---- | -------------------------------------------------------- | --------------------------- |
| 1    | User records or uploads audio                            | Frontend (Browser UI)       |
| 2    | Audio is sent as a request to `/api/transcribe`          | Frontend → Backend          |
| 3    | Audio format is validated and temporarily stored         | Backend                     |
| 4    | Whisper model performs speech-to-text conversion         | Transcription Module        |
| 5    | Raw transcript is sent to LLM for refinement             | Backend → Local LLM Service |
| 6    | Cleaned transcript is returned to the backend            | LLM Service                 |
| 7    | Backend returns JSON response `{raw_text, cleaned_text}` | Backend                     |
| 8    | Transcript is displayed (side-by-side) to the user       | Frontend UI                 |

**Result:**  
User receives both raw and refined text for comparison and further usage.

---

### B. CLI Tool — PDF-to-Mind-Map Flow (New Feature)

```mermaid
sequenceDiagram
    participant User
    participant CLI as CLI Orchestrator
    participant PDF as PDF Extractor
    participant LLM as Ollama Service
    participant HTML as HTML Generator

    User->>CLI: Run cli_mindmap.py [PDF, Page, Index]

    CLI->>PDF: extract_paragraph(path, page, index)
    PDF-->>CLI: Return Raw Paragraph Text

    CLI->>LLM: Request Cleaning (System Prompt: "Editor")
    LLM-->>CLI: Return Cleaned Transcript

    CLI->>LLM: Request Structuring (System Prompt: "JSON Tree")
    LLM-->>CLI: Return Hierarchical JSON

    CLI->>HTML: Inject JSON into Mermaid Template
    HTML-->>CLI: Write .html file to disk

    CLI-->>User: Success Message + File Path
```

#### **B. CLI Tool: PDF-to-Mind-Map Workflow (New Feature)**

This workflow explains how a paragraph in a PDF becomes a structured mind-map.

| Step | Action                                                                 | Component Responsible |
| ---- | ---------------------------------------------------------------------- | --------------------- |
| 1    | User runs CLI command with PDF path, page, and paragraph index         | User → CLI Tool       |
| 2    | Text is extracted from selected paragraph                              | PDF Extractor Module  |
| 3    | Extracted text is cleaned using the LLM (normalization and grammar)    | CLI → LLM Service     |
| 4    | Cleaned text is sent back to LLM to generate structured JSON hierarchy | CLI → LLM Service     |
| 5    | JSON is embedded into an HTML/Mermaid mind-map template                | Mind-Map Generator    |
| 6    | Final mind-map `.html` file is saved to disk                           | CLI Tool              |
| 7    | CLI prints the `"Success"` message with output file location           | CLI Output            |

**Result:**  
User obtains an interactive web-based mind map derived from the selected paragraph.

---
---
