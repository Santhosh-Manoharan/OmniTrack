-- OmniTrack Database Schema
-- Run this in PostgreSQL to create the expense tracking tables

-- Create the omnitrack database (if not exists from docker-compose)
-- CREATE DATABASE omnitrack;

-- Connect to omnitrack database
\c omnitrack;

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_date DATE NOT NULL DEFAULT CURRENT_DATE,
    amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'INR',
    payee VARCHAR(255),
    type VARCHAR(20) NOT NULL CHECK (type IN ('debit', 'credit', 'transfer')),
    category VARCHAR(50) DEFAULT 'other',
    source VARCHAR(50) NOT NULL CHECK (source IN ('receipt_upload', 'gpay_email', 'gpay_sms', 'manual', 'bank_import')),
    source_ref VARCHAR(255),
    raw_text TEXT,
    document_id INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type);
CREATE INDEX IF NOT EXISTS idx_transactions_source ON transactions(source);

-- Categories reference table
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    keywords TEXT[], -- for auto-categorization
    is_income BOOLEAN DEFAULT false
);

-- Insert default categories
INSERT INTO categories (name, description, keywords, is_income) VALUES
    ('groceries', 'Grocery shopping', ARRAY['reliance', 'bigbazaar', 'dmart', 'kirana', 'supermarket', 'grocery'], false),
    ('utilities', 'Bills and utilities', ARRAY['electricity', 'water', 'gas', 'broadband', 'jio', 'airtli', 'bill'], false),
    ('transport', 'Transportation', ARRAY['uber', 'ola', 'petrol', 'diesel', 'metro', 'bus', 'auto', 'rapido'], false),
    ('entertainment', 'Entertainment', ARRAY['netflix', 'spotify', 'prime', 'hotstar', 'movie', 'pvr', 'inox'], false),
    ('medical', 'Healthcare', ARRAY['hospital', 'pharmacy', 'doctor', 'apollo', 'medplus', 'insurance'], false),
    ('education', 'Education', ARRAY['school', 'college', 'course', 'udemy', 'coursera', 'fee'], false),
    ('rent', 'Rent and housing', ARRAY['rent', 'maintenance', 'housing', 'society'], false),
    ('food', 'Food and dining', ARRAY['swiggy', 'zomato', 'restaurant', 'cafe', 'food', 'pizza', 'burger'], false),
    ('shopping', 'Shopping', ARRAY['amazon', 'flipkart', 'myntra', 'shop', 'store', 'mall'], false),
    ('salary', 'Income', ARRAY['salary', 'income', 'credited', 'payment received', 'freelance'], true),
    ('transfer', 'Money transfer', ARRAY['upi', 'transfer', 'sent to', 'received from'], false),
    ('other', 'Other', NULL, false)
ON CONFLICT (name) DO NOTHING;

-- Monthly summary view
CREATE OR REPLACE VIEW monthly_summary AS
SELECT
    DATE_TRUNC('month', transaction_date) AS month,
    type,
    category,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_amount
FROM transactions
GROUP BY DATE_TRUNC('month', transaction_date), type, category
ORDER BY month DESC, type, total_amount DESC;

-- Daily spending view
CREATE OR REPLACE VIEW daily_spending AS
SELECT
    transaction_date,
    category,
    COUNT(*) AS count,
    SUM(amount) AS total
FROM transactions
WHERE type = 'debit'
GROUP BY transaction_date, category
ORDER BY transaction_date DESC;

-- Function to auto-categorize based on payee name
CREATE OR REPLACE FUNCTION auto_categorize(payee_text TEXT)
RETURNS VARCHAR(50) AS $$
DECLARE
    cat VARCHAR(50);
BEGIN
    SELECT c.name INTO cat
    FROM categories c
    WHERE c.keywords IS NOT NULL
      AND EXISTS (
          SELECT 1
          FROM unnest(c.keywords) AS kw
          WHERE LOWER(payee_text) LIKE '%' || kw || '%'
      )
    LIMIT 1;
    
    RETURN COALESCE(cat, 'other');
END;
$$ LANGUAGE plpgsql;
