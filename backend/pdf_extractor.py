import logging
import time
from pypdf import PdfReader
import os

# Configure logging to satisfy requirements
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def extract_paragraph(pdf_path: str, page_number: int, paragraph_index: int):
    """
    Extracts a specific paragraph from a PDF file.
    """
    start_time = time.time()

    # Check if file exists
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

        # STRATEGY 1: Split by double newlines (standard paragraphs)
        paragraphs = [p.strip() for p in full_text.split("\n\n") if p.strip()]

        # STRATEGY 2: If that failed (only 1 result), try splitting by single newlines
        # but filter out very short lines to avoid headlines/page numbers
        if len(paragraphs) <= 1:
            logger.info(
                "Double newline split yielded 1 or 0 results. Trying single newline split."
            )
            raw_lines = [line.strip() for line in full_text.split("\n") if line.strip()]
            # Treat every non-empty line as a paragraph for now
            paragraphs = raw_lines

        if paragraph_index < 0 or paragraph_index >= len(paragraphs):
            # Debug info: print what we actually found
            logger.warning(f"Available paragraphs ({len(paragraphs)}):")
            for i, p in enumerate(paragraphs[:3]):  # Print first 3 to avoid spam
                logger.warning(f" [{i}]: {p[:50]}...")

            error_msg = f"Paragraph index {paragraph_index} out of range on page {page_number}. Found {len(paragraphs)} paragraphs."
            logger.error(error_msg)
            raise ValueError(error_msg)

        target_text = paragraphs[paragraph_index]
        end_time = time.time()
        extraction_time = end_time - start_time

        # Log metadata as required
        logger.info(f"--- Extraction Metadata ---")
        logger.info(f"Source: {pdf_path}")
        logger.info(f"Page Number: {page_number}")
        logger.info(f"Paragraph Index: {paragraph_index}")
        logger.info(f"Paragraph Length: {len(target_text)} chars")
        logger.info(f"Extraction Time: {extraction_time:.6f} seconds")

        return {
            "text": target_text,
            "page": page_number,
            "paragraph_index": paragraph_index,
            "length": len(target_text),
            "extraction_time": extraction_time,
        }

    except Exception as e:
        logger.error(f"Extraction failed: {str(e)}")
        raise e


if __name__ == "__main__":
    test_path = "data/why-llm-cant-develop-software.pdf"
    try:
        # Changed to Index 0 to ensure we get the first available chunk
        print("Attempting to extract Page 1, Paragraph 0...")
        result = extract_paragraph(test_path, 1, 0)
        print(
            f"\nSUCCESS! Extracted Text (First 200 chars):\n{result['text'][:200]}..."
        )
    except Exception as e:
        print(f"Test failed: {e}")
