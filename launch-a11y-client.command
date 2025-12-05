#!/bin/zsh
cd ~/Documents/a11y-checker

# activate the new virtual environment
source .venv/bin/activate

# use Streamlit from the new venv
./.venv/bin/streamlit run streamlit_app_client.py --server.port 8501


