from fastapi import FastAPI, Depends, HTTPException, UploadFile, File,Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Literal
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlencode
import os
import uuid
import httpx

from dotenv import load_dotenv

from database import engine, Base, SessionLocal
import models


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

SETU_CLIENT_ID = os.getenv("SETU_CLIENT_ID")
SETU_CLIENT_SECRET = os.getenv("SETU_CLIENT_SECRET")
SETU_PRODUCT_INSTANCE_ID = os.getenv("SETU_PRODUCT_INSTANCE_ID")

SETU_AUTH_URL = "https://uat.setu.co/api/v2/auth/token"
SETU_BASE_URL = "https://fiu-sandbox.setu.co"

# Public callback URL.
#
# This is used only for the mock consent flow unless
# you later enable the real Setu integration.
CALLBACK_URL = os.getenv(
    "CALLBACK_URL",
    "http://127.0.0.1:8000/aa/callback"
)


# ============================================================
# MOCK CONSENT STORAGE
# ============================================================

mock_consents = {}

# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="UPI Tracker",
    version="0.1.0",
    description=(
        "UPI transaction tracker with a local mock "
        "Account Aggregator consent flow."
    ),
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# DATABASE
# ============================================================

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ============================================================
# TRANSACTION SCHEMA
# ============================================================

class TransactionCreate(BaseModel):
    account_id: int
    statement_id: int

    transaction_date: str
    value_date: str | None = None
    time: str | None = None

    amount: float
    currency: str = "INR"

    direction: Literal["inflow", "outflow"]

    transaction_type: str
    payment_method: str | None = None

    description: str | None = None
    merchant: str | None = None
    counterparty: str | None = None
    reference_number: str | None = None

    balance: float | None = None

    source: str
    fingerprint: str | None = None


class AccountCreate(BaseModel):
    account_name: str
    account_type: str | None = None
    bank_name: str | None = None
    account_number_last4: str | None = None
    currency: str = "INR"


class StatementCreate(BaseModel):
    account_id: int
    filename: str
    file_format: str
    period_start: str | None = None
    period_end: str | None = None
    imported_at: str | None = None
    processing_status: str = "pending"


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():
    return {
        "message": "UPI Tracker is running!",
        "status": "ok",
        "version": "0.1.0",
        "account_aggregator": {
            "mode": "mock",
            "status": "enabled",
        },
        "endpoints": {
            "transactions": "/transactions",
            "summary": "/summary",
            "app_summary": "/summary/apps",
            "create_consent": "/aa/create-consent",
            "callback": "/aa/callback",
        },
    }


# ============================================================
# TRANSACTIONS
# ============================================================

@app.get("/transactions")
def get_transactions(
    start_date: str | None = None,
    end_date: str | None = None,
    direction: str | None = None,
    transaction_type: str | None = None,
    payment_method: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Transaction)

    if start_date:
        query = query.filter(
            models.Transaction.transaction_date >= start_date
        )

    if end_date:
        query = query.filter(
            models.Transaction.transaction_date <= end_date
        )

    if direction:
        query = query.filter(
            models.Transaction.direction == direction
        )

    if transaction_type:
        query = query.filter(
            models.Transaction.transaction_type == transaction_type
        )

    if payment_method:
        query = query.filter(
            models.Transaction.payment_method == payment_method
        )

    return query.all()


# ============================================================
# ADD TRANSACTION
# ============================================================

@app.post("/transactions")
def add_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
):
    new_transaction = models.Transaction(
        account_id=transaction.account_id,
        statement_id=transaction.statement_id,

        transaction_date=transaction.transaction_date,
        value_date=transaction.value_date,
        time=transaction.time,

        amount=transaction.amount,
        currency=transaction.currency,

        direction=transaction.direction,

        transaction_type=transaction.transaction_type,
        payment_method=transaction.payment_method,

        description=transaction.description,
        merchant=transaction.merchant,
        counterparty=transaction.counterparty,
        reference_number=transaction.reference_number,

        balance=transaction.balance,

        source=transaction.source,
        fingerprint=transaction.fingerprint,
    )

    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    return {
        "message": "Transaction added successfully",
        "transaction": new_transaction,
    }


@app.post("/accounts")
def create_account(
    account: AccountCreate,
    db: Session = Depends(get_db),
):
    new_account = models.Account(
        account_name=account.account_name,
        account_type=account.account_type,
        bank_name=account.bank_name,
        account_number_last4=account.account_number_last4,
        currency=account.currency,
    )

    db.add(new_account)
    db.commit()
    db.refresh(new_account)

    return {
        "message": "Account created successfully",
        "account": new_account,
    }


@app.get("/accounts")
def get_accounts(
    db: Session = Depends(get_db),
):
    return db.query(models.Account).all()



@app.post("/statements")
def create_statement(
    statement: StatementCreate,
    db: Session = Depends(get_db),
):
    account = (
        db.query(models.Account)
        .filter(models.Account.id == statement.account_id)
        .first()
    )

    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )

    new_statement = models.Statement(
        account_id=statement.account_id,
        filename=statement.filename,
        file_format=statement.file_format,
        period_start=statement.period_start,
        period_end=statement.period_end,
        imported_at=(
            statement.imported_at
            or datetime.now(timezone.utc).isoformat()
        ),
        processing_status=statement.processing_status,
    )

    db.add(new_statement)
    db.commit()
    db.refresh(new_statement)

    return {
        "message": "Statement created successfully",
        "statement": new_statement,
    }





@app.get("/statements")
def get_statements(
    account_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Statement)

    if account_id:
        query = query.filter(
            models.Statement.account_id == account_id
        )

    return query.all()


# ============================================================
# CSV IMPORT
# ============================================================

@app.post("/statements/import-csv")
def import_csv_statement(
    account_id: int,
    statement_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    account = (
        db.query(models.Account)
        .filter(models.Account.id == account_id)
        .first()
    )

    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )

    statement = (
        db.query(models.Statement)
        .filter(models.Statement.id == statement_id)
        .first()
    )

    if not statement:
        raise HTTPException(
            status_code=404,
            detail="Statement not found",
        )

    if statement.account_id != account_id:
        raise HTTPException(
            status_code=400,
            detail="Statement does not belong to this account",
        )

    file_path = f"temp_{file.filename}"

    with open(file_path, "wb") as output_file:
        output_file.write(file.file.read())

    try:
        from importers.csv_parser import import_csv_transactions

        transactions, rejected_rows = import_csv_transactions(
            file_path=file_path,
            account_id=account_id,
            statement_id=statement_id,
            db=db,
        )

        return {
        "message": "CSV imported successfully",
        "transaction_count": len(transactions),
        "rejected_count": len(rejected_rows),
        "rejected_rows": rejected_rows,
        }

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)





# ============================================================
# SUMMARY
# ============================================================

@app.get("/summary")
def get_summary(
    start_date: str | None = None,
    end_date: str | None = None,
    direction: str | None = None,
    transaction_type: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Transaction)

    if start_date:
        query = query.filter(
            models.Transaction.transaction_date >= start_date
        )

    if end_date:
        query = query.filter(
            models.Transaction.transaction_date <= end_date
        )

    if direction:
        query = query.filter(
            models.Transaction.direction == direction
        )

    if transaction_type:
        query = query.filter(
            models.Transaction.transaction_type == transaction_type
        )

    transactions = query.all()

    total_inflow = 0.0
    total_outflow = 0.0

    for transaction in transactions:

        if transaction.direction == "inflow":
            total_inflow += float(transaction.amount)

        elif transaction.direction == "outflow":
            total_outflow += float(transaction.amount)

    net_amount = total_inflow - total_outflow

    return {
        "total_inflow": total_inflow,
        "total_outflow": total_outflow,
        "net_amount": net_amount,
        "transaction_count": len(transactions),
    }

# ============================================================
# APP SUMMARY
# ============================================================

@app.get("/summary/apps")
def get_category_summary(
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Transaction)

    if start_date:
        query = query.filter(
            models.Transaction.transaction_date >= start_date
        )

    if end_date:
        query = query.filter(
            models.Transaction.transaction_date <= end_date
        )

    transactions = query.all()

    category_summary = {}

    for transaction in transactions:

        if transaction.category not in category_summary:
            category_summary[transaction.category] = {
                "total_spent": 0.0,
                "transaction_count": 0,
            }

        if transaction.transaction_type in ("expense", "withdrawal"):
            category_summary[
                transaction.category
            ]["total_spent"] += float(transaction.amount)

            category_summary[
                transaction.category
            ]["transaction_count"] += 1

    return category_summary


# ============================================================
# AA CALLBACK - GET
# ============================================================

@app.get("/aa/callback")
async def aa_callback_get(request: Request):

    query_params = dict(request.query_params)

    consent_id = query_params.get("consentId")
    status = query_params.get("status")

    if consent_id:
        mock_consents[consent_id] = {
            "consent_id": consent_id,
            "status": status or "UNKNOWN",
            "mode": query_params.get("mode", "mock"),
            "updated_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

    return {
        "status": "success",
        "message": "AA callback processed successfully",
        "mode": "mock",
        "consent": (
            mock_consents.get(consent_id)
            if consent_id
            else None
        ),
        "query_params": query_params,
    }


# ============================================================
# AA CALLBACK - POST
# ============================================================

@app.post("/aa/callback")
async def aa_callback_post(request: Request):

    try:
        data = await request.json()

    except Exception:
        body = await request.body()

        data = {
            "raw_body": body.decode(
                "utf-8",
                errors="replace",
            )
        }

    consent_id = (
        data.get("consentId")
        if isinstance(data, dict)
        else None
    )

    status = (
        data.get("status")
        if isinstance(data, dict)
        else None
    )

    if consent_id:
        mock_consents[consent_id] = {
            "consent_id": consent_id,
            "status": status or "UNKNOWN",
            "mode": "mock",
            "updated_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

    print()
    print("=" * 60)
    print("AA CALLBACK RECEIVED")
    print("=" * 60)
    print(data)
    print("=" * 60)
    print()

    return {
        "status": "success",
        "message": "AA callback processed successfully",
        "mode": "mock",
        "consent": (
            mock_consents.get(consent_id)
            if consent_id
            else None
        ),
        "data": data,
    }


# ============================================================
# SETU AUTHENTICATION
# ============================================================

async def get_setu_token():
    """
    Real Setu authentication helper.

    This function is kept so the real integration can be
    enabled later. The mock consent endpoint below does not
    use it.
    """

    if not SETU_CLIENT_ID:
        raise RuntimeError(
            "SETU_CLIENT_ID is missing from .env"
        )

    if not SETU_CLIENT_SECRET:
        raise RuntimeError(
            "SETU_CLIENT_SECRET is missing from .env"
        )

    auth_body = {
        "clientID": SETU_CLIENT_ID,
        "secret": SETU_CLIENT_SECRET,
    }

    print()
    print("=" * 60)
    print("SETU AUTHENTICATION")
    print("=" * 60)
    print("Auth URL:", SETU_AUTH_URL)
    print(
        "Client ID present:",
        bool(SETU_CLIENT_ID),
    )
    print(
        "Client secret present:",
        bool(SETU_CLIENT_SECRET),
    )
    print("=" * 60)

    async with httpx.AsyncClient(
        timeout=30
    ) as client:

        response = await client.post(
            SETU_AUTH_URL,
            json=auth_body,
        )

    try:
        response_data = response.json()

    except Exception:
        response_data = {
            "raw_response": response.text,
        }

    if response.status_code != 200:
        raise RuntimeError(
            f"Setu authentication failed "
            f"(HTTP {response.status_code}): "
            f"{response_data}"
        )

    token = None

    if isinstance(response_data, dict):

        data = response_data.get("data")

        if isinstance(data, dict):
            token = data.get("token")

        if not token:
            token = response_data.get("token")

    if not token:
        raise RuntimeError(
            "Setu authentication succeeded but "
            f"token was not found: {response_data}"
        )

    return token


@app.get("/aa/consent/{consent_id}")
async def get_mock_consent(consent_id: str):

    consent = mock_consents.get(consent_id)

    if not consent:
        raise HTTPException(
            status_code=404,
            detail="Consent not found",
        )

    return {
        "status": "success",
        "consent": consent,
    }

@app.post("/aa/fetch-data")
async def fetch_mock_data(
    consent_id: str,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # CHECK CONSENT
    # --------------------------------------------------------

    consent = mock_consents.get(consent_id)

    if not consent:
        raise HTTPException(
            status_code=404,
            detail="Consent not found"
        )

    if consent["status"] != "APPROVED":
        raise HTTPException(
            status_code=400,
            detail="Consent is not approved"
        )

    # --------------------------------------------------------
    # PREVENT DUPLICATE FETCH FOR SAME CONSENT
    # --------------------------------------------------------

    existing_transactions = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.consent_id == consent_id
        )
        .all()
    )

    if existing_transactions:
        return {
            "status": "success",
            "mode": "mock",
            "consent_id": consent_id,
            "message": "Mock financial data already fetched",
            "transactions": existing_transactions
        }

    # --------------------------------------------------------
    # MOCK BANK TRANSACTIONS
    # --------------------------------------------------------

    now = datetime.now()

    mock_transactions = [
        {
            "amount": 250.00,
            "type": "paid",
            "network": "UPI",
            "app": "PhonePe",
            "description": "Grocery Store"
        },
        {
            "amount": 1200.00,
            "type": "paid",
            "network": "UPI",
            "app": "Google Pay",
            "description": "Electricity Bill"
        },
        {
            "amount": 5000.00,
            "type": "received",
            "network": "UPI",
            "app": "PhonePe",
            "description": "Salary"
        },
        {
            "amount": 350.00,
            "type": "paid",
            "network": "UPI",
            "app": "Paytm",
            "description": "Restaurant"
        }
    ]

    saved_transactions = []

    for item in mock_transactions:

        transaction = models.Transaction(
            amount=item["amount"],
            type=item["type"],
            network=item["network"],
            app=item["app"],
            description=item["description"],
            date=now.strftime("%Y-%m-%d"),
            time=now.strftime("%H:%M:%S"),
            consent_id=consent_id
        )

        db.add(transaction)
        saved_transactions.append(transaction)

    db.commit()

    for transaction in saved_transactions:
        db.refresh(transaction)

    return {
        "status": "success",
        "mode": "mock",
        "consent_id": consent_id,
        "message": "Mock financial data fetched successfully",
        "transactions": saved_transactions
    }

# ============================================================
# TEST SETU AUTH
# ============================================================

@app.get("/setu/test-auth")
async def test_setu_auth():
    """
    Tests real Setu authentication.

    This endpoint is separate from the mock AA consent flow.
    """

    try:
        token = await get_setu_token()

        return {
            "status": "success",
            "message": "Setu authentication successful",
            "token_received": bool(token),
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e),
        }


# ============================================================
# MOCK ACCOUNT AGGREGATOR CONSENT
# ============================================================

@app.post("/aa/create-consent")
async def create_consent():
    """
    Create a LOCAL MOCK Account Aggregator consent.

    IMPORTANT:
    This endpoint deliberately does NOT call Setu.

    We are using this while the Setu FIU onboarding/KYC
    is not completed.

    This means:
      - No PAN required
      - No Setu KYC required
      - No Setu consent validation
      - No Fair Usage Policy validation
      - No real bank data
      - No real Account Aggregator consent

    It is only for developing/testing the UPI Tracker.
    """

    now = datetime.now(timezone.utc)

    from_date = now - timedelta(days=365)

    from_timestamp = (
        from_date
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )

    to_timestamp = (
        now
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )

    # --------------------------------------------------------
    # Generate a local consent ID
    # --------------------------------------------------------

    consent_id = f"mock-consent-{uuid.uuid4().hex[:12]}"

    # --------------------------------------------------------
    # Mock consent
    # --------------------------------------------------------

    consent = {
        "id": consent_id,
        "status": "CREATED",
        "mode": "MOCK",
        "vua": "9999999999",
        "consentTypes": [
            "TRANSACTIONS"
        ],
        "fiTypes": [
            "DEPOSIT"
        ],
        "fetchType": "ONETIME",
        "consentMode": "VIEW",
        "dataRange": {
            "from": from_timestamp,
            "to": to_timestamp,
        },
        "consentDuration": {
            "unit": "MONTH",
            "value": 1,
        },
        "dataLife": {
            "unit": "DAY",
            "value": 1,
        },
        "frequency": {
            "unit": "DAY",
            "value": 1,
        },
        "purpose": {
            "code": "102",
            "category": "PERSONAL_FINANCE_MANAGEMENT",
            "text": (
                "Customer spending patterns "
                "and budget analysis"
            ),
        },
        "redirectUrl": CALLBACK_URL,
        "createdAt": to_timestamp,
    }

    # --------------------------------------------------------
    # Mock redirect URL
    # --------------------------------------------------------

    redirect_query = urlencode(
        {
            "consentId": consent_id,
            "status": "APPROVED",
            "mode": "mock",
        }
    )

    mock_redirect_url = (
        f"{CALLBACK_URL}?{redirect_query}"
    )

    # --------------------------------------------------------
    # Debug output
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("MOCK AA CONSENT CREATED")
    print("=" * 60)
    print("Consent ID:")
    print(consent_id)
    print()
    print("Redirect URL:")
    print(mock_redirect_url)
    print("=" * 60)
    print()

    # --------------------------------------------------------
    # Return success
    # --------------------------------------------------------

    return {
        "status": "success",
        "mode": "mock",
        "message": (
            "Mock Account Aggregator consent "
            "created successfully"
        ),
        "consent": consent,
        "redirect_url": mock_redirect_url,
        "next_step": (
            "Open redirect_url to simulate "
            "the consent callback."
        ),
    }


# ============================================================
# MOCK APPROVAL
# ============================================================

@app.get("/aa/mock-approve")
async def mock_approve(
    consent_id: str | None = None,
):
    """
    Optional helper endpoint for testing.

    Example:

        /aa/mock-approve?consent_id=mock-consent-123

    It simulates a customer approving the consent.
    """

    if not consent_id:
        consent_id = (
            f"mock-consent-{uuid.uuid4().hex[:12]}"
        )

    callback_url = (
        f"{CALLBACK_URL}"
        f"?consentId={consent_id}"
        f"&status=APPROVED"
        f"&mode=mock"
    )

    return {
        "status": "success",
        "mode": "mock",
        "consent_id": consent_id,
        "callback_url": callback_url,
        "message": (
            "Mock consent approved. "
            "Open callback_url to continue."
        ),
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "application": "UPI Tracker",
        "account_aggregator_mode": "mock",
    }