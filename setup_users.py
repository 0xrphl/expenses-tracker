"""
Script to set up users with proper password hashes
Run this after creating the database schema
"""
import psycopg2
import hashlib

# Database configuration - Session Pooler (IPv4 compatible)
DB_CONFIG = {
    'host': 'aws-1-us-east-1.pooler.supabase.com',
    'port': 5432,
    'database': 'postgres',
    'user': 'postgres.pyyiqnjwgyexrzvpiaok',
    'password': 'Fourier98*expenses'
}

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def setup_users():
    """Create users with hashed passwords"""
    password = 'Fourier98*expenses'
    password_hash = hash_password(password)
    
    users = [
        ('rafael', 'rafael@expenses.com', password_hash),
        ('yessica', 'yessica@expenses.com', password_hash)
    ]
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        for username, email, pwd_hash in users:
            cur.execute("""
                INSERT INTO users (username, email, password_hash)
                VALUES (%s, %s, %s)
                ON CONFLICT (username) 
                DO UPDATE SET password_hash = EXCLUDED.password_hash
            """, (username, email, pwd_hash))
            print(f"✓ User {username} created/updated")
        
        conn.commit()
        cur.close()
        conn.close()
        print("Users setup completed!")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    setup_users()

