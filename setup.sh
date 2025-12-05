#!/bin/bash
set -e
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
playwright install chromium
echo "✅ Setup complete. To run: source .venv/bin/activate && streamlit run streamlit_app.py"
