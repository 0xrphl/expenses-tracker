# Expenses Tracker - Streamlit App

A modern expense and income tracking application built with Streamlit and PostgreSQL.

## Features

- 🔐 User authentication with login
- 💰 Income tracking with automatic USD/COP conversion
- 💸 Expense management with categories
- 🏠 Fixed expenses tracking with payment confirmation
- 📊 Dashboard with financial overview
- 💎 Asset management
- 💱 Exchange rate management
- 🌙 Dark theme UI

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Database Setup

1. Connect to your Supabase PostgreSQL database:
   ```
   postgresql://postgres:Fourier98*expenses@db.pyyiqnjwgyexrzvpiaok.supabase.co:5432/postgres
   ```

2. Run the schema SQL file to create tables:
   ```bash
   psql "postgresql://postgres:Fourier98*expenses@db.pyyiqnjwgyexrzvpiaok.supabase.co:5432/postgres" -f database/schema.sql
   ```

3. Set up users with proper password hashes:
   ```bash
   python setup_users.py
   ```

### 3. Run the Application

```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`

## Default Users

- **Username**: `rafael` | **Password**: `Fourier98*expenses`
- **Username**: `yessica` | **Password**: `Fourier98*expenses`

## Income Calculation Logic

- **Income 1 (Rafael)**: Base amount = 4400 * 2300 COP
- **Income 2**: Base amount = 4400 * 3000 COP

Conversion to USD:
- If USD/COP < 4400: Use 4400 as exchange rate (more USD)
- If USD/COP ≥ 4400: Use actual exchange rate (less USD)

## Fixed Expenses

Default fixed expenses:
- Residence Admin: $100 USD
- Gas Utility Bill: $15 USD
- Internet: $25 USD
- Mobile Internet: $20 USD
- Water: $26 USD
- Mortgage: $490 USD
- Second Credit Line: $300 USD
- Uber: $100 USD (variable liability)

## Expense Categories

- Luxury
- Transportation
- Groceries
- Deliveries
- Maid
- Utility Bills
- Uber
- Other

## Tech Stack

- Streamlit
- PostgreSQL (Supabase)
- Python 3.8+
