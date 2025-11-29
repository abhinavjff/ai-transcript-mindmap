import logging
import time
import json
import os
import re
from openai import OpenAI
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
base_url = os.getenv("LLM_BASE_URL", "http://ollama:11434/v1")
api_key = os.getenv("LLM_API_KEY", "ollama")
model_name = os.getenv("LLM_MODEL", "gemma3:4b")

client = OpenAI(base_url=base_url, api_key=api_key)


def clean_json_response(content):
    """
    Helper to extract JSON from LLM response if it includes markdown blocks.
    """
    # Remove markdown code blocks if present
    content = re.sub(r"```json\s*", "", content)
    content = re.sub(r"```\s*$", "", content)
    return content.strip()


def generate_mindmap_json(transcript_text: str):
    """
    Asks LLM to convert text into a JSON topic hierarchy.
    """
    start_time = time.time()
    logger.info("--- Processing Step: Mind Map Generation ---")

    # System prompt to enforce strict JSON output
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
            response_format={"type": "json_object"},  # Forces JSON mode if supported
        )

        content = response.choices[0].message.content
        logger.info(f"Raw LLM Output (Snippet): {content[:100]}...")

        # Clean and Parse JSON
        content = clean_json_response(content)
        mindmap_data = json.loads(content)

        end_time = time.time()
        logger.info(f"Mind Map Generation Time: {end_time - start_time:.4f}s")

        return mindmap_data

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from LLM: {e}")
        logger.error(f"Bad Content: {content}")
        # Return a fallback error node so the app doesn't crash
        return {
            "root": "Error Parsing JSON",
            "children": [{"name": "Raw Text", "children": []}],
        }
    except Exception as e:
        logger.error(f"Mind Map generation failed: {e}")
        raise e


def save_mindmap_html(mindmap_json, output_file="mindmap.html"):
    """
    Converts JSON to a Mermaid graph and saves as HTML.
    """

    def json_to_mermaid(node, parent_id=None, node_id=0):
        lines = []
        current_id = f"node{node_id}"

        # Sanitize label (remove quotes)
        label = node.get("name", node.get("root", "Topic")).replace('"', "'")

        if parent_id:
            lines.append(f'    {parent_id} --> {current_id}["{label}"]')
        else:
            lines.append(f'    {current_id}["{label}"]')

        child_id_counter = node_id + 1
        for child in node.get("children", []):
            child_lines, next_id = json_to_mermaid(child, current_id, child_id_counter)
            lines.extend(child_lines)
            child_id_counter = next_id

        return lines, child_id_counter

    mermaid_lines, _ = json_to_mermaid(mindmap_json)
    mermaid_graph = "graph TD\n" + "\n".join(mermaid_lines)

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

    logger.info(f"--- Visualization Saved ---")
    logger.info(f"Saved to: {os.path.abspath(output_file)}")
    return output_file


if __name__ == "__main__":
    # Test data (simulating a good transcript paragraph)
    test_transcript = (
        "Software engineering requires models that can do more than just generate code. "
        "When a person runs into a problem, they are able to temporarily stash the full context, "
        "focus on resolving the issue, and then pop their mental stack to get back to the problem in hand."
    )

    print("Generating Mind Map...")
    data = generate_mindmap_json(test_transcript)
    save_mindmap_html(data, "test_mindmap.html")
    print("Done! Check test_mindmap.html")
