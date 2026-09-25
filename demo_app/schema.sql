CREATE TABLE members (
    member_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    zip_code TEXT,
    status TEXT NOT NULL DEFAULT 'Active',
    created_at TEXT NOT NULL
);

CREATE TABLE accounts (
    account_id TEXT PRIMARY KEY,
    member_id TEXT NOT NULL,
    account_type TEXT NOT NULL,
    balance_cents INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'Open',
    opened_at TEXT NOT NULL,

    FOREIGN KEY (member_id)
        REFERENCES members(member_id)
);

CREATE TABLE transactions (
    transaction_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    transaction_type TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'Posted',
    created_at TEXT NOT NULL,

    FOREIGN KEY (account_id)
        REFERENCES accounts(account_id)
);