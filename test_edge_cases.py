from importers.csv_parser import parse_amount, parse_date
from importers.csv_parser import (
    read_csv_rows,
    get_csv_columns,
    normalize_csv_rows,
)

file_path = "edge_case_test.csv"

rows = read_csv_rows(file_path)
columns = get_csv_columns(file_path)
results, rejected_rows = normalize_csv_rows(rows, columns)

print(f"Valid transactions: {len(results)}")
print(f"Rejected rows: {len(rejected_rows)}")

for row in results:
    print(row)

for row in rejected_rows:
    print("Rejected:", row)


print("\nTesting invalid amount:")

bad_rows = [
    {
        "Date": "2026-09-02",
        "Description": "Bad Amount Test",
        "Money Out": "12,34.56",
        "Money In": "",
        "Balance": "9000",
    }
]

bad_results, bad_rejected = normalize_csv_rows(
    bad_rows,
    columns,
)

print("Valid transactions:", len(bad_results))
print("Rejected rows:", len(bad_rejected))

for row in bad_rejected:
    print("Rejected:", row)