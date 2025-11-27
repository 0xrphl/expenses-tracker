"""
Script to set up the database schema and users
"""
import psycopg2
import hashlib

# Database connection - Session Pooler (IPv4 compatible)
# Using Session Pooler connection string from Supabase
CONNECTION_STRING = "postgresql://postgres.pyyiqnjwgyexrzvpiaok:Fourier98*expenses@aws-1-us-east-1.pooler.supabase.com:5432/postgres"

# Individual parameters for Session Pooler
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

def setup_database():
    """Create all tables and set up users"""
    try:
        # Try connection string first
        print("Attempting to connect to database...")
        try:
            conn = psycopg2.connect(CONNECTION_STRING)
            print("[OK] Connected using connection string")
        except Exception as e1:
            print(f"[WARNING] Connection string failed: {e1}")
            print("Trying individual parameters...")
            try:
                conn = psycopg2.connect(**DB_CONFIG)
                print("[OK] Connected using individual parameters")
            except Exception as e2:
                print(f"[ERROR] Connection failed: {e2}")
                print("\nIf you're on an IPv4 network, you may need to use Session Pooler.")
                print("Get the pooler connection string from: Supabase Dashboard > Settings > Database > Connection Pooling")
                raise
        conn.autocommit = True
        cur = conn.cursor()
        
        print("Creating database schema...")
        
        # Enable UUID extension
        cur.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
        print("[OK] UUID extension enabled")
        
        # Create users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
              id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
              username VARCHAR(50) UNIQUE NOT NULL,
              email VARCHAR(255) UNIQUE,
              password_hash VARCHAR(255) NOT NULL,
              created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        print("[OK] UUID extension enabled")
        
        # Create users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
              id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
              username VARCHAR(50) UNIQUE NOT NULL,
              email VARCHAR(255) UNIQUE,
              password_hash VARCHAR(255) NOT NULL,
              created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        print("[OK] Users table created")
        
        # Create expense categories table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS expense_categories (
              id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
              name VARCHAR(100) UNIQUE NOT NULL,
              description TEXT,
              created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        print("[OK] Expense categories table created")
        
        # Insert default categories
        cur.execute("""
            INSERT INTO expense_categories (name, description) VALUES
              ('Luxury', 'Luxury items and services'),
              ('Transportation', 'Transportation expenses'),
              ('Groceries', 'Grocery shopping'),
              ('Deliveries', 'Food and package deliveries'),
              ('Maid', 'Maid and cleaning services'),
              ('Utility Bills', 'Utility bills'),
              ('Uber', 'Ride-sharing services'),
              ('Other', 'Other expenses')
            ON CONFLICT (name) DO NOTHING;
        """)
        print("[OK] Default categories inserted")
        
        # Create fixed expenses table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS fixed_expenses (
              id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
              user_id UUID REFERENCES users(id) ON DELETE CASCADE,
              name VARCHAR(100) NOT NULL,
              amount DECIMAL(10, 2) NOT NULL,
              currency VARCHAR(3) DEFAULT 'USD',
              category_id UUID REFERENCES expense_categories(id),
              is_paid BOOLEAN DEFAULT FALSE,
              due_date DATE,
              month_year VARCHAR(7),
              created_at TIMESTAMP DEFAULT NOW(),
              UNIQUE(user_id, name, month_year)
            );
        """)
        print("[OK] Fixed expenses table created")
        
        # Create expenses table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
              id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
              user_id UUID REFERENCES users(id) ON DELETE CASCADE,
              amount DECIMAL(10, 2) NOT NULL,
              currency VARCHAR(3) DEFAULT 'USD',
              category_id UUID REFERENCES expense_categories(id),
              description TEXT,
              date DATE NOT NULL,
              created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        print("[OK] Expenses table created")
        
        # Create income table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS income (
              id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
              user_id UUID REFERENCES users(id) ON DELETE CASCADE,
              name VARCHAR(100) NOT NULL,
              amount_cop DECIMAL(10, 2) NOT NULL,
              exchange_rate DECIMAL(10, 4),
              amount_usd DECIMAL(10, 2),
              date DATE NOT NULL,
              created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        print("[OK] Income table created")
        
        # Create assets table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS assets (
              id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
              user_id UUID REFERENCES users(id) ON DELETE CASCADE,
              name VARCHAR(100) NOT NULL,
              type VARCHAR(50),
              value DECIMAL(10, 2) NOT NULL,
              currency VARCHAR(3) DEFAULT 'USD',
              description TEXT,
              date DATE NOT NULL,
              created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        print("[OK] Assets table created")
        
        # Create exchange rates table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS exchange_rates (
              id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
              rate DECIMAL(10, 4) NOT NULL,
              date DATE NOT NULL DEFAULT CURRENT_DATE,
              is_active BOOLEAN DEFAULT TRUE,
              notes TEXT,
              created_at TIMESTAMP DEFAULT NOW(),
              updated_at TIMESTAMP DEFAULT NOW()
            );
        """)
        print("[OK] Exchange rates table created")
        
        # Insert default exchange rate
        cur.execute("""
            INSERT INTO exchange_rates (rate, date, is_active) 
            VALUES (4200.00, CURRENT_DATE, TRUE)
            ON CONFLICT DO NOTHING;
        """)
        print("[OK] Default exchange rate inserted")
        
        # Create indexes
        indexes = [
            ("idx_expenses_user_id", "CREATE INDEX IF NOT EXISTS idx_expenses_user_id ON expenses(user_id);"),
            ("idx_expenses_date", "CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date);"),
            ("idx_fixed_expenses_user_id", "CREATE INDEX IF NOT EXISTS idx_fixed_expenses_user_id ON fixed_expenses(user_id);"),
            ("idx_fixed_expenses_month_year", "CREATE INDEX IF NOT EXISTS idx_fixed_expenses_month_year ON fixed_expenses(month_year);"),
            ("idx_income_user_id", "CREATE INDEX IF NOT EXISTS idx_income_user_id ON income(user_id);"),
            ("idx_income_date", "CREATE INDEX IF NOT EXISTS idx_income_date ON income(date);"),
            ("idx_assets_user_id", "CREATE INDEX IF NOT EXISTS idx_assets_user_id ON assets(user_id);"),
            ("idx_exchange_rates_date", "CREATE INDEX IF NOT EXISTS idx_exchange_rates_date ON exchange_rates(date);"),
            ("idx_exchange_rates_active", "CREATE INDEX IF NOT EXISTS idx_exchange_rates_active ON exchange_rates(is_active);")
        ]
        
        for idx_name, idx_sql in indexes:
            cur.execute(idx_sql)
        print("[OK] All indexes created")
        
        # Set up users
        print("\nSetting up users...")
        password = 'Fourier98*expenses'
        password_hash = hash_password(password)
        
        users = [
            ('rafael', 'rafael@expenses.com', password_hash),
            ('yessica', 'yessica@expenses.com', password_hash)
        ]
        
        for username, email, pwd_hash in users:
            cur.execute("""
                INSERT INTO users (username, email, password_hash)
                VALUES (%s, %s, %s)
                ON CONFLICT (username) 
                DO UPDATE SET password_hash = EXCLUDED.password_hash, email = EXCLUDED.email
            """, (username, email, pwd_hash))
            print(f"[OK] User {username} created/updated")
        
        cur.close()
        conn.close()
        
        print("\n[SUCCESS] Database setup completed successfully!")
        print("\nYou can now run the Streamlit app with: streamlit run app.py")
        print("\nDefault users:")
        print("  - Username: rafael | Password: Fourier98*expenses")
        print("  - Username: yessica | Password: Fourier98*expenses")
        
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    setup_database()

