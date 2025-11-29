import logging
import time
import sys
import os
from dotenv import load_dotenv
from openai import OpenAI
from pdf_extractor import extract_paragraph

# 1. Load environment variables from .env
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 2. Get Configuration from .env
# Inside DevContainer, this should be "http://ollama:11434/v1"
base_url = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
api_key = os.getenv("LLM_API_KEY", "ollama")
model_name = os.getenv("LLM_MODEL", "llama3.1:8b")

logger.info(f"Connecting to LLM at: {base_url}")
logger.info(f"Using Model: {model_name}")

# Initialize OpenAI Client
client = OpenAI(base_url=base_url, api_key=api_key)


def clean_transcript(raw_text: str):
    """
    Sends raw text to the LLM for cleaning/normalization.
    """
    start_time = time.time()

    # Estimate tokens (approx 4 chars per token)
    input_tokens = len(raw_text) / 4

    logger.info(f"--- Processing Step: LLM Cleaning ---")
    logger.info(f"Input Text Length: {len(raw_text)} chars")

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful editor. Your task is to clean up the following text. Fix grammar, remove formatting artifacts, and ensure it reads smoothly as a transcript. Do not summarize; keep the full content.",
                },
                {"role": "user", "content": raw_text},
            ],
            temperature=0.2,
        )

        cleaned_text = response.choices[0].message.content
        end_time = time.time()

        # Output Metrics
        output_tokens = len(cleaned_text) / 4
        processing_time = end_time - start_time
        memory_usage = sys.getsizeof(cleaned_text)

        # Logging per requirements
        logger.info(f"--- Transcript Generation Complete ---")
        logger.info(f"Cleaned Text Length: {len(cleaned_text)} chars")
        logger.info(f"Processing Time: {processing_time:.4f}s")
        logger.info(f"Memory Usage: {memory_usage} bytes")

        return cleaned_text

    except Exception as e:
        logger.error(f"LLM Processing failed: {str(e)}")
        return raw_text


def process_pdf_paragraph(pdf_path, page, paragraph_index):
    """
    Orchestrates extraction and cleaning.
    """
    # Step 1: Extract
    extraction_result = extract_paragraph(pdf_path, page, paragraph_index)
    raw_text = extraction_result["text"]

    # Step 2: Clean
    cleaned_text = clean_transcript(raw_text)

    return {
        "original": raw_text,
        "cleaned": cleaned_text,
        "metadata": extraction_result,
    }


if __name__ == "__main__":
    test_path = "data/why-llm-cant-develop-software.pdf"

    # Test with Page 1, Paragraph 0
    print("Running pipeline...")
    # NOTE: Ensure the file exists at backend/data/why-llm-cant-develop-software.pdf
    try:
        result = process_pdf_paragraph(test_path, 1, 0)

        print("\n=== RAW TEXT ===")
        print(result["original"][:100] + "...")
        print("\n=== CLEANED TRANSCRIPT ===")
        print(result["cleaned"])
    except Exception as e:
        print(f"Error: {e}")
