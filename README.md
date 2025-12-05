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

## ⚠️ Important: Playwright Browsers

**For Local Development:**
The setup script automatically installs Playwright browsers. If you encounter browser errors, run:
```bash
playwright install chromium
```

**For Streamlit Cloud Deployment:**
Playwright browsers must be installed during deployment. Streamlit Cloud has limitations with browser installation. If you see browser errors:
1. Check the app logs for installation attempts
2. Contact Streamlit support about browser installation
3. Consider using a different hosting platform that supports Playwright

See `PLAYWRIGHT_SETUP.md` for more details.
