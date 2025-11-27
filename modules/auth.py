"""Authentication functions"""
import streamlit as st
import hashlib
from functools import wraps
from psycopg2.extras import RealDictCursor
from modules.database import get_db_connection

def hash_password(password):
    """Hash password for storage"""
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(password, hashed):
    """Check password against hash"""
    return hash_password(password) == hashed

def require_auth(func):
    """Decorator to require authentication"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'authenticated' not in st.session_state or not st.session_state.authenticated:
            st.error("Please log in first")
            st.stop()
        return func(*args, **kwargs)
    return wrapper

def init_session_state():
    """Initialize session state"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    # Initialize modal states
    if 'show_add_expense' not in st.session_state:
        st.session_state.show_add_expense = False
    if 'show_add_income' not in st.session_state:
        st.session_state.show_add_income = False
    if 'show_add_asset' not in st.session_state:
        st.session_state.show_add_asset = False
    if 'show_fixed_expenses' not in st.session_state:
        st.session_state.show_fixed_expenses = False
    if 'show_exchange_rates' not in st.session_state:
        st.session_state.show_exchange_rates = False

def login_page():
    """Login page"""
    st.title("💰 Expenses Tracker")
    st.markdown("### Sign in to manage your finances")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Sign In")
        
        if submit:
            conn = get_db_connection()
            if conn:
                try:
                    cur = conn.cursor(cursor_factory=RealDictCursor)
                    cur.execute("""
                        SELECT id, username, password_hash 
                        FROM users 
                        WHERE username = %s
                    """, (username,))
                    user = cur.fetchone()
                    
                    if user and check_password(password, user['password_hash']):
                        st.session_state.authenticated = True
                        st.session_state.user_id = user['id']
                        st.session_state.username = user['username']
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                    cur.close()
                    conn.close()
                except Exception as e:
                    st.error(f"Login error: {e}")
                    conn.close()

