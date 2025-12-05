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
playwright install-deps  # Install system dependencies (Linux)
```

**For Streamlit Cloud Deployment:**
1. **Browser binaries** are installed via the app's installation button
2. **System dependencies** are installed via `packages.txt` (automatically on deployment)
3. If you see "missing dependencies" errors:
   - The `packages.txt` file should handle this automatically
   - Redeploy the app to trigger system package installation
   - Check that `packages.txt` is in the repository

**Common Issues:**
- "Browsers not found" → Click "Install Browsers" button in sidebar
- "Missing dependencies" → System libraries needed, should install via `packages.txt` on next deployment
- "Permission denied" → Streamlit Cloud limitation, contact support

See `PLAYWRIGHT_SETUP.md` for more details.
