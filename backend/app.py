import os
import sys

# Ensure root directory is on sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import create_app

app = create_app()

if __name__ == "__main__":
    print("===============================================================")
    print("  SignAI — AI-Powered Multilingual Sign Language System")
    print("  Server running at: http://127.0.0.1:5000")
    print("  Open this URL in your web browser to access the dashboard.")
    print("===============================================================")
    app.run(host="127.0.0.1", port=5000, debug=False)
