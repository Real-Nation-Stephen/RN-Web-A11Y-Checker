# Playwright Browser Installation for Streamlit Cloud

## Problem

Playwright requires browser binaries to be installed separately. In Streamlit Cloud, these browsers are not automatically installed, causing errors when trying to launch Chromium.

## Solution Options

### Option 1: Use Streamlit Cloud Advanced Settings (Recommended)

1. Go to your Streamlit Cloud app settings
2. Navigate to **Advanced settings**
3. Add a **Post-install command**:
   ```bash
   playwright install chromium
   ```

### Option 2: Create a Setup Script

Create a file called `setup_playwright.py`:

```python
#!/usr/bin/env python3
"""Install Playwright browsers for Streamlit Cloud"""
import subprocess
import sys

if __name__ == "__main__":
    print("Installing Playwright browsers...")
    result = subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        check=True
    )
    print("✅ Playwright browsers installed successfully")
```

Then in Streamlit Cloud settings, add as post-install command:
```bash
python setup_playwright.py
```

### Option 3: Manual Installation (Not Recommended)

If the above don't work, you may need to contact Streamlit support to add browser installation to your deployment.

## Current Error Handling

The app now includes error handling that will:
- Detect when browsers are not installed
- Show a clear error message to users
- Provide instructions for fixing the issue

## Testing Locally

To test locally, make sure browsers are installed:

```bash
playwright install chromium
```

## Verification

After deployment, check the logs to see if browsers were installed successfully. Look for:
- ✅ "Playwright browsers installed successfully"
- ❌ Any errors about missing executables

