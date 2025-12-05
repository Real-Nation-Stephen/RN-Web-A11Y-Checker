# auth/auth_module.py
# Shared authentication module for Streamlit apps

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict, Optional


class AuthManager:
    """Manages Google Sheets-based authentication"""
    
    def __init__(self):
        self.authenticated = False
        self.user_email = None
        self.user_name = None
        self.user_role = None
        self.sheet_client = None
        self.spreadsheet = None
        self.credentials = None
        self.spreadsheet_id = None
        self.users_tab = 'Users'
        self._cached_users = None
        self.load_credentials()
    
    def load_credentials(self):
        """Load Google Sheets API credentials from Streamlit secrets or local file"""
        self.credentials = None
        self.spreadsheet_id = None
        self.users_tab = 'Users'
        
        try:
            # Try Streamlit secrets first (for cloud deployment)
            if hasattr(st, 'secrets') and st.secrets:
                # Check if secrets exist - try different ways to access them
                secrets_dict = dict(st.secrets) if hasattr(st.secrets, '__iter__') else {}
                
                # Debug: show what keys are available
                available_keys = list(secrets_dict.keys()) if secrets_dict else []
                print(f"🔍 Available secret keys: {available_keys}")
                
                # Check for required fields
                has_project_id = 'project_id' in secrets_dict
                has_client_email = 'client_email' in secrets_dict
                has_spreadsheet_id = 'SPREADSHEET_ID' in secrets_dict
                
                print(f"🔍 Has project_id: {has_project_id}, Has client_email: {has_client_email}, Has SPREADSHEET_ID: {has_spreadsheet_id}")
                
                if has_project_id and has_client_email:
                    print("✅ Loading credentials from Streamlit secrets...")
                    
                    # Get private key - handle both string and multi-line formats
                    private_key = secrets_dict.get("private_key", "")
                    if private_key and not private_key.startswith("-----BEGIN"):
                        # If it's stored without newlines, try to reconstruct
                        print("⚠️ Private key format may need adjustment")
                    
                    self.credentials = {
                        "type": secrets_dict.get("type", "service_account"),
                        "project_id": secrets_dict.get("project_id", ""),
                        "private_key_id": secrets_dict.get("private_key_id", ""),
                        "private_key": private_key,
                        "client_email": secrets_dict.get("client_email", ""),
                        "client_id": secrets_dict.get("client_id", ""),
                        "auth_uri": secrets_dict.get("auth_uri", "https://accounts.google.com/o/oauth2/auth"),
                        "token_uri": secrets_dict.get("token_uri", "https://oauth2.googleapis.com/token"),
                        "auth_provider_x509_cert_url": secrets_dict.get("auth_provider_x509_cert_url", "https://www.googleapis.com/oauth2/v1/certs"),
                        "client_x509_cert_url": secrets_dict.get("client_x509_cert_url", ""),
                        "universe_domain": secrets_dict.get("universe_domain", "googleapis.com")
                    }
                    self.spreadsheet_id = secrets_dict.get("SPREADSHEET_ID", "")
                    self.users_tab = secrets_dict.get("USERS_TAB_NAME", "Users")
                    
                    # Validate we have essential fields
                    if not self.spreadsheet_id:
                        print("⚠️ WARNING: SPREADSHEET_ID not found in secrets!")
                    if not self.credentials.get("private_key"):
                        print("⚠️ WARNING: private_key not found in secrets!")
                    if not self.credentials.get("client_email"):
                        print("⚠️ WARNING: client_email not found in secrets!")
                    
                    if self.spreadsheet_id and self.credentials.get("private_key") and self.credentials.get("client_email"):
                        print(f"✅ Credentials loaded successfully. Spreadsheet ID: {self.spreadsheet_id[:10]}...")
                        return
                    else:
                        print("❌ Credentials incomplete, falling back to local file...")
                else:
                    print(f"⚠️ Required secrets not found. Looking for: project_id, client_email")
        except Exception as e:
            print(f"⚠️ Failed to load from Streamlit secrets: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
        
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
                print(f"   - Has credentials dict: {self.credentials is not None}")
                print(f"   - Has spreadsheet_id: {self.spreadsheet_id is not None and self.spreadsheet_id != ''}")
                return False
            
            # Validate credentials structure
            required_fields = ["type", "project_id", "private_key", "client_email"]
            missing_fields = [f for f in required_fields if not self.credentials.get(f)]
            if missing_fields:
                print(f"❌ Missing required credential fields: {missing_fields}")
                return False
            
            print(f"🔗 Connecting to Google Sheets...")
            print(f"   - Project ID: {self.credentials.get('project_id')}")
            print(f"   - Client Email: {self.credentials.get('client_email')}")
            print(f"   - Spreadsheet ID: {self.spreadsheet_id}")
            
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
            print(f"❌ Failed to connect to Google Sheets: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
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


def show_login_page(auth_manager: AuthManager):
    """Display login page"""
    st.markdown('<h1 style="text-align: center;">🔐 Login Required</h1>', unsafe_allow_html=True)
    
    # Show connection status
    with st.expander("🔍 Connection Status", expanded=False):
        has_creds = auth_manager.credentials is not None
        has_spreadsheet_id = auth_manager.spreadsheet_id is not None and auth_manager.spreadsheet_id != ""
        st.write(f"**Credentials loaded:** {'✅ Yes' if has_creds else '❌ No'}")
        st.write(f"**Spreadsheet ID:** {'✅ Set' if has_spreadsheet_id else '❌ Missing'}")
        if has_creds:
            st.write(f"**Client Email:** {auth_manager.credentials.get('client_email', 'N/A')}")
        if has_spreadsheet_id:
            st.write(f"**Spreadsheet ID:** {auth_manager.spreadsheet_id}")
    
    # Get users for dropdown
    users = auth_manager.get_users_from_sheet()
    
    if not users:
        st.error("❌ No users found. Please check your Google Sheets configuration.")
        st.info("💡 For local development, create `auth/password_sheet_api.py` with your credentials.")
        st.info("💡 For Streamlit Cloud, add secrets in Settings → Secrets.")
        
        # Show debug info
        if not auth_manager.credentials:
            st.warning("⚠️ No credentials loaded. Check Streamlit Cloud secrets or local auth file.")
        elif not auth_manager.spreadsheet_id:
            st.warning("⚠️ No Spreadsheet ID found. Make sure SPREADSHEET_ID is in your secrets.")
        return
    
    user_names = [user['name'] for user in users]
    
    # Login form
    with st.container():
        st.markdown("### Please select your name and enter your password")
        
        selected_user = st.selectbox("Select your name", options=user_names, key="login_user_select")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", type="primary", use_container_width=True):
            # Find selected user's email
            selected_email = None
            for user in users:
                if user['name'] == selected_user:
                    selected_email = user['email']
                    break
            
            if selected_email and auth_manager.authenticate(selected_email, password):
                st.session_state.authenticated_user = {
                    'email': auth_manager.user_email,
                    'name': auth_manager.user_name,
                    'role': auth_manager.user_role
                }
                st.success(f"✅ Welcome, {auth_manager.user_name}!")
                st.rerun()
            else:
                st.error("❌ Invalid password. Please try again.")


def check_authentication(auth_manager: AuthManager) -> bool:
    """Check if user is authenticated, show login if not"""
    # Initialize session state
    if 'authenticated_user' not in st.session_state:
        st.session_state.authenticated_user = None
    
    # Check authentication
    if not st.session_state.authenticated_user:
        show_login_page(auth_manager)
        return False
    
    # Load user from session
    user = st.session_state.authenticated_user
    auth_manager.user_email = user['email']
    auth_manager.user_name = user['name']
    auth_manager.user_role = user['role']
    auth_manager.authenticated = True
    
    return True

