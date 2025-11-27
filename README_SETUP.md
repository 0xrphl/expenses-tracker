# Database Setup Instructions

## Quick Setup

I've created the setup scripts for you. The database connection uses:
- **Host**: db.pyyiqnjwgyexrzvpiaok.supabase.co
- **Port**: 5432
- **Database**: postgres
- **User**: postgres
- **Password**: Fourier98*expenses

## Steps to Set Up

1. **Test the connection** (optional):
   ```bash
   python test_connection.py
   ```

2. **Set up the database** (creates all tables and users):
   ```bash
   python setup_database.py
   ```

   This will:
   - Create all necessary tables (users, expenses, income, assets, exchange_rates, etc.)
   - Insert default expense categories
   - Create default exchange rate (4200.00)
   - Create users: `rafael` and `yessica` with password `Fourier98*expenses`

3. **Run the Streamlit app**:
   ```bash
   streamlit run app.py
   ```

## If Connection Fails

If you get a DNS resolution error, check:
1. **Internet connection** - Make sure you're connected to the internet
2. **Supabase hostname** - Verify the hostname is correct in your Supabase dashboard
3. **Firewall** - Port 5432 might be blocked
4. **VPN** - If you're using a VPN, try disconnecting/reconnecting

## Manual Setup (Alternative)

If the script doesn't work, you can manually run the SQL:

1. Connect to your Supabase database using any PostgreSQL client
2. Run the SQL from `database/schema.sql`
3. Run `python setup_users.py` to create users with proper password hashes

## Default Users

After setup, you can log in with:
- **Username**: `rafael` | **Password**: `Fourier98*expenses`
- **Username**: `yessica` | **Password**: `Fourier98*expenses`

## Next Steps

Once the database is set up:
1. Run `streamlit run app.py`
2. Log in with one of the default users
3. Start adding expenses, income, and managing exchange rates!

