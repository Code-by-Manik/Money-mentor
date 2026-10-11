from sqlalchemy import Column, Integer, Float, String
from database import Base

class Account(Base):
    __tablename__ = "accounts"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    account_name = Column(
        String,
        nullable=False
    )

    account_type = Column(
        String,
        nullable=True
    )

    bank_name = Column(
        String,
        nullable=True
    )

    account_number_last4 = Column(
        String,
        nullable=True
    )

    currency = Column(
        String,
        nullable=False,
        default="INR"
    )


class Statement(Base):
    __tablename__ = "statements"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    account_id = Column(
        Integer,
        nullable=False
    )

    filename = Column(
        String,
        nullable=False
    )

    file_format = Column(
        String,
        nullable=False
    )

    period_start = Column(
        String,
        nullable=True
    )

    period_end = Column(
        String,
        nullable=True
    )

    imported_at = Column(
        String,
        nullable=False
    )

    processing_status = Column(
        String,
        nullable=False,
        default="pending"
    )

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    account_id = Column(
        Integer,
        nullable=False
    )

    statement_id = Column(
        Integer,
        nullable=False
    )

    transaction_date = Column(
        String,
        nullable=False
    )

    value_date = Column(
        String,
        nullable=True
    )

    time = Column(
        String,
        nullable=True
    )

    amount = Column(
        Float,
        nullable=False
    )

    currency = Column(
        String,
        nullable=False,
        default="INR"
    )

    direction = Column(
        String,
        nullable=False
    )

    transaction_type = Column(
        String,
        nullable=False
    )

    category = Column(
        String,
        nullable=True
    )

    payment_method = Column(
        String,
        nullable=True
    )

    description = Column(
        String,
        nullable=True
    )

    merchant = Column(
        String,
        nullable=True
    )

    counterparty = Column(
        String,
        nullable=True
    )

    reference_number = Column(
        String,
        nullable=True
    )

    balance = Column(
        Float,
        nullable=True
    )

    source = Column(
        String,
        nullable=False
    )

    fingerprint = Column(
        String,
        nullable=True
    )