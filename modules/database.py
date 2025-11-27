"""Database connection and configuration"""
import psycopg2

# Database configuration - Session Pooler (IPv4 compatible)
DB_CONFIG = {
    'host': 'aws-1-us-east-1.pooler.supabase.com',
    'port': 5432,
    'database': 'postgres',
    'user': 'postgres.pyyiqnjwgyexrzvpiaok',
    'password': 'Fourier98*expenses'
}

CONNECTION_STRING = "postgresql://postgres.pyyiqnjwgyexrzvpiaok:Fourier98*expenses@aws-1-us-east-1.pooler.supabase.com:5432/postgres"

def get_db_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(CONNECTION_STRING)
        return conn
    except Exception as e:
        import streamlit as st
        st.error(f"Database connection error: {e}")
        return None

