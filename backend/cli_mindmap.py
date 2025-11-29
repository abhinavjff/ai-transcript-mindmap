import argparse
import json
import logging
import os
import sys

from mindmap_service import generate_mindmap_json, save_mindmap_html
from transcript_service import process_pdf_paragraph

# Configure Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a Mind Map from a PDF paragraph."
    )
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("page", type=int, help="Page number (1-based)")
    parser.add_argument("paragraph", type=int, help="Paragraph index (0-based)")
    parser.add_argument(
        "--output",
        default="final_mindmap.html",
        help="Output filename for the mind map",
    )

    args = parser.parse_args()

    # Validation
    if not os.path.exists(args.pdf_path):
        logger.error(f"File not found: {args.pdf_path}")
        sys.exit(1)

    try:
        logger.info("=== STEP 1: Extraction & Cleaning ===")
        result = process_pdf_paragraph(args.pdf_path, args.page, args.paragraph)

        cleaned_text = result["cleaned"]
        logger.info("Transcript ready.")
        logger.info(f"Preview: {cleaned_text[:100]}...")

        # --- 1. SAVE TRANSCRIPT (The missing Deliverable #4) ---
        txt_filename = args.output.replace(".html", ".txt")
        if txt_filename == args.output:
            txt_filename += ".txt"

        with open(txt_filename, "w") as f:
            f.write(cleaned_text)
        logger.info(f"Cleaned Transcript saved to: {txt_filename}")
        # -------------------------------------------------------

        logger.info("=== STEP 2: Generating Mind Map Structure ===")
        mindmap_data = generate_mindmap_json(cleaned_text)

        # --- 2. SAVE JSON (Requirement: "JSON and at least one visual") ---
        json_filename = args.output.replace(".html", ".json")
        if json_filename == args.output:
            json_filename += ".json"

        with open(json_filename, "w") as f:
            json.dump(mindmap_data, f, indent=2)
        logger.info(f"JSON Structure saved to: {json_filename}")
        # ---------------------------------------------------------------------

        logger.info("=== STEP 3: Saving Visualization ===")
        output_path = save_mindmap_html(mindmap_data, args.output)

        print("\n" + "=" * 40)
        print("SUCCESS!")
        print(f"1. Transcript: {txt_filename}")
        print(f"2. JSON Data:  {json_filename}")
        print(f"3. Visual Map: {output_path}")
        print("=" * 40 + "\n")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
