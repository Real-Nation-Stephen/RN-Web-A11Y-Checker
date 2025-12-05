"""
Playwright browser installation helper
Automatically installs browsers if not present (for Streamlit Cloud)
"""
import subprocess
import sys
import os

def ensure_playwright_browsers():
    """Ensure Playwright browsers are installed"""
    try:
        from playwright.sync_api import sync_playwright
        
        # Try to launch to see if browsers are installed
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
                browser.close()
                print("✅ Playwright browsers are already installed")
                return True
            except Exception:
                # Browsers not installed, try to install
                print("🔧 Playwright browsers not found. Installing...")
                return install_playwright_browsers()
    except ImportError:
        print("⚠️ Playwright not installed")
        return False
    except Exception as e:
        print(f"⚠️ Error checking Playwright: {e}")
        return False

def install_playwright_browsers():
    """Install Playwright browsers"""
    try:
        print("📦 Installing Playwright Chromium browser...")
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        print("✅ Playwright browsers installed successfully")
        print(result.stdout)
        return True
    except subprocess.TimeoutExpired:
        print("❌ Browser installation timed out")
        return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing browsers: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

# Auto-install on import (only in Streamlit Cloud environment)
if os.getenv("STREAMLIT_SERVER_PORT") or os.getenv("STREAMLIT_SHARE"):
    # We're in Streamlit Cloud, try to install browsers
    # But do it lazily to avoid blocking app startup
    _browsers_installed = None
    
    def check_and_install():
        global _browsers_installed
        if _browsers_installed is None:
            _browsers_installed = ensure_playwright_browsers()
        return _browsers_installed

