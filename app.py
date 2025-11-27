"""Main Streamlit application"""
import streamlit as st
from modules.auth import init_session_state, login_page, require_auth
from modules.pages import show_dashboard_page, show_expenses_page, show_fixed_expenses_page, show_assets_page

# Page configuration
st.set_page_config(
    page_title="Expenses Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme
st.markdown("""
<style>
    .stApp {
        background-color: #0f0f0f;
        color: #e0e0e0;
    }
    .main .block-container {
        padding-top: 2rem;
    }
    h1, h2, h3 {
        color: #6366f1;
    }
    .metric-card {
        background-color: #1a1a1a;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #333333;
        margin-bottom: 1rem;
    }
    .positive {
        color: #10b981;
    }
    .negative {
        color: #ef4444;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application"""
    init_session_state()
    
    if not st.session_state.authenticated:
        login_page()
    else:
        # Sidebar navigation
        with st.sidebar:
            st.title(f"💰 Expenses Tracker")
            st.markdown(f"**Welcome, {st.session_state.username}**")
            st.markdown("---")
            
            # Navigation menu
            page = st.radio(
                "Navigation",
                ["📊 Dashboard", "💸 Expenses", "🏠 Fixed Expenses", "💎 Assets & Credits"],
                key="nav_menu"
            )
            
            st.markdown("---")
            
            # Quick actions
            st.markdown("### Quick Actions")
            if st.button("💰 Add Income", use_container_width=True, key="sidebar_add_income"):
                if not st.session_state.get('show_add_income'):
                    st.session_state.show_add_income = True
                    st.session_state.current_page = "📊 Dashboard"
                    st.rerun()
            
            st.markdown("---")
            
            # Logout
            if st.button("🚪 Logout", use_container_width=True, type="secondary"):
                st.session_state.authenticated = False
                st.session_state.user_id = None
                st.session_state.username = None
                st.rerun()
        
        # Store current page
        st.session_state.current_page = page
        
        # Show selected page
        if page == "📊 Dashboard":
            show_dashboard_page()
        elif page == "💸 Expenses":
            show_expenses_page()
        elif page == "🏠 Fixed Expenses":
            show_fixed_expenses_page()
        elif page == "💎 Assets & Credits":
            show_assets_page()
        
        # Handle add income modal (can be triggered from sidebar)
        if st.session_state.get('show_add_income'):
            from modules.database import get_db_connection
            from modules.modals import show_add_income_modal
            from psycopg2.extras import RealDictCursor
            
            conn = get_db_connection()
            if conn:
                try:
                    cur = conn.cursor(cursor_factory=RealDictCursor)
                    cur.execute("""
                        SELECT rate FROM exchange_rates 
                        WHERE is_active = TRUE 
                        ORDER BY date DESC LIMIT 1
                    """)
                    exchange_rate_data = cur.fetchone()
                    current_rate = exchange_rate_data['rate'] if exchange_rate_data else 4200
                    show_add_income_modal(cur, conn, current_rate)
                    cur.close()
                    conn.close()
                except Exception as e:
                    st.error(f"Error: {e}")

if __name__ == "__main__":
    main()
