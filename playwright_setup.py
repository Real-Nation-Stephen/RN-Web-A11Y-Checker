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
        import streamlit as st
        st.info("📦 Installing Playwright Chromium browser... This may take a few minutes.")
    except:
        print("📦 Installing Playwright Chromium browser...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        output = result.stdout
        if output:
            print(output)
            try:
                import streamlit as st
                st.text(output)
            except:
                pass
        return True
    except subprocess.TimeoutExpired:
        error_msg = "❌ Browser installation timed out (took longer than 10 minutes)"
        print(error_msg)
        try:
            import streamlit as st
            st.error(error_msg)
        except:
            pass
        return False
    except subprocess.CalledProcessError as e:
        error_msg = f"❌ Error installing browsers: {e.stderr or e.stdout or str(e)}"
        print(error_msg)
        try:
            import streamlit as st
            st.error(error_msg)
            if e.stderr:
                st.code(e.stderr, language="text")
        except:
            pass
        return False
    except Exception as e:
        error_msg = f"❌ Unexpected error: {e}"
        print(error_msg)
        try:
            import streamlit as st
            st.error(error_msg)
        except:
            pass
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

