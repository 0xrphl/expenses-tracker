-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  username VARCHAR(50) UNIQUE NOT NULL,
  email VARCHAR(255) UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Insert default users (rafael and yessica)
-- Password: Fourier98*expenses
-- Hash is SHA256 of the password: 6799ce70caf8e22d4aa2f0797e0e88796459fe20ea6c20aaa653b862907216bf
-- Note: Run setup_users.py to properly set up users with correct password hashes

-- Expense categories
CREATE TABLE IF NOT EXISTS expense_categories (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(100) UNIQUE NOT NULL,
  description TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Insert default categories
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

-- Fixed expenses/liabilities
CREATE TABLE IF NOT EXISTS fixed_expenses (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(100) NOT NULL,
  amount DECIMAL(10, 2) NOT NULL,
  currency VARCHAR(3) DEFAULT 'USD',
  category_id UUID REFERENCES expense_categories(id),
  is_paid BOOLEAN DEFAULT FALSE,
  due_date DATE,
  month_year VARCHAR(7), -- Format: YYYY-MM
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, name, month_year)
);

-- Expenses
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

-- Income
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

-- Assets
CREATE TABLE IF NOT EXISTS assets (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(100) NOT NULL,
  type VARCHAR(50), -- savings, investment, property, etc.
  value DECIMAL(10, 2) NOT NULL,
  currency VARCHAR(3) DEFAULT 'USD',
  description TEXT,
  date DATE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Exchange Rates (USD/COP)
CREATE TABLE IF NOT EXISTS exchange_rates (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  rate DECIMAL(10, 4) NOT NULL,
  date DATE NOT NULL DEFAULT CURRENT_DATE,
  is_active BOOLEAN DEFAULT TRUE,
  notes TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Insert default exchange rate
INSERT INTO exchange_rates (rate, date, is_active) 
VALUES (4200.00, CURRENT_DATE, TRUE)
ON CONFLICT DO NOTHING;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_expenses_user_id ON expenses(user_id);
CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date);
CREATE INDEX IF NOT EXISTS idx_fixed_expenses_user_id ON fixed_expenses(user_id);
CREATE INDEX IF NOT EXISTS idx_fixed_expenses_month_year ON fixed_expenses(month_year);
CREATE INDEX IF NOT EXISTS idx_income_user_id ON income(user_id);
CREATE INDEX IF NOT EXISTS idx_income_date ON income(date);
CREATE INDEX IF NOT EXISTS idx_assets_user_id ON assets(user_id);
CREATE INDEX IF NOT EXISTS idx_exchange_rates_date ON exchange_rates(date);
CREATE INDEX IF NOT EXISTS idx_exchange_rates_active ON exchange_rates(is_active);
