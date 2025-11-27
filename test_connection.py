"""
Test database connection
"""
import psycopg2
import sys

# Session Pooler connection (IPv4 compatible)
connection_string = "postgresql://postgres.pyyiqnjwgyexrzvpiaok:Fourier98*expenses@aws-1-us-east-1.pooler.supabase.com:5432/postgres"

print("Testing database connection...")
print("Using Session Pooler (IPv4 compatible)")
print("Connection: postgresql://postgres.pyyiqnjwgyexrzvpiaok:***@aws-1-us-east-1.pooler.supabase.com:5432/postgres")

# Try connection string format
print("\n[1] Trying connection string format...")
try:
    conn = psycopg2.connect(connection_string)
    print("[SUCCESS] Connected using connection string!")
    conn.close()
    sys.exit(0)
except Exception as e:
    print(f"[ERROR] Connection string failed: {e}")

# Try individual parameters
print("\n[2] Trying individual parameters...")
try:
    conn = psycopg2.connect(
        host='aws-1-us-east-1.pooler.supabase.com',
        port=5432,
        database='postgres',
        user='postgres.pyyiqnjwgyexrzvpiaok',
        password='Fourier98*expenses'
    )
    print("[SUCCESS] Connected using individual parameters!")
    conn.close()
    sys.exit(0)
except Exception as e:
    print(f"[ERROR] All connection methods failed: {e}")
    print("\nPossible issues:")
    print("1. Network connectivity - check your internet connection")
    print("2. DNS resolution - the hostname might not be resolvable")
    print("3. Firewall - port 5432 might be blocked")
    print("4. IPv4 network - if on IPv4-only network, you may need Session Pooler")
    print("   Get pooler connection from: Supabase Dashboard > Settings > Database > Connection Pooling")
    print("5. Hostname - verify the Supabase database hostname is correct")
    sys.exit(1)

print("\nConnection test successful! You can now run setup_database.py")

