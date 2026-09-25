# Used only to simulate a slow legacy banking response.
import time

from flask import Flask, render_template, request, abort

# Standard database connection helper
from db import get_connection

# Decimal avoids floating-point problems when working with money.
from decimal import Decimal, InvalidOperation

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    abort,
)

# Generate unique IDs for transfer transaction records
from uuid import uuid4

app = Flask(__name__)


# Jinja filter used in HTML to display cents as dollars.
# Example: 912540 -> $9,125.40
@app.template_filter("money")
def format_money(cents):
    return f"${cents / 100:,.2f}"


@app.route("/", methods=["GET", "POST"])
def member_search():
    """Search for a member by member ID."""

    member = None
    error = None

    if request.method == "POST":
        member_id = request.form.get("member_id", "").strip()

        connection = get_connection()

        try:
            # Parameterized query protects against SQL injection.
            member = connection.execute(
                """
                SELECT member_id, full_name, phone, email, status
                FROM members
                WHERE member_id = ?
                """,
                (member_id,),
            ).fetchone()

        finally:
            connection.close()

        # Valid business outcome: search completed, but member does not exist.
        if member is None:
            error = "Member not found."

    return render_template(
        "search.html",
        member=member,
        error=error,
    )


@app.route("/member/<member_id>")
def member_profile(member_id):
    """Display member information and all accounts owned by the member."""

    connection = get_connection()

    try:
        member = connection.execute(
            """
            SELECT *
            FROM members
            WHERE member_id = ?
            """,
            (member_id,),
        ).fetchone()

        # Stop if someone tries to open a member that does not exist.
        if member is None:
            abort(404)

        accounts = connection.execute(
            """
            SELECT *
            FROM accounts
            WHERE member_id = ?
            ORDER BY account_type
            """,
            (member_id,),
        ).fetchall()

        # Simulate an unusually slow legacy-system response.
        # Member 100003 will take a few seconds to load.
        if member_id == "100003":
            time.sleep(4)

        # Simulate a user who exists but the current teller
        # does not have permission to access their record.
        if member_id == "100004":
            return render_template(
             "permission_denied.html",
             member_id=member_id,
    ), 403

    finally:
        connection.close()

    return render_template(
        "member.html",
        member=member,
        accounts=accounts,
    )


@app.route("/account/<account_id>")
def account_details(account_id):
    """Display account balance and transaction history."""

    connection = get_connection()

    try:
        account = connection.execute(
            """
            SELECT *
            FROM accounts
            WHERE account_id = ?
            """,
            (account_id,),
        ).fetchone()

        if account is None:
            abort(404)

        # Show newest transactions first.
        transactions = connection.execute(
            """
            SELECT *
            FROM transactions
            WHERE account_id = ?
            ORDER BY created_at DESC
            """,
            (account_id,),
        ).fetchall()

    finally:
        connection.close()

    return render_template(
        "account.html",
        account=account,
        transactions=transactions,
    )

@app.route("/account/<source_account_id>/transfer", methods=["GET", "POST"])
def transfer(source_account_id):
    """
    Prepare an internal transfer.

    This screen validates the request first.
    No money moves until the user confirms on the next screen.
    """

    connection = get_connection()

    try:
        # Load the source account
        source_account = connection.execute(
            """
            SELECT *
            FROM accounts
            WHERE account_id = ?
            """,
            (source_account_id,),
        ).fetchone()

        if source_account is None:
            abort(404)

        # Find other accounts owned by the same member
        destination_accounts = connection.execute(
            """
            SELECT *
            FROM accounts
            WHERE member_id = ?
              AND account_id != ?
            """,
            (
                source_account["member_id"],
                source_account_id,
            ),
        ).fetchall()

        error = None

        if request.method == "POST":

            destination_account_id = request.form.get(
                "destination_account_id"
            )

            amount_text = request.form.get("amount", "").strip()

            try:
                # Convert entered dollars safely into cents
                amount_decimal = Decimal(amount_text)

                if amount_decimal <= 0:
                    raise ValueError

                amount_cents = int(amount_decimal * 100)

            except (InvalidOperation, ValueError):
                error = "Enter a valid transfer amount."

            if error is None:

                # Prevent overdrawing the source account
                if amount_cents > source_account["balance_cents"]:
                    error = "Insufficient funds."

            if error is None:

                destination_account = connection.execute(
                    """
                    SELECT *
                    FROM accounts
                    WHERE account_id = ?
                    """,
                    (destination_account_id,),
                ).fetchone()

                if destination_account is None:
                    error = "Destination account not found."

            if error is None:

                # Do NOT move money yet.
                # First show the user a confirmation screen.
                return render_template(
                    "transfer_confirm.html",
                    source_account=source_account,
                    destination_account=destination_account,
                    amount_cents=amount_cents,
                )

    finally:
        connection.close()

    return render_template(
        "transfer.html",
        source_account=source_account,
        destination_accounts=destination_accounts,
        error=error,
    )

@app.route("/account/<account_id>/transaction/<operation>", methods=["GET", "POST"])
def teller_transaction(account_id, operation):
    """
    Handle basic teller deposits and withdrawals.

    The same route is reused for both operations so we do not
    duplicate banking logic.
    """

    # Only these two operations are allowed through this screen.
    if operation not in {"deposit", "withdrawal"}:
        abort(404)

    connection = get_connection()

    try:
        # Load the selected account.
        account = connection.execute(
            """
            SELECT *
            FROM accounts
            WHERE account_id = ?
            """,
            (account_id,),
        ).fetchone()

        if account is None:
            abort(404)

        error = None

        # Only fully open accounts can perform teller transactions.
        # This gives us realistic Restricted/Frozen business rules.
        if account["status"] != "Open":
            error = (
                f"Transaction blocked: account status is "
                f"{account['status']}."
            )

        if request.method == "POST" and error is None:

            amount_text = request.form.get("amount", "").strip()

            try:
                # Convert entered dollars into Decimal first.
                amount_decimal = Decimal(amount_text)

                # Reject zero or negative transactions.
                if amount_decimal <= 0:
                    raise ValueError

                # Convert exact dollars to integer cents.
                amount_cents = int(amount_decimal * 100)

            except (InvalidOperation, ValueError):
                error = "Enter a valid amount greater than $0.00."

            if error is None:

                current_balance = account["balance_cents"]

                if operation == "withdrawal":

                    # Do not allow the account to go negative.
                    if amount_cents > current_balance:
                        error = "Insufficient funds."

                    else:
                        new_balance = current_balance - amount_cents

                else:
                    new_balance = current_balance + amount_cents

                if error is None:

                    # Update account balance.
                    connection.execute(
                        """
                        UPDATE accounts
                        SET balance_cents = ?
                        WHERE account_id = ?
                        """,
                        (new_balance, account_id),
                    )

                    # Record the banking transaction.
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
                        VALUES (
                            lower(hex(randomblob(8))),
                            ?,
                            ?,
                            ?,
                            ?,
                            'Posted',
                            datetime('now')
                        )
                        """,
                        (
                            account_id,
                            operation.capitalize(),
                            amount_cents,
                            f"Teller {operation}",
                        ),
                    )

                    # Save both database changes together.
                    connection.commit()

                    return redirect(
                        url_for(
                            "account_details",
                            account_id=account_id,
                        )
                    )

    finally:
        connection.close()

    return render_template(
        "transaction.html",
        account=account,
        operation=operation,
        error=error,
    )

@app.route("/transfer/confirm", methods=["POST"])
def confirm_transfer():
    """
    Execute a confirmed internal transfer.

    Important:
    The debit, credit, and transaction records are committed together.
    If anything fails, the whole operation is rolled back.
    """

    # Never blindly trust values coming back from HTML.
    source_account_id = request.form.get("source_account_id", "").strip()
    destination_account_id = request.form.get(
        "destination_account_id", ""
    ).strip()

    try:
        amount_cents = int(request.form.get("amount_cents", "0"))

        if amount_cents <= 0:
            raise ValueError

    except ValueError:
        return "Invalid transfer amount.", 400

    # Prevent transferring an account to itself.
    if source_account_id == destination_account_id:
        return "Source and destination accounts must be different.", 400

    connection = get_connection()

    try:
        # Start one database transaction.
        # This keeps the debit and credit together.
        connection.execute("BEGIN IMMEDIATE")

        # Re-read both accounts at confirmation time.
        # We do this because the balance may have changed
        # after the review screen was displayed.
        source_account = connection.execute(
            """
            SELECT *
            FROM accounts
            WHERE account_id = ?
            """,
            (source_account_id,),
        ).fetchone()

        destination_account = connection.execute(
            """
            SELECT *
            FROM accounts
            WHERE account_id = ?
            """,
            (destination_account_id,),
        ).fetchone()

        if source_account is None or destination_account is None:
            connection.rollback()
            return "Account not found.", 404

        # Internal transfer must stay within the same member.
        if source_account["member_id"] != destination_account["member_id"]:
            connection.rollback()
            return "Cross-member transfer is not allowed here.", 400

        # Do not allow transactions from restricted or frozen accounts.
        if source_account["status"] != "Open":
            connection.rollback()
            return (
                f"Transfer blocked: source account is "
                f"{source_account['status']}."
            ), 400

        if destination_account["status"] != "Open":
            connection.rollback()
            return (
                f"Transfer blocked: destination account is "
                f"{destination_account['status']}."
            ), 400

        # Re-check available funds immediately before moving money.
        if amount_cents > source_account["balance_cents"]:
            connection.rollback()
            return "Insufficient funds.", 400

        # Debit the source account.
        connection.execute(
            """
            UPDATE accounts
            SET balance_cents = balance_cents - ?
            WHERE account_id = ?
            """,
            (amount_cents, source_account_id),
        )

        # Credit the destination account.
        connection.execute(
            """
            UPDATE accounts
            SET balance_cents = balance_cents + ?
            WHERE account_id = ?
            """,
            (amount_cents, destination_account_id),
        )

        # Create a transaction record for money leaving the source.
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
            VALUES (?, ?, ?, ?, ?, 'Posted', datetime('now'))
            """,
            (
                f"TXN-{uuid4().hex[:12].upper()}",
                source_account_id,
                "Transfer Out",
                amount_cents,
                f"Transfer to {destination_account_id}",
            ),
        )

        # Create the matching transaction record
        # for money arriving in the destination.
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
            VALUES (?, ?, ?, ?, ?, 'Posted', datetime('now'))
            """,
            (
                f"TXN-{uuid4().hex[:12].upper()}",
                destination_account_id,
                "Transfer In",
                amount_cents,
                f"Transfer from {source_account_id}",
            ),
        )

        # Save ALL changes together.
        connection.commit()

    except Exception:
        # If any step fails, undo the entire transfer.
        connection.rollback()
        raise

    finally:
        connection.close()

    # Return to the source account so the teller can see
    # the updated balance and transaction history.
    return redirect(
        url_for(
            "account_details",
            account_id=source_account_id,
        )
    )


if __name__ == "__main__":
    # Development server for our local demo application.
    app.run(debug=True)