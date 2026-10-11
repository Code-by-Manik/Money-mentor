import csv


def read_csv_rows(file_path):
    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        return list(reader)


def get_csv_columns(file_path):
    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        return reader.fieldnames

def find_column(columns, possible_names):
    for column in columns:
        if column.strip().lower() in possible_names:
            return column

    return None


def get_amount_columns(columns):
    inflow_column = find_column(
        columns,
        {"money in", "deposit", "credit"}
    )

    outflow_column = find_column(
        columns,
        {"money out", "withdrawal", "debit"}
    )

    return inflow_column, outflow_column

def parse_amount(value):
    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    value = (
        value.replace("₹", "")
        .replace("$", "")
        .replace("£", "")
        .strip()
    )

    # Validate comma grouping before removing separators.
    import re

    number_pattern = (
        r"[+-]?"
        r"(?:\d+|\d{1,3}(?:,\d{3})+)"
        r"(?:\.\d+)?"
    )

    if not re.fullmatch(number_pattern, value):
        raise ValueError(f"Invalid amount format: {value}")

    return float(value.replace(",", ""))

from datetime import datetime


def parse_date(value):
    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d-%b-%Y",
        "%d-%b-%y",
    ]

    for date_format in formats:
        try:
            parsed_date = datetime.strptime(value, date_format)
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            continue

    raise ValueError(f"Unsupported date format: {value}")

def is_non_transaction_row(row):
    date_value = str(row.get("Date") or "").strip().lower()
    description = str(row.get("Description") or "").strip().lower()

    if date_value == "date":
        return True

    summary_words = {
        "total",
        "subtotal",
        "opening balance",
        "closing balance",
        "balance brought forward",
        "balance carried forward",
    }

    if description in summary_words:
        return True

    return False

def is_repeated_header(row, columns):
    for column in columns:
        value = str(row.get(column) or "").strip().lower()
        if value != column.strip().lower():
            return False

    return True

def normalize_csv_row(row, columns):
    date_column = find_column(
        columns,
        {"date", "transaction date", "txn date"}
    )

    description_column = find_column(
        columns,
        {"description", "narration", "details"}
    )

    balance_column = find_column(
        columns,
        {"balance", "closing balance"}
    )

    inflow_column, outflow_column = get_amount_columns(columns)

    transaction_date = (
        parse_date(row.get(date_column))
        if date_column else None
    )

    # Skip rows without a valid transaction date.
    if not transaction_date:
        return None

    description = (
        row.get(description_column) or ""
    ).strip() if description_column else ""

    # Preserve transactions that have no description.
    if not description:
        description = "Unknown transaction"

    money_in = row.get(inflow_column) if inflow_column else None
    money_out = row.get(outflow_column) if outflow_column else None

    if money_in is not None and str(money_in).strip():
        amount = parse_amount(money_in)
        direction = "inflow"
    elif money_out is not None and str(money_out).strip():
        amount = parse_amount(money_out)
        direction = "outflow"
    else:
        return None

    balance = (
        row.get(balance_column)
        if balance_column else None
    )

    return {
        "transaction_date": transaction_date,
        "value_date": None,
        "description": description,
        "amount": amount,
        "direction": direction,
        "balance": parse_amount(balance),
    }


def is_summary_row(row, columns):
    description_column = find_column(
        columns,
        {"description", "narration", "details"}
    )

    if not description_column:
        return False

    description = str(
        row.get(description_column) or ""
    ).strip().lower()

    summary_words = {
        "total",
        "subtotal",
        "opening balance",
        "closing balance",
        "balance brought forward",
        "balance carried forward",
    }

    return description in summary_words


def normalize_csv_rows(rows, columns):
    normalized_rows = []
    rejected_rows = []

    for row_number, row in enumerate(rows, start=2):
        if is_repeated_header(row, columns):
            continue

        if is_summary_row(row, columns):
            continue

        try:
            normalized_row = normalize_csv_row(row, columns)

            if normalized_row is not None:
                normalized_rows.append(normalized_row)

        except (ValueError, TypeError) as error:
            rejected_rows.append({
                "row_number": row_number,
                "reason": str(error),
                "data": row,
            })

    return normalized_rows, rejected_rows



def transaction_fingerprint(
    account_id,
    transaction_date,
    amount,
    direction,
    description,
    balance,
):
    import hashlib
    import json

    data = [
        account_id,
        transaction_date,
        round(float(amount), 2),
        direction,
        " ".join((description or "").lower().split()),
        round(float(balance), 2) if balance is not None else None,
    ]

    raw = json.dumps(data, separators=(",", ":"))

    return hashlib.sha256(raw.encode("utf-8")).hexdigest()



def normalize_merchant(description):
    text = (description or "").strip().lower()

    merchant_patterns = {
        "swiggy": ["swiggy"],
        "zomato": ["zomato"],
        "netflix": ["netflix"],
        "spotify": ["spotify"],
        "uber": ["uber"],
        "ola": ["ola"],
        "amazon": ["amazon"],
        "flipkart": ["flipkart"],
        "blinkit": ["blinkit"],
        "zepto": ["zepto"],
        "bigbasket": ["bigbasket"],
    }

    for merchant, patterns in merchant_patterns.items():
        if any(pattern in text for pattern in patterns):
            return merchant.title()

    return (description or "").strip()



from models import Transaction

def classify_transaction(description, direction):
    text = (description or "").strip().lower()

    if "salary" in text:
        return "income"

    if "atm" in text or "cash withdrawal" in text:
        return "withdrawal"

    if direction == "outflow":
        return "expense"

    if direction == "inflow":
        return "income"

    return "unknown"



def classify_category(description, transaction_type):
    text = (description or "").strip().lower()

    # Income
    if transaction_type == "income":
        return "income"

    # Cash withdrawals
    if any(word in text for word in [
        "atm", "cash withdrawal", "cash wdl"
    ]):
        return "cash"


        # Health and medical
    if any(word in text for word in [
        "pharmacy", "medical store", "chemist",
        "hospital", "clinic", "doctor",
        "medplus", "pharmeasy", "netmeds"
    ]):
        return "health"

    # Food and groceries
    if any(word in text for word in [
        "swiggy", "zomato", "restaurant", "food",
        "dominos", "pizza", "cafe", "grocery", "groceries",
        "blinkit", "zepto", "bigbasket", "instamart",
        "dunzo", "mcdonald", "kfc", "subway"
    ]):
        return "food"

    # Transport
    if any(word in text for word in [
        "uber", "ola", "rapido", "metro", "fuel",
        "petrol", "diesel", "irctc", "redbus",
        "fastag", "toll", "parking","dmrc"
    ]):
        return "transport"

    # Subscriptions and digital services
    if any(word in text for word in [
        "netflix", "spotify", "prime video", "hotstar",
        "youtube premium", "subscription", "disney+",
        "jio cinema"
    ]):
        return "subscriptions"

    # Shopping
    if any(word in text for word in [
        "amazon", "flipkart", "myntra", "meesho",
        "ajio", "nykaa", "shopsy"
    ]):
        return "shopping"

    # Bills and utilities
    if any(word in text for word in [
        "electricity", "water bill", "gas bill", "broadband",
        "mobile recharge", "recharge", "jio", "airtel", "vi ",
        "bescom", "dhbvn", "uhbvn", "postpaid", "bill payment",
        "telephone bill"
    ]):
        return "bills"

    # Transfers and financial services
    if any(word in text for word in [
        "neft", "imps", "rtgs", "upi transfer", "bank transfer"
    ]):
        return "transfers"

    return "other"



def import_csv_transactions(
    file_path,
    account_id,
    statement_id,
    db,
):
    rows = read_csv_rows(file_path)
    columns = get_csv_columns(file_path)

    normalized_rows, rejected_rows = normalize_csv_rows(rows, columns)

    imported_transactions = []

    # Build fingerprints for transactions already in this account.
    existing_transactions = (
        db.query(Transaction)
        .filter(Transaction.account_id == account_id)
        .all()
    )

    existing_fingerprints = set()

    for existing in existing_transactions:
        fingerprint = transaction_fingerprint(
            existing.account_id,
            existing.transaction_date,
            existing.amount,
            existing.direction,
            existing.description,
            existing.balance,
        )
        existing_fingerprints.add(fingerprint)

    for row in normalized_rows:
        transaction_type = classify_transaction(
            row["description"],
            row["direction"],
        )

        category = classify_category(
            row["description"],
            transaction_type,
        )

        fingerprint = transaction_fingerprint(
            account_id,
            row["transaction_date"],
            row["amount"],
            row["direction"],
            row["description"],
            row["balance"],
        )

        # Skip transactions we've already seen.
        if fingerprint in existing_fingerprints:
            continue

        transaction = Transaction(
            account_id=account_id,
            statement_id=statement_id,
            transaction_date=row["transaction_date"],
            value_date=row["value_date"],
            amount=row["amount"],
            direction=row["direction"],
            transaction_type=transaction_type,
            category=category,
            description=row["description"],
            merchant=normalize_merchant(row["description"]),
            balance=row["balance"],
            source="csv",
            fingerprint=fingerprint,
        )

        db.add(transaction)
        imported_transactions.append(transaction)

        # Also catches duplicates within the same uploaded file.
        existing_fingerprints.add(fingerprint)

    db.commit()

    return imported_transactions, rejected_rows