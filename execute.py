import os
import sys

# 1. Add the 'backend' folder to Python's path
# This allows us to import modules that live inside the backend/ directory
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

# 2. Import the main function from your CLI tool
from cli_mindmap import main

# 3. Run the application
if __name__ == "__main__":
    print("--- Executing Mind Map Generator ---")
    main()
