import sqlite3

conn = sqlite3.connect("upi_tracker.db")

print("Foreign keys on transactions:")
for row in conn.execute("PRAGMA foreign_key_list(transactions)"):
    print(row)

print("\nForeign keys on statements:")
for row in conn.execute("PRAGMA foreign_key_list(statements)"):
    print(row)

print("\nTransactions per account:")
for row in conn.execute(
    "SELECT account_id, COUNT(*) FROM transactions GROUP BY account_id"
):
    print(row)

conn.close()