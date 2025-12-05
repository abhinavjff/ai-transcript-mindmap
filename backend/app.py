import os
import tempfile
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydub import AudioSegment

from logger_config import setup_logger
from mindmap_service import generate_mindmap_json, json_to_mermaid

# --- NEW IMPORTS FOR MIND MAP ---
from pdf_extractor import extract_text_range
from transcript_service import clean_transcript
from transcription import TranscriptionService

# --------------------------------

load_dotenv()
logger = setup_logger(__name__)


# Request Models
class CleanRequest(BaseModel):
    text: str
    system_prompt: str | None = None


class MindMapRequest(BaseModel):
    pdf_path: str = "data/why-llm-cant-develop-software.pdf"
    # Feedback Requirement: "Read two paragraphs"
    start_para: int = 0
    end_para: int = 2


service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global service
    logger.info("🚀 Starting AI Transcript App...")
    try:
        service = TranscriptionService(
            whisper_model=os.getenv("WHISPER_MODEL"),
            llm_base_url=os.getenv("LLM_BASE_URL"),
            llm_api_key=os.getenv("LLM_API_KEY"),
            llm_model=os.getenv("LLM_MODEL"),
        )
        logger.info("✅ TranscriptionService initialized successfully!")
    except Exception as e:
        logger.error(f"❌ Failed to initialize TranscriptionService: {e}")
        raise e
    yield


app = FastAPI(title="AI Transcript App", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/status")
async def get_status():
    status = "ready" if service else "initializing"
    return {"status": status}


@app.get("/api/system-prompt")
async def get_system_prompt():
    if not service:
        raise HTTPException(status_code=503, detail="Service not ready")
    return {"default_prompt": service.get_default_system_prompt()}


@app.post("/api/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    if not service:
        raise HTTPException(status_code=503, detail="Service not ready")

    logger.info(f"Received audio file: {audio.filename}")
    suffix = os.path.splitext(audio.filename)[1] or ".webm"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await audio.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Save as MP3 (Feedback Requirement)
        mp3_filename = "saved_input.mp3"
        try:
            AudioSegment.from_file(tmp_path).export(mp3_filename, format="mp3")
            logger.info(f"Audio converted to MP3: {mp3_filename}")
        except Exception as e:
            logger.error(f"MP3 conversion failed: {e}")

        logger.info("Starting Whisper transcription...")
        raw_text = service.transcribe(tmp_path)
        logger.info("Transcription complete.")
        return {"success": True, "text": raw_text}

    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.post("/api/clean")
async def clean_text(request: CleanRequest):
    if not service:
        raise HTTPException(status_code=503, detail="Service not ready")
    logger.info(f"Cleaning text (len={len(request.text)})")
    try:
        cleaned = service.clean_with_llm(
            request.text, system_prompt=request.system_prompt
        )
        logger.info("Cleaning complete.")
        return {"success": True, "text": cleaned}
    except Exception as e:
        logger.error(f"Cleaning error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- NEW ENDPOINT: MIND MAP GENERATION ---
@app.post("/api/generate-mindmap")
async def generate_mindmap_endpoint(request: MindMapRequest):
    logger.info("🧠 Mindmap generation requested")

    try:
        # 1. Extract Text (First 2 paragraphs)
        logger.info(
            f"Extracting PDF paragraphs {request.start_para}-{request.end_para}..."
        )
        raw_text = extract_text_range(
            request.pdf_path, 1, request.start_para, request.end_para
        )

        # 2. Clean Text (Using logic from transcript_service)
        logger.info("Cleaning extracted text...")
        cleaned_text = clean_transcript(raw_text)

        # 3. Generate JSON
        logger.info("Structuring Mind Map JSON...")
        data_json = generate_mindmap_json(cleaned_text)

        # 4. Generate Mermaid (Feedback Requirement)
        logger.info("Converting to Mermaid syntax...")
        mermaid_code = json_to_mermaid(data_json)

        return {
            "status": "success",
            "json": data_json,
            "mermaid": mermaid_code,
            "transcript": cleaned_text,
        }

    except Exception as e:
        logger.error(f"Mindmap generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
