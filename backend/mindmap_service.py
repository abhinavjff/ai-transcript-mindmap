import json
import os
import re
import time

from dotenv import load_dotenv
from openai import OpenAI

from logger_config import setup_logger  # Use consistent logger

load_dotenv()
logger = setup_logger(__name__)

# Configuration
base_url = os.getenv("LLM_BASE_URL", "http://ollama:11434/v1")
api_key = os.getenv("LLM_API_KEY", "ollama")
model_name = os.getenv("LLM_MODEL", "gemma3:4b")

client = OpenAI(base_url=base_url, api_key=api_key)


def clean_json_response(content):
    """Helper to extract JSON from LLM response."""
    content = re.sub(r"```json\s*", "", content)
    content = re.sub(r"```\s*$", "", content)
    return content.strip()


def generate_mindmap_json(transcript_text: str):
    """Asks LLM to convert text into a JSON topic hierarchy."""
    start_time = time.time()
    logger.info("--- Processing Step: Mind Map Generation ---")

    system_prompt = (
        "You are a helpful assistant. Analyze the provided text and extract the main topic "
        "and subtopics. Output the result strictly as a valid JSON object with this structure: "
        '{"root": "Main Topic Title", "children": [{"name": "Subtopic", "children": []}]}. '
        "Do not add any markdown formatting or explanation. Just the JSON."
    )

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcript_text},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        logger.info(f"Raw LLM Output (Snippet): {content[:50]}...")

        content = clean_json_response(content)
        mindmap_data = json.loads(content)

        logger.info(f"Mind Map Generation Time: {time.time() - start_time:.4f}s")
        return mindmap_data

    except Exception as e:
        logger.error(f"Mind Map generation failed: {e}")
        # Fallback to prevent crash
        return {
            "root": "Error Parsing Data",
            "children": [{"name": "Please try again", "children": []}],
        }


# --- NEW: Exported function for UI ---
def json_to_mermaid(mindmap_json):
    """
    Converts JSON structure to Mermaid Syntax String.
    Used by both the HTML generator and the API.
    """
    if not mindmap_json:
        return "graph TD;\nError[No Data]"

    def parse_node(node, parent_id=None, node_id=0):
        lines = []
        current_id = f"node{node_id}"

        # Sanitize label (remove quotes)
        label = node.get("name", node.get("root", "Topic")).replace('"', "'")

        if parent_id:
            lines.append(f'    {parent_id} --> {current_id}["{label}"]')
        else:
            lines.append(f'    {current_id}["{label}"]')

        counter = node_id + 1
        for child in node.get("children", []):
            child_lines, new_counter = parse_node(child, current_id, counter)
            lines.extend(child_lines)
            counter = new_counter

        return lines, counter

    lines, _ = parse_node(mindmap_json)
    return "graph TD\n" + "\n".join(lines)


def save_mindmap_html(mindmap_json, output_file="mindmap.html"):
    """
    Converts JSON to Mermaid HTML file using the helper above.
    """
    mermaid_graph = json_to_mermaid(mindmap_json)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <body>
        <h2>Mind Map Visualization</h2>
        <pre class="mermaid">
{mermaid_graph}
        </pre>
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{ startOnLoad: true }});
        </script>
    </body>
    </html>
    """

    with open(output_file, "w") as f:
        f.write(html_content)

    logger.info(f"Saved HTML to: {os.path.abspath(output_file)}")
    return output_file
