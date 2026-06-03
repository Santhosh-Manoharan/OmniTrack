-- OmniTrack Database Schema v2
-- Bank transaction tracking via email/SMS

CREATE DATABASE IF NOT EXISTS omnitrack;
\c omnitrack;

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_date DATE,
    amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'INR',
    transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('DEBIT', 'CREDIT', 'TRANSFER')),
    merchant_name VARCHAR(255),
    merchant_upi VARCHAR(255),
    bank_name VARCHAR(100),
    account_identifier VARCHAR(20),
    category VARCHAR(50) DEFAULT 'other',
    source VARCHAR(50) NOT NULL CHECK (source IN ('bank_email', 'bank_sms', 'receipt_upload', 'manual')),
    source_ref VARCHAR(255),
    raw_text TEXT,
    document_id INTEGER,
    is_generated BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_txn_date ON transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_txn_category ON transactions(category);
CREATE INDEX IF NOT EXISTS idx_txn_type ON transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_txn_source ON transactions(source);
CREATE INDEX IF NOT EXISTS idx_txn_merchant ON transactions(merchant_name);

-- Categories
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    keywords TEXT[],
    is_income BOOLEAN DEFAULT false
);

INSERT INTO categories (name, keywords, is_income) VALUES
    ('groceries', ARRAY['reliance','bigbazaar','dmart','kirana','supermarket','blaze','more','grocery'], false),
    ('utilities', ARRAY['electricity','water','gas','broadband','jio','airtli','vodafone','bsnl','idea','bill','dth','recharge'], false),
    ('transport', ARRAY['uber','ola','rapido','petrol','diesel','metro','bus','auto','zoom','drive','fuel'], false),
    ('food', ARRAY['swiggy','zomato','restaurant','cafe','food','pizza','burger','dunkin','mcdonald','kfc'], false),
    ('entertainment', ARRAY['netflix','spotify','prime','hotstar','movie','inox','pvr','game','play'], false),
    ('medical', ARRAY['hospital','pharmacy','doctor','apollo','medplus','lab','health','clinic','dr.'], false),
    ('education', ARRAY['school','college','course','udemy','coursera','fee','tuition','coaching'], false),
    ('rent', ARRAY['rent','maintenance','housing','society','landlord'], false),
    ('shopping', ARRAY['amazon','flipkart','myntra','store','mall','purchase','shop','online'], false),
    ('salary', ARRAY['salary','income','credited','payment received','freelance','bonus','dividend'], true),
    ('transfer', ARRAY['upi','transfer','sent to','received from','neft','rtgs','imps','self'], false),
    ('fuel', ARRAY['petrol','diesel','fuel','hpcl','iocl','bpcl','shell','hp','indianoil'], false),
    ('insurance', ARRAY['insurance','lic','policy','premium','lic','max life','icici pru'], false),
    ('emi', ARRAY['emi','loan','hdfc loan','sbi loan','axis loan','payment due'], false),
    ('other', NULL, false)
ON CONFLICT (name) DO NOTHING;

-- Merchant master
CREATE TABLE IF NOT EXISTS merchants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    upi_ids TEXT[],
    default_category VARCHAR(50) DEFAULT 'other',
    is_favorite BOOLEAN DEFAULT false,
    UNIQUE(name)
);

-- Auto-categorize function
CREATE OR REPLACE FUNCTION auto_categorize_merchant(payee TEXT)
RETURNS VARCHAR(50) AS $$
DECLARE
    cat VARCHAR(50);
BEGIN
    SELECT c.name INTO cat FROM categories c
    WHERE c.keywords IS NOT NULL
      AND EXISTS (SELECT 1 FROM unnest(c.keywords) AS kw WHERE LOWER(payee) LIKE '%' || kw || '%')
    LIMIT 1;
    RETURN COALESCE(cat, 'other');
END;
$$ LANGUAGE plpgsql;

-- Views
CREATE OR REPLACE VIEW monthly_summary AS
SELECT
    DATE_TRUNC('month', transaction_date) AS month,
    transaction_type,
    category,
    COUNT(*) AS txn_count,
    SUM(amount) AS total
FROM transactions
GROUP BY 1,2,3 ORDER BY 1 DESC,2,3 DESC;

CREATE OR REPLACE VIEW daily_spending AS
SELECT transaction_date, category, COUNT(*) AS cnt, SUM(amount) AS total
FROM transactions WHERE transaction_type='DEBIT'
GROUP BY 1,2 ORDER BY 1 DESC;

CREATE OR REPLACE VIEW merchant_spending AS
SELECT merchant_name, category, COUNT(*) AS txns, SUM(amount) AS total_spent,
       AVG(amount) AS avg_txn, MAX(transaction_date) AS last_seen
FROM transactions WHERE transaction_type='DEBIT'
GROUP BY 1,2 ORDER BY total_spent DESC;
