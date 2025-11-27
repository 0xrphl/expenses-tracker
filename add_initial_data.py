"""
Script to add initial income and fixed expenses data
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date

# Database configuration - Session Pooler
DB_CONFIG = {
    'host': 'aws-1-us-east-1.pooler.supabase.com',
    'port': 5432,
    'database': 'postgres',
    'user': 'postgres.pyyiqnjwgyexrzvpiaok',
    'password': 'Fourier98*expenses'
}

CONNECTION_STRING = "postgresql://postgres.pyyiqnjwgyexrzvpiaok:Fourier98*expenses@aws-1-us-east-1.pooler.supabase.com:5432/postgres"

def get_current_exchange_rate(cur):
    """Get current active exchange rate"""
    cur.execute("""
        SELECT rate FROM exchange_rates 
        WHERE is_active = TRUE 
        ORDER BY date DESC LIMIT 1
    """)
    result = cur.fetchone()
    return result['rate'] if result else 4200.0

def calculate_income(multiplier, threshold=4400):
    """Calculate income based on multiplier and threshold"""
    # Get current exchange rate
    conn = psycopg2.connect(CONNECTION_STRING)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    current_rate = get_current_exchange_rate(cur)
    cur.close()
    conn.close()
    
    # Base amount in COP
    amount_cop = 4400 * multiplier
    
    # Calculate USD based on threshold logic
    if current_rate < threshold:
        # If USD/COP < threshold, use threshold as rate (get more USD)
        calculated_rate = threshold
        amount_usd = amount_cop / threshold
    else:
        # If USD/COP >= threshold, use actual rate (get less USD)
        calculated_rate = current_rate
        amount_usd = amount_cop / current_rate
    
    return {
        'amount_cop': amount_cop,
        'amount_usd': amount_usd,
        'exchange_rate': current_rate,
        'calculated_rate': calculated_rate
    }

def add_initial_data():
    """Add initial income and fixed expenses"""
    try:
        conn = psycopg2.connect(CONNECTION_STRING)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get user IDs
        cur.execute("SELECT id, username FROM users WHERE username IN ('rafael', 'yessica')")
        users = {user['username']: user['id'] for user in cur.fetchall()}
        
        if 'rafael' not in users or 'yessica' not in users:
            print("[ERROR] Users not found. Please run setup_database.py first.")
            return
        
        rafael_id = users['rafael']
        yessica_id = users['yessica']
        
        print("Adding income data...")
        
        # Add income for Rafael (Income 1)
        income1 = calculate_income(2300, 4400)
        cur.execute("""
            INSERT INTO income (user_id, name, amount_cop, exchange_rate, amount_usd, date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (rafael_id, 'Income 1 (Rafael)', income1['amount_cop'], income1['calculated_rate'], income1['amount_usd'], date.today()))
        print(f"[OK] Added Income 1 (Rafael): ${income1['amount_usd']:,.2f} USD (Rate: {income1['calculated_rate']:,.2f})")
        
        # Add income for Income 2
        income2 = calculate_income(3000, 4400)
        cur.execute("""
            INSERT INTO income (user_id, name, amount_cop, exchange_rate, amount_usd, date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (yessica_id, 'Income 2', income2['amount_cop'], income2['calculated_rate'], income2['amount_usd'], date.today()))
        print(f"[OK] Added Income 2: ${income2['amount_usd']:,.2f} USD (Rate: {income2['calculated_rate']:,.2f})")
        
        # Get current month
        current_month = date.today().strftime('%Y-%m')
        
        # Get category IDs
        cur.execute("SELECT id, name FROM expense_categories")
        categories = {cat['name']: cat['id'] for cat in cur.fetchall()}
        
        print("\nAdding fixed expenses...")
        
        # Fixed expenses for both users
        fixed_expenses = [
            ('Residence Admin', 100, categories.get('Utility Bills')),
            ('Gas Utility Bill', 15, categories.get('Utility Bills')),
            ('Internet', 25, categories.get('Utility Bills')),
            ('Mobile Internet', 20, categories.get('Utility Bills')),
            ('Water', 26, categories.get('Utility Bills')),
            ('Mortgage', 490, categories.get('Other')),
            ('Second Credit Line', 300, categories.get('Other')),
            ('Uber', 100, categories.get('Uber'))
        ]
        
        for user_id in [rafael_id, yessica_id]:
            username = 'rafael' if user_id == rafael_id else 'yessica'
            for name, amount, cat_id in fixed_expenses:
                try:
                    cur.execute("""
                        INSERT INTO fixed_expenses (user_id, name, amount, currency, category_id, month_year, is_paid)
                        VALUES (%s, %s, %s, %s, %s, %s, FALSE)
                        ON CONFLICT (user_id, name, month_year) DO NOTHING
                    """, (user_id, name, amount, 'USD', cat_id, current_month))
                    print(f"[OK] Added fixed expense for {username}: {name} - ${amount}")
                except Exception as e:
                    print(f"[WARNING] Could not add {name} for {username}: {e}")
        
        conn.commit()
        cur.close()
        conn.close()
        
        print("\n[SUCCESS] Initial data added successfully!")
        print(f"\nSummary:")
        print(f"  - Income 1 (Rafael): ${income1['amount_usd']:,.2f} USD")
        print(f"  - Income 2: ${income2['amount_usd']:,.2f} USD")
        print(f"  - Fixed expenses added for both users for {current_month}")
        
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_initial_data()

