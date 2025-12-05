# Complete Guide: Google Sheets Authentication & Streamlit Deployment

> **For Real Nation Projects**  
> A comprehensive guide to add Google Sheets login functionality to any Streamlit app and deploy it to Streamlit Cloud.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Google Sheets API Setup](#google-sheets-api-setup)
3. [Project Structure](#project-structure)
4. [Code Implementation](#code-implementation)
5. [Local Development Setup](#local-development-setup)
6. [GitHub Setup](#github-setup)
7. [Streamlit Cloud Deployment](#streamlit-cloud-deployment)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### What You Need

- Google account with access to Google Cloud Console
- GitHub account
- Streamlit Cloud account (free)
- Python 3.8+ installed locally
- Basic knowledge of Python and Streamlit

### Python Packages Required

```bash
pip install streamlit pandas gspread google-auth google-auth-oauthlib google-auth-httplib2
```

---

## Google Sheets API Setup

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Create Project"** or select existing project
3. Name it (e.g., `rn-your-app-name`)
4. Note the **Project ID**

### Step 2: Enable Google Sheets API

1. In Google Cloud Console, go to **"APIs & Services"** → **"Library"**
2. Search for **"Google Sheets API"**
3. Click **"Enable"**
4. Also enable **"Google Drive API"** (important!)

### Step 3: Create Service Account

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"Create Credentials"** → **"Service Account"**
3. Fill in details:
   - **Service account name**: `your-app-name-service`
   - **Service account ID**: (auto-generated)
   - Click **"Create and Continue"**
4. Grant role: **"Editor"** (or specific roles if needed)
5. Click **"Done"**

### Step 4: Generate Service Account Key

1. Click on the service account you just created
2. Go to **"Keys"** tab
3. Click **"Add Key"** → **"Create new key"**
4. Choose **JSON** format
5. Click **"Create"**
6. **Save this JSON file securely** - you'll need it!

### Step 5: Create Google Sheet for User Authentication

1. Create a new Google Sheet
2. Name it (e.g., "Your App Users")
3. Create a tab called **"Users"** with these columns:
   ```
   | Name | Email | Password | Role |
   ```
4. Add your users (passwords can be plain text for internal apps):
   ```
   | Kay O'Neill | kay@realnation.ie | yourpassword | admin |
   | Stephen Maguire | stephen.maguire@realnation.ie | yourpassword | user |
   ```
5. **IMPORTANT**: Share the sheet with your service account email
   - Click **"Share"** button
   - Add the service account email (found in the JSON file: `client_email`)
   - Give it **"Editor"** permissions

6. Copy the **Spreadsheet ID** from the URL:
   ```
   https://docs.google.com/spreadsheets/d/1nLOJvUut6RgfYbsSQa1ghPnJMaUWdHbbvlWqSDwwmU4/edit
                                           ^^^^ THIS IS YOUR SPREADSHEET ID ^^^^
   ```

---

## Project Structure

### Recommended File Structure

```
your-app/
├── .streamlit/
│   └── secrets.toml.example    # Example secrets (don't commit real secrets!)
├── auth/
│   └── password_sheet_api.py   # Local credentials (gitignored)
├── .gitignore
├── your_app.py                 # Main Streamlit app
├── requirements.txt
├── README.md
└── DEPLOYMENT.md
```

### Create `.gitignore`

```gitignore
# Secrets and credentials
.streamlit/secrets.toml
auth/password_sheet_api.py
*.json
*.key

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
*.egg-info/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

---

## Code Implementation

### Step 1: Create `auth/password_sheet_api.py` (Local Credentials)

**DO NOT COMMIT THIS FILE!**

```python
# auth/password_sheet_api.py
# This file contains your actual credentials for local development
# Add this file to .gitignore!

GOOGLE_SHEETS_CREDENTIALS = {
    "type": "service_account",
    "project_id": "your-project-id",
    "private_key_id": "your-private-key-id",
    "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY_HERE\n-----END PRIVATE KEY-----\n",
    "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
    "client_id": "your-client-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

SPREADSHEET_ID = "your-spreadsheet-id-here"
USERS_TAB_NAME = "Users"
```

**How to fill this in:**
1. Open the JSON key file you downloaded from Google Cloud
2. Copy each value into the corresponding field above
3. For `private_key`, keep the newlines (`\n`) in the string

### Step 2: Create `.streamlit/secrets.toml.example` (Template)

```toml
# .streamlit/secrets.toml.example
# This is a template - copy to secrets.toml and fill in your actual values
# DO NOT commit secrets.toml!

# Google Sheets Service Account Credentials
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = """-----BEGIN PRIVATE KEY-----
YOUR_PRIVATE_KEY_HERE
-----END PRIVATE KEY-----"""
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
universe_domain = "googleapis.com"

# Google Sheets Configuration
SPREADSHEET_ID = "your-spreadsheet-id"
USERS_TAB_NAME = "Users"
```

### Step 3: Implement Authentication in Your App

Add this code to your main Streamlit app:

```python
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict

class YourApp:
    def __init__(self):
        self.authenticated = False
        self.user_email = None
        self.user_name = None
        self.user_role = None
        self.sheet_client = None
        self.spreadsheet = None
        self.load_credentials()
    
    def load_credentials(self):
        """Load Google Sheets API credentials from Streamlit secrets or local file"""
        self.credentials = None
        self.spreadsheet_id = None
        self.users_tab = 'Users'
        
        try:
            # Try Streamlit secrets first (for cloud deployment)
            if hasattr(st, 'secrets'):
                if 'project_id' in st.secrets and 'client_email' in st.secrets:
                    print("✅ Loading credentials from Streamlit secrets...")
                    self.credentials = {
                        "type": st.secrets.get("type", "service_account"),
                        "project_id": st.secrets.get("project_id", ""),
                        "private_key_id": st.secrets.get("private_key_id", ""),
                        "private_key": st.secrets.get("private_key", ""),
                        "client_email": st.secrets.get("client_email", ""),
                        "client_id": st.secrets.get("client_id", ""),
                        "auth_uri": st.secrets.get("auth_uri", "https://accounts.google.com/o/oauth2/auth"),
                        "token_uri": st.secrets.get("token_uri", "https://oauth2.googleapis.com/token"),
                        "auth_provider_x509_cert_url": st.secrets.get("auth_provider_x509_cert_url", "https://www.googleapis.com/oauth2/v1/certs"),
                        "client_x509_cert_url": st.secrets.get("client_x509_cert_url", ""),
                        "universe_domain": st.secrets.get("universe_domain", "googleapis.com")
                    }
                    self.spreadsheet_id = st.secrets.get("SPREADSHEET_ID", "")
                    self.users_tab = st.secrets.get("USERS_TAB_NAME", "Users")
                    return
        except Exception as e:
            print(f"⚠️ Failed to load from Streamlit secrets: {str(e)}")
        
        try:
            # Fall back to local file (for local development)
            print("✅ Loading credentials from auth/password_sheet_api.py...")
            from auth.password_sheet_api import (
                GOOGLE_SHEETS_CREDENTIALS, 
                SPREADSHEET_ID,
                USERS_TAB_NAME
            )
            self.credentials = GOOGLE_SHEETS_CREDENTIALS
            self.spreadsheet_id = SPREADSHEET_ID
            self.users_tab = USERS_TAB_NAME
        except ImportError:
            print("⚠️ Authentication credentials not found. Using demo mode.")
            self.credentials = None
            self.spreadsheet_id = None
    
    def connect_to_sheets(self):
        """Connect to Google Sheets"""
        if hasattr(self, 'sheet_client') and self.sheet_client and self.spreadsheet:
            return True
        
        try:
            if not self.credentials or not self.spreadsheet_id:
                print("⚠️ No credentials found")
                return False
            
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = Credentials.from_service_account_info(self.credentials, scopes=scopes)
            self.sheet_client = gspread.authorize(creds)
            self.spreadsheet = self.sheet_client.open_by_key(self.spreadsheet_id)
            
            print(f"✅ Connected to Google Sheets: {self.spreadsheet.title}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {str(e)}")
            return False
    
    def get_users_from_sheet(self) -> List[Dict]:
        """Get users from Google Sheets Users tab"""
        if hasattr(self, '_cached_users') and self._cached_users:
            return self._cached_users
        
        try:
            if not self.connect_to_sheets():
                # Fallback demo users
                print("⚠️ Using demo mode")
                return [
                    {"name": "Demo User", "email": "demo@example.com", "role": "admin", "password": "demo"}
                ]
            
            # Get Users worksheet
            try:
                users_ws = self.spreadsheet.worksheet(self.users_tab)
            except gspread.WorksheetNotFound:
                print(f"❌ '{self.users_tab}' tab not found")
                return []
            
            # Get all records
            records = users_ws.get_all_records()
            
            # Convert to user list
            users = []
            for record in records:
                user = {
                    "name": str(record.get('Name', '')).strip(),
                    "email": str(record.get('Email', '')).strip().lower(),
                    "password": str(record.get('Password', '')).strip(),
                    "role": str(record.get('Role', 'user')).strip().lower()
                }
                if user['name'] and user['email']:
                    users.append(user)
            
            self._cached_users = users
            print(f"✅ Loaded {len(users)} users from Google Sheets")
            return users
            
        except Exception as e:
            print(f"❌ Error loading users: {str(e)}")
            return []
    
    def authenticate(self, email: str, password: str) -> bool:
        """Authenticate user with email and password"""
        users = self.get_users_from_sheet()
        
        email = email.strip().lower()
        password = password.strip()
        
        for user in users:
            if user['email'] == email and user['password'] == password:
                self.authenticated = True
                self.user_email = user['email']
                self.user_name = user['name']
                self.user_role = user['role']
                print(f"✅ User authenticated: {self.user_name}")
                return True
        
        print(f"❌ Authentication failed for: {email}")
        return False

def show_login_page(app):
    """Display login page"""
    st.markdown('<h1 style="text-align: center;">🔐 Login Required</h1>', unsafe_allow_html=True)
    
    # Get users for dropdown
    users = app.get_users_from_sheet()
    
    if not users:
        st.error("❌ No users found. Please check your Google Sheets configuration.")
        return
    
    user_names = [user['name'] for user in users]
    
    # Login form
    with st.container():
        st.markdown("### Please select your name and enter your password")
        
        selected_user = st.selectbox("Select your name", options=user_names)
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", type="primary", use_container_width=True):
            # Find selected user's email
            selected_email = None
            for user in users:
                if user['name'] == selected_user:
                    selected_email = user['email']
                    break
            
            if selected_email and app.authenticate(selected_email, password):
                st.session_state.authenticated_user = {
                    'email': app.user_email,
                    'name': app.user_name,
                    'role': app.user_role
                }
                st.success(f"✅ Welcome, {app.user_name}!")
                st.rerun()
            else:
                st.error("❌ Invalid password. Please try again.")

def main():
    # Initialize session state
    if 'authenticated_user' not in st.session_state:
        st.session_state.authenticated_user = None
    
    # Create app instance
    if 'app_instance' not in st.session_state:
        st.session_state.app_instance = YourApp()
    
    app = st.session_state.app_instance
    
    # Force reload credentials if missing
    if not app.credentials:
        app.load_credentials()
    
    # Check authentication
    if not st.session_state.authenticated_user:
        show_login_page(app)
        return
    
    # Load user from session
    user = st.session_state.authenticated_user
    app.user_email = user['email']
    app.user_name = user['name']
    app.user_role = user['role']
    app.authenticated = True
    
    # Your main app content goes here
    st.title(f"Welcome, {app.user_name}! 👋")
    st.write("Your authenticated app content goes here...")
    
    # Logout button
    if st.sidebar.button("🚪 Logout"):
        st.session_state.authenticated_user = None
        st.rerun()

if __name__ == "__main__":
    main()
```

### Step 4: Create `requirements.txt`

```txt
streamlit>=1.28.0
pandas>=2.0.0
gspread>=5.11.0
google-auth>=2.23.0
google-auth-oauthlib>=1.1.0
google-auth-httplib2>=0.1.1
```

---

## Local Development Setup

### Step 1: Set Up Your Environment

```bash
# Clone or create your project
cd your-app

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Add Your Credentials

1. Create `auth/` folder
2. Create `auth/password_sheet_api.py` with your actual credentials (see code above)
3. Verify `.gitignore` excludes this file

### Step 3: Test Locally

```bash
streamlit run your_app.py
```

**What to check:**
- ✅ App loads without errors
- ✅ Login page displays with users from Google Sheet
- ✅ Can log in successfully
- ✅ Check terminal for connection messages

---

## GitHub Setup

### Step 1: Initialize Git Repository

```bash
git init
git add .
git commit -m "Initial commit"
```

### Step 2: Create GitHub Repository

1. Go to [github.com](https://github.com)
2. Click **"New repository"**
3. Name it (e.g., `your-app-name`)
4. Don't initialize with README (you already have files)
5. Click **"Create repository"**

### Step 3: Push to GitHub

```bash
git remote add origin https://github.com/YourUsername/your-app-name.git
git branch -M main
git push -u origin main
```

### Step 4: Verify

**CRITICAL CHECK:** Make sure these are **NOT** in your repo:
- ❌ `auth/password_sheet_api.py`
- ❌ `.streamlit/secrets.toml`
- ❌ Any `.json` key files

If they are, **remove them immediately**:
```bash
git rm --cached auth/password_sheet_api.py
git commit -m "Remove sensitive files"
git push
```

---

## Streamlit Cloud Deployment

### Step 1: Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io/)
2. Click **"New app"**
3. Connect your GitHub account (if not already)
4. Select:
   - **Repository**: `YourUsername/your-app-name`
   - **Branch**: `main`
   - **Main file path**: `your_app.py`
5. Click **"Deploy"**

The app will start deploying but **won't work yet** - you need to add secrets!

### Step 2: Add Secrets to Streamlit Cloud

**CRITICAL STEP - App won't work without this!**

1. In Streamlit Cloud dashboard, find your app
2. Click **⋮** (three dots) → **"Settings"**
3. Go to **"Secrets"** section
4. Copy and paste your credentials in **TOML format**:

```toml
# Google Sheets Service Account Credentials
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = """-----BEGIN PRIVATE KEY-----
YOUR_ACTUAL_PRIVATE_KEY_HERE
-----END PRIVATE KEY-----"""
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
universe_domain = "googleapis.com"

# Google Sheets Configuration
SPREADSHEET_ID = "your-spreadsheet-id"
USERS_TAB_NAME = "Users"
```

5. Click **"Save"**
6. App will automatically restart (~30 seconds)

### Step 3: Test Your Deployed App

1. Open your app URL (e.g., `https://your-app-name.streamlit.app`)
2. Verify:
   - ✅ Login page loads
   - ✅ Users from Google Sheet appear
   - ✅ Can log in successfully
   - ✅ No "demo mode" warnings

---

## Troubleshooting

### Problem: "Using demo mode" Warning

**Causes:**
1. Secrets not configured in Streamlit Cloud
2. Secrets formatted incorrectly (TOML syntax error)
3. Google Sheet not shared with service account

**Solutions:**
1. Go to Streamlit Cloud → Settings → Secrets and verify they're saved
2. Check for syntax errors in secrets (especially the `private_key` triple quotes)
3. In Google Sheets, click Share and add your service account email

### Problem: "Spreadsheet not found" Error

**Causes:**
1. Wrong Spreadsheet ID in secrets
2. Google Sheet not shared with service account
3. Google Drive API not enabled

**Solutions:**
1. Double-check Spreadsheet ID from URL
2. Share sheet with service account email (from `client_email` in credentials)
3. Enable Google Drive API in Google Cloud Console

### Problem: "Failed to load credentials"

**Causes:**
1. Local `auth/password_sheet_api.py` missing
2. Secrets not in Streamlit Cloud
3. Import error in code

**Solutions:**
1. Create the `auth/password_sheet_api.py` file with your credentials
2. Add secrets to Streamlit Cloud
3. Check terminal/logs for specific error messages

### Problem: "Authentication failed" for Valid Users

**Causes:**
1. Password mismatch (check for extra spaces)
2. Email case sensitivity
3. Google Sheet column names wrong

**Solutions:**
1. Check password in Google Sheet (no extra spaces)
2. Code converts email to lowercase - make sure Sheet has lowercase emails
3. Ensure column names are exactly: `Name`, `Email`, `Password`, `Role`

### Problem: App Works Locally but Not in Cloud

**Causes:**
1. Secrets not added to Streamlit Cloud
2. Dependencies missing from `requirements.txt`
3. File paths are different

**Solutions:**
1. Add secrets to Streamlit Cloud (most common issue!)
2. Add all imports to `requirements.txt`
3. Use relative paths, not absolute paths

### Problem: Changes Not Showing After Push

**Causes:**
1. Streamlit Cloud hasn't pulled latest commit
2. Browser cache

**Solutions:**
1. Manually reboot app: Settings → Reboot app
2. Hard refresh browser: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
3. Wait 2-3 minutes for auto-update

---

## Security Best Practices

### ✅ DO:
- Use `.gitignore` to exclude sensitive files
- Store credentials in Streamlit secrets for cloud deployment
- Use service account email (not your personal email)
- Limit service account permissions to only what's needed
- Rotate credentials if they're ever exposed
- Use strong passwords in Google Sheet

### ❌ DON'T:
- Commit credentials to GitHub
- Share credentials in Slack/email
- Use production credentials for testing
- Give service account more permissions than needed
- Store passwords in plain text in production (this is OK for internal apps only)

---

## Quick Reference: Common Commands

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run app locally
streamlit run your_app.py

# Check for uncommitted secrets
git status
```

### Git & GitHub
```bash
# Check status
git status

# Add all changes
git add .

# Commit changes
git commit -m "Your message"

# Push to GitHub
git push origin main

# View recent commits
git log --oneline -5
```

### Streamlit Cloud
- **Deploy new app**: [share.streamlit.io](https://share.streamlit.io/) → New app
- **Update secrets**: App → ⋮ → Settings → Secrets → Save
- **Reboot app**: App → ⋮ → Reboot app
- **View logs**: App → ⋮ → Manage app → Logs

---

## Complete Checklist for New Project

### Initial Setup
- [ ] Create Google Cloud project
- [ ] Enable Google Sheets API and Google Drive API
- [ ] Create service account and download JSON key
- [ ] Create Google Sheet with Users tab
- [ ] Share sheet with service account email
- [ ] Copy Spreadsheet ID from URL

### Code Setup
- [ ] Create project structure
- [ ] Add `.gitignore` file
- [ ] Create `auth/password_sheet_api.py` with credentials
- [ ] Create `.streamlit/secrets.toml.example` template
- [ ] Implement authentication code in main app
- [ ] Create `requirements.txt`
- [ ] Test locally

### GitHub
- [ ] Initialize git repository
- [ ] Create GitHub repository
- [ ] Push code to GitHub
- [ ] Verify sensitive files are NOT in repo

### Streamlit Cloud
- [ ] Deploy app on share.streamlit.io
- [ ] Add secrets to Streamlit Cloud
- [ ] Reboot app
- [ ] Test deployed app
- [ ] Verify authentication works

### Final Verification
- [ ] Can log in with real users
- [ ] No "demo mode" warnings
- [ ] Google Sheets connection working
- [ ] All features work in cloud
- [ ] No credentials in GitHub

---

## Support & Resources

### Documentation
- [Streamlit Docs](https://docs.streamlit.io/)
- [gspread Documentation](https://docs.gspread.org/)
- [Google Sheets API](https://developers.google.com/sheets/api)

### Real Nation Contacts
- **Technical Issues**: Stephen Maguire (stephen.maguire@realnation.ie)
- **Access Issues**: Kay O'Neill (kay@realnation.ie)

---

## Example Projects

### Working Examples
1. **RN Time Tracker** - https://github.com/Real-Nation-Stephen/RN-Time-Tracker
   - Full authentication implementation
   - Multiple Google Sheets tabs
   - Role-based access

### Reusable Code
- Copy authentication code from RN Time Tracker
- Adapt `load_credentials()` function
- Reuse login UI components

---

**Created by**: Real Nation Development Team  
**Last Updated**: December 2025  
**Version**: 1.0

---

## Need Help?

If you get stuck:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review the [Complete Checklist](#complete-checklist-for-new-project)
3. Look at RN Time Tracker code for reference
4. Contact Stephen for technical assistance

**Good luck with your deployment! 🚀**

