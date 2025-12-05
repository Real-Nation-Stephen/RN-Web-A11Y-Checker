"""
Playwright browser installation helper
Automatically installs browsers if not present (for Streamlit Cloud)
"""
import subprocess
import sys
import os

def check_browsers_installed():
    """Check if Playwright browsers are installed (sync version for Streamlit)"""
    try:
        import asyncio
        from playwright.async_api import async_playwright
        
        # Check if we're in an async context
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context, can't use sync API
            # Instead, check if browser executable exists
            return _check_browser_executable()
        except RuntimeError:
            # No running loop, safe to use sync API
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                try:
                    browser = p.chromium.launch(headless=True)
                    browser.close()
                    return True, "✅ Browsers are installed and ready"
                except Exception as e:
                    error_msg = str(e).lower()
                    error_str = str(e)
                    
                    # Check for missing system dependencies
                    if "missing dependencies" in error_msg or "install-deps" in error_msg:
                        return False, f"⚠️ System dependencies missing: Browsers installed but system libraries needed. See packages.txt"
                    elif any(keyword in error_msg for keyword in ["executable", "browser", "not found", "doesn't exist"]):
                        return False, f"❌ Browsers not found: {error_str[:200]}"
                    else:
                        return False, f"⚠️ Browser launch error: {error_str[:200]}"
    except ImportError:
        return False, "⚠️ Playwright not installed"
    except Exception as e:
        error_str = str(e)
        # If it's the async/sync API error, use executable check instead
        if "asyncio loop" in error_str.lower() or "async" in error_str.lower():
            return _check_browser_executable()
        return False, f"⚠️ Error checking: {error_str[:200]}"

def _check_browser_executable():
    """Check if browser executable exists without launching"""
    try:
        import os
        from pathlib import Path
        
        # Try to find Playwright browser executable
        # Common locations
        possible_paths = [
            os.path.expanduser("~/.cache/ms-playwright/chromium-*/chrome-linux/chrome"),
            os.path.expanduser("~/.cache/ms-playwright/chromium-*/chrome"),
            "/root/.cache/ms-playwright/chromium-*/chrome-linux/chrome",
        ]
        
        import glob
        for pattern in possible_paths:
            matches = glob.glob(pattern)
            if matches:
                exe_path = matches[0]
                if os.path.exists(exe_path) and os.access(exe_path, os.X_OK):
                    return True, "✅ Browser executable found (system deps may still be needed)"
        
        # If we can't find it, assume browsers might be installed but we can't verify
        # This is better than failing completely
        return False, "⚠️ Cannot verify browser installation (check may be unreliable)"
    except Exception as e:
        return False, f"⚠️ Error checking executable: {str(e)[:200]}"

def ensure_playwright_browsers():
    """Ensure Playwright browsers are installed"""
    is_installed, message = check_browsers_installed()
    if is_installed:
        print(message)
        return True
    else:
        print(f"🔧 {message}. Attempting installation...")
        return install_playwright_browsers()

def install_playwright_browsers():
    """Install Playwright browsers"""
    st = None
    try:
        import streamlit as st
    except:
        pass
    
    if st:
        st.info("📦 Installing Playwright Chromium browser... This may take a few minutes.")
        progress_bar = st.progress(0)
        status_text = st.empty()
    else:
        print("📦 Installing Playwright Chromium browser...")
        progress_bar = None
        status_text = None
    
    try:
        if status_text:
            status_text.text("Running: playwright install chromium")
        if progress_bar:
            progress_bar.progress(10)
        
        # Run the installation
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=False,  # Don't raise on error, we'll check returncode
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if progress_bar:
            progress_bar.progress(90)
        
        # Check if installation succeeded
        if result.returncode == 0:
            output = result.stdout or "Installation completed"
            print(f"✅ Installation successful: {output}")
            if st:
                if progress_bar:
                    progress_bar.progress(100)
                if status_text:
                    status_text.text("✅ Installation complete!")
                st.success("✅ Browsers installed successfully!")
                if output and len(output.strip()) > 0:
                    with st.expander("Installation output"):
                        st.code(output, language="text")
            
            # Verify installation worked (but don't fail if verification has issues)
            if progress_bar:
                progress_bar.progress(95)
            if status_text:
                status_text.text("Verifying installation...")
            
            try:
                is_installed, verify_msg = check_browsers_installed()
                if is_installed:
                    if progress_bar:
                        progress_bar.progress(100)
                    if status_text:
                        status_text.text("✅ Verified: Browsers are ready!")
                    return True
                else:
                    if st:
                        # Installation succeeded, verification had issues - still return True
                        # The actual scan will test if it really works
                        st.info(f"ℹ️ Installation completed. Verification note: {verify_msg}")
                        st.info("💡 Try running a scan to test if browsers work.")
                    # Return True anyway since installation succeeded
                    # The real test will be when we try to use it
                    return True
            except Exception as verify_error:
                # Verification failed but installation succeeded
                if st:
                    st.warning(f"⚠️ Installation completed but verification had issues: {str(verify_error)}")
                    st.info("💡 Installation succeeded - try running a scan to test.")
                # Still return True since installation command succeeded
                return True
        else:
            # Installation failed
            error_output = result.stderr or result.stdout or "Unknown error"
            error_msg = f"❌ Installation failed (exit code {result.returncode})"
            print(f"{error_msg}: {error_output}")
            
            if st:
                st.error(error_msg)
                with st.expander("Error details", expanded=True):
                    st.code(error_output, language="text")
                
                # Check if it's a permission issue
                if "permission" in error_output.lower() or "denied" in error_output.lower():
                    st.warning("""
                    **Permission Error Detected**
                    
                    Streamlit Cloud may not allow subprocess calls or file system writes.
                    This is a known limitation. Options:
                    1. Contact Streamlit support
                    2. Use a different hosting platform (Railway, Render, etc.)
                    3. Run the app locally
                    """)
                elif "timeout" in error_output.lower():
                    st.warning("Installation timed out. The process may have been killed.")
                else:
                    st.info("💡 This might be a Streamlit Cloud limitation. Check the error details above.")
            
            return False
            
    except subprocess.TimeoutExpired:
        error_msg = "❌ Browser installation timed out (took longer than 10 minutes)"
        print(error_msg)
        if st:
            st.error(error_msg)
            st.warning("The installation process was killed due to timeout.")
        return False
    except Exception as e:
        error_msg = f"❌ Unexpected error during installation: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        if st:
            st.error(error_msg)
            with st.expander("Full error details"):
                st.code(traceback.format_exc(), language="python")
        return False
    finally:
        if progress_bar:
            progress_bar.empty()
        if status_text:
            status_text.empty()

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

