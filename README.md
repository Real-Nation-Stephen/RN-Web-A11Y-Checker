# Website Accessibility Checker (Streamlit)

This app crawls a website (same domain), runs accessibility checks (axe-core via Playwright),
and generates:
- an **Audit** (with Quick Wins and a **Severity** breakdown)
- an **Accessibility Statement** (Markdown)

## Quick start (Mac)

```bash
cd ~/Downloads  # or wherever you saved the zip
unzip a11y-checker.zip
cd a11y-checker
bash setup.sh
# when setup finishes:
source .venv/bin/activate
streamlit run streamlit_app.py
```

Then open http://localhost:8501 if your browser doesn't open automatically.
