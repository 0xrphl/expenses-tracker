# Database Connection Setup

## Connection Information

You provided the direct connection string:
```
postgresql://postgres:Fourier98*expenses@db.pyyiqnjwgyexrzvpiaok.supabase.co:5432/postgres
```

## Connection Methods

### Direct Connection (Current Setup)
- **Host**: db.pyyiqnjwgyexrzvpiaok.supabase.co
- **Port**: 5432
- **Database**: postgres
- **User**: postgres
- **Password**: Fourier98*expenses

This is configured in all the scripts and the app.

### Session Pooler (For IPv4 Networks)

If you're on an IPv4-only network and the direct connection doesn't work, use Session Pooler:

1. Go to **Supabase Dashboard > Settings > Database > Connection Pooling**
2. Copy the **Session Pooler** connection string
3. Update the connection in `app.py` and `setup_database.py`

The pooler typically uses:
- Port: **6543** (instead of 5432)
- User format: `postgres.PROJECT_REF` (instead of just `postgres`)

## Testing Connection

Run the test script:
```bash
python test_connection.py
```

## Setting Up Database

Once connection works, run:
```bash
python setup_database.py
```

This will create all tables and set up users.

## Troubleshooting

### DNS Resolution Error
- Check your internet connection
- Verify the hostname is correct
- Try using Session Pooler if on IPv4 network

### Connection Timeout
- Check firewall settings (port 5432 or 6543)
- Verify Supabase project is active
- Check if your IP needs to be whitelisted in Supabase

### IPv4 Network Issues
If you see "Not IPv4 compatible" in Supabase:
- Use Session Pooler (port 6543)
- Or purchase IPv4 add-on from Supabase

