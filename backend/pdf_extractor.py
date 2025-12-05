import os
import time

from pypdf import PdfReader

from logger_config import setup_logger

logger = setup_logger(__name__)


# --- ORIGINAL FUNCTION (Restored for CLI compatibility) ---
def extract_paragraph(pdf_path: str, page_number: int, paragraph_index: int):
    """
    Extracts a specific single paragraph from a PDF file.
    Used by: cli_mindmap.py
    """
    start_time = time.time()

    if not os.path.exists(pdf_path):
        logger.error(f"File not found: {pdf_path}")
        raise FileNotFoundError(f"PDF not found at {pdf_path}")

    try:
        reader = PdfReader(pdf_path)
        internal_page_idx = page_number - 1

        if internal_page_idx < 0 or internal_page_idx >= len(reader.pages):
            raise ValueError(f"Page {page_number} out of range.")

        page = reader.pages[internal_page_idx]
        full_text = page.extract_text()

        # Strategy 1: Double newlines
        paragraphs = [p.strip() for p in full_text.split("\n\n") if p.strip()]

        # Strategy 2: Single newlines fallback
        if len(paragraphs) <= 1:
            paragraphs = [
                line.strip() for line in full_text.split("\n") if line.strip()
            ]

        if paragraph_index < 0 or paragraph_index >= len(paragraphs):
            raise ValueError(f"Paragraph index {paragraph_index} out of range.")

        target_text = paragraphs[paragraph_index]

        # Log metadata
        logger.info("--- Extraction Metadata (Single) ---")
        logger.info(f"Source: {pdf_path}")
        logger.info(f"Paragraph Index: {paragraph_index}")
        logger.info(f"Extraction Time: {time.time() - start_time:.4f}s")

        return {
            "text": target_text,
            "page": page_number,
            "paragraph_index": paragraph_index,
            "length": len(target_text),
        }

    except Exception as e:
        logger.error(f"Extraction failed: {str(e)}")
        raise e


# --- NEW FUNCTION (For Web UI / Feedback Requirement) ---
def extract_text_range(
    pdf_path: str, page_number: int, start_para: int = 0, end_para: int = 2
):
    """
    Extracts a range of paragraphs (e.g., first 2 paragraphs).
    Used by: app.py (Web API)
    """
    start_time = time.time()

    if not os.path.exists(pdf_path):
        logger.error(f"File not found: {pdf_path}")
        raise FileNotFoundError(f"PDF not found at {pdf_path}")

    try:
        reader = PdfReader(pdf_path)
        internal_page_idx = page_number - 1

        if internal_page_idx < 0 or internal_page_idx >= len(reader.pages):
            raise ValueError(f"Page {page_number} out of range.")

        page = reader.pages[internal_page_idx]
        full_text = page.extract_text()

        # Same splitting strategy
        paragraphs = [p.strip() for p in full_text.split("\n\n") if p.strip()]
        if len(paragraphs) <= 1:
            logger.info(
                "Double newline split yielded minimal results. Trying single newline split."
            )
            paragraphs = [
                line.strip() for line in full_text.split("\n") if line.strip()
            ]

        # Validate Range
        if start_para < 0:
            start_para = 0
        if end_para > len(paragraphs):
            end_para = len(paragraphs)

        # Extract Range
        selected_paragraphs = paragraphs[start_para:end_para]
        target_text = " ".join(selected_paragraphs)

        logger.info("--- Extraction Metadata (Range) ---")
        logger.info(f"Source: {pdf_path}")
        logger.info(f"Range: {start_para} to {end_para}")
        logger.info(f"Time: {time.time() - start_time:.4f}s")

        return target_text

    except Exception as e:
        logger.error(f"Range extraction failed: {str(e)}")
        raise e
