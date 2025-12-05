#!/usr/bin/env python3
"""Install Playwright browsers for Streamlit Cloud deployment"""
import subprocess
import sys

if __name__ == "__main__":
    print("🔧 Installing Playwright browsers...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ Playwright browsers installed successfully")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing browsers: {e}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)

