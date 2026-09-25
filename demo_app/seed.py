from multiprocessing.dummy import connection
import sqlite3
from pathlib import Path

from db import DATABASE_PATH
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = BASE_DIR / "schema.sql"


def create_database():
    if DATABASE_PATH.exists():
        DATABASE_PATH.unlink()

    connection = sqlite3.connect(DATABASE_PATH)
    # Enforce relationships between members, accounts, and transactions.
    # Without this, SQLite does not enforce foreign keys by default.
    connection.execute("PRAGMA foreign_keys = ON")

    with open(SCHEMA_PATH, "r", encoding="utf-8") as schema_file:
        connection.executescript(schema_file.read())

    return connection

def seed_members(connection):
    """Insert all demo members into the members table."""

    # Use one timestamp for when this demo dataset was created
    created_at = datetime.now().isoformat()

    for member in MEMBERS:
        connection.execute(
            """
            INSERT INTO members (
                member_id,
                full_name,
                phone,
                email,
                address,
                city,
                state,
                zip_code,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            # *member expands the 9 values in each MEMBERS tuple.
            # created_at becomes the 10th database value.
            (*member, created_at),
        )


def seed_accounts(connection):
    """Insert all demo accounts into the accounts table."""

    for account in ACCOUNTS:
        connection.execute(
            """
            INSERT INTO accounts (
                account_id,
                member_id,
                account_type,
                balance_cents,
                status,
                opened_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            account,
        )


def seed_transactions(connection):
    """Insert all demo transactions into the transactions table."""

    for transaction in TRANSACTIONS:
        connection.execute(
            """
            INSERT INTO transactions (
                transaction_id,
                account_id,
                transaction_type,
                amount_cents,
                description,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            transaction,
        )

MEMBERS = [
    (
        "100001",
        "John Carter",
        "214-555-0188",
        "john.carter@example.com",
        "1450 Legacy Dr",
        "Plano",
        "TX",
        "75024",
        "Active",
    ),
    (
        "100002",
        "Maria Lopez",
        "469-555-0142",
        "maria.lopez@example.com",
        "820 Main St",
        "Dallas",
        "TX",
        "75201",
        "Active",
    ),
    (
        "100003",
        "David Miller",
        "972-555-0103",
        "david.miller@example.com",
        "234 Oak Ln",
        "Frisco",
        "TX",
        "75034",
        "Active",
    ),
    (
        "100004",
        "Sophia Wilson",
        "214-555-0114",
        "sophia.wilson@example.com",
        "782 Pine Rd",
        "Plano",
        "TX",
        "75025",
        "Active",
    ),
    (
        "100005",
        "Ethan Harris",
        "972-555-0255",
        "ethan.harris@example.com",
        "920 Ridge Rd",
        "Garland",
        "TX",
        "75043",
        "Restricted",
    ),
]

ACCOUNTS = [
    ("CHK-100001-01", "100001", "Checking", 284075, "Open", "2021-03-15"),
    ("SAV-100001-01", "100001", "Savings", 912540, "Open", "2021-03-15"),

    ("CHK-100002-01", "100002", "Checking", 118010, "Open", "2022-06-10"),
    ("SAV-100002-01", "100002", "Savings", 432065, "Open", "2022-06-10"),

    ("CHK-100003-01", "100003", "Checking", 356820, "Open", "2020-11-02"),
    ("SAV-100003-01", "100003", "Savings", 1284500, "Open", "2020-11-02"),

    ("CHK-100004-01", "100004", "Checking", 745230, "Open", "2023-01-20"),
    ("SAV-100004-01", "100004", "Savings", 650000, "Open", "2023-01-20"),

    ("CHK-100005-01", "100005", "Checking", 92500, "Restricted", "2019-08-12"),
    ("SAV-100005-01", "100005", "Savings", 325400, "Frozen", "2019-08-12"),
]

TRANSACTIONS = [
    (
        "TXN-000001",
        "CHK-100001-01",
        "Deposit",
        250000,
        "Payroll Deposit",
        "Posted",
        "2026-09-01T09:15:00"
    ),
    (
        "TXN-000002",
        "CHK-100001-01",
        "Withdrawal",
        4250,
        "ATM Withdrawal",
        "Posted",
        "2026-09-03T14:20:00"
    ),
    (
        "TXN-000003",
        "SAV-100001-01",
        "Deposit",
        50000,
        "Savings Transfer",
        "Posted",
        "2026-09-05T10:10:00"
    ),
    (
        "TXN-000004",
        "SAV-100001-01",
        "Interest",
        825,
        "Monthly Interest",
        "Posted",
        "2026-09-10T00:00:00"
    ),

    (
        "TXN-000005",
        "CHK-100002-01",
        "Deposit",
        180000,
        "Payroll Deposit",
        "Posted",
        "2026-09-02T08:30:00"
    ),
    (
        "TXN-000006",
        "CHK-100002-01",
        "Withdrawal",
        6500,
        "Debit Card Purchase",
        "Posted",
        "2026-09-04T17:45:00"
    ),
    (
        "TXN-000007",
        "SAV-100002-01",
        "Deposit",
        25000,
        "Transfer From Checking",
        "Posted",
        "2026-09-06T11:00:00"
    ),

    (
        "TXN-000008",
        "CHK-100003-01",
        "Deposit",
        320000,
        "Direct Deposit",
        "Posted",
        "2026-09-01T07:55:00"
    ),
    (
        "TXN-000009",
        "CHK-100003-01",
        "Fee",
        1200,
        "Monthly Service Fee",
        "Posted",
        "2026-09-08T00:00:00"
    ),
    (
        "TXN-000010",
        "SAV-100003-01",
        "Interest",
        1450,
        "Monthly Interest",
        "Posted",
        "2026-09-10T00:00:00"
    ),

    (
        "TXN-000011",
        "CHK-100004-01",
        "Deposit",
        275000,
        "Payroll Deposit",
        "Posted",
        "2026-09-02T09:05:00"
    ),
    (
        "TXN-000012",
        "CHK-100004-01",
        "Withdrawal",
        8750,
        "Utility Payment",
        "Posted",
        "2026-09-07T13:25:00"
    ),
    (
        "TXN-000013",
        "SAV-100004-01",
        "Deposit",
        100000,
        "Transfer From Checking",
        "Posted",
        "2026-09-09T15:10:00"
    ),

    (
        "TXN-000014",
        "CHK-100005-01",
        "Withdrawal",
        5000,
        "ATM Withdrawal",
        "Posted",
        "2026-09-01T12:40:00"
    ),
    (
        "TXN-000015",
        "SAV-100005-01",
        "Deposit",
        20000,
        "Incoming Transfer",
        "Pending",
        "2026-09-11T10:30:00"
    ),
]

def main():
    # Create a fresh database using schema.sql
    connection = create_database()

    try:
        # Insert data in this order because of the foreign-key relationships:
        # Member must exist before an account can reference it.
        # Account must exist before a transaction can reference it.
        seed_members(connection)
        seed_accounts(connection)
        seed_transactions(connection)

        # Save all INSERT operations permanently
        connection.commit()

        print("Bank database created and seeded successfully.")
        print(f"Database location: {DATABASE_PATH}")

    finally:
        # Always close the database connection when finished
        connection.close()


# Run main() only when this file is executed directly.
if __name__ == "__main__":
    main()