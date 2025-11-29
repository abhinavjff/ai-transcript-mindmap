import os
import sys
import unittest

# Add backend to path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from mindmap_service import save_mindmap_html
from pdf_extractor import extract_paragraph


class TestMindMapFeature(unittest.TestCase):

    def setUp(self):
        # Create a dummy PDF path for reference (we won't actually parse a real PDF in unit tests
        # unless we mock it, but we can test the failure logic)
        self.dummy_path = "non_existent_file.pdf"
        self.output_html = "test_output.html"

    def tearDown(self):
        # Clean up generated files
        if os.path.exists(self.output_html):
            os.remove(self.output_html)

    def test_pdf_extractor_file_not_found(self):
        """Test that extractor raises error for missing file"""
        with self.assertRaises(FileNotFoundError):
            extract_paragraph(self.dummy_path, 1, 0)

    def test_html_generation(self):
        """Test that HTML is generated from valid JSON"""
        dummy_json = {
            "root": "Test Topic",
            "children": [
                {"name": "Subtopic A", "children": []},
                {"name": "Subtopic B", "children": []},
            ],
        }

        # Run the generator
        save_mindmap_html(dummy_json, self.output_html)

        # Check if file was created
        self.assertTrue(os.path.exists(self.output_html))

        # Check content
        with open(self.output_html) as f:
            content = f.read()
            self.assertIn("mermaid", content)
            self.assertIn("Test Topic", content)
            self.assertIn("Subtopic A", content)


if __name__ == "__main__":
    unittest.main()
