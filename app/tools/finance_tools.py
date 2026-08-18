from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.database import engine
from app.database.models import Invoice


def find_customer(customer_name: str) -> dict[str, Any]:
    """
    Find customers by name using a case-insensitive partial match.

    Possible statuses:
    - FOUND
    - NOT_FOUND
    - AMBIGUOUS

    This is a read-only database operation.
    """

    if not customer_name or not customer_name.strip():
        return {
            "status": "NOT_FOUND",
            "message": "Customer name was not provided.",
            "matches": [],
        }

    search_term = customer_name.strip()

    with Session(engine) as session:
        statement = (
            select(
                Invoice.customer_id,
                Invoice.customer_name,
            )
            .where(
                Invoice.customer_name.ilike(
                    f"%{search_term}%"
                )
            )
            .distinct()
            .order_by(Invoice.customer_name)
        )

        results = session.execute(statement).all()

    matches = [
        {
            "customer_id": customer_id,
            "customer_name": customer_name,
        }
        for customer_id, customer_name in results
    ]

    if not matches:
        return {
            "status": "NOT_FOUND",
            "message": "No matching customer was found.",
            "matches": [],
        }

    if len(matches) > 1:
        return {
            "status": "AMBIGUOUS",
            "message": (
                "Multiple customers matched the provided name. "
                "Customer identification requires clarification."
            ),
            "matches": matches,
        }

    return {
        "status": "FOUND",
        "message": "Exactly one customer matched.",
        "matches": matches,
    }


def get_customer_invoices(
    customer_id: str,
) -> dict[str, Any]:
    """
    Return all invoices belonging to a verified customer.

    Possible statuses:
    - FOUND
    - NOT_FOUND

    This is a read-only database operation.
    """

    if not customer_id or not customer_id.strip():
        return {
            "status": "NOT_FOUND",
            "message": "Customer ID was not provided.",
            "customer_id": customer_id,
            "invoices": [],
        }

    normalized_customer_id = customer_id.strip()

    with Session(engine) as session:
        statement = (
            select(Invoice)
            .where(
                Invoice.customer_id
                == normalized_customer_id
            )
            .order_by(Invoice.invoice_date)
        )

        invoices = session.scalars(statement).all()

    if not invoices:
        return {
            "status": "NOT_FOUND",
            "message": (
                "No invoices were found for this customer ID."
            ),
            "customer_id": normalized_customer_id,
            "invoices": [],
        }

    invoice_records = [
        {
            "customer_id": invoice.customer_id,
            "customer_name": invoice.customer_name,
            "invoice_no": invoice.invoice_no,
            "invoice_date": invoice.invoice_date.isoformat(),
            "due_date": invoice.due_date.isoformat(),
            "invoice_amount": str(
                invoice.invoice_amount
            ),
            "amount_paid": str(
                invoice.amount_paid
            ),
            "outstanding_amount": str(
                invoice.outstanding_amount
            ),
            "aging_days": invoice.aging_days,
            "aging_bucket": invoice.aging_bucket,
            "currency": invoice.currency,
            "payment_status": invoice.payment_status,
        }
        for invoice in invoices
    ]

    return {
        "status": "FOUND",
        "message": (
            f"{len(invoice_records)} invoice(s) found."
        ),
        "customer_id": normalized_customer_id,
        "invoices": invoice_records,
    }


def get_customer_outstanding(
    customer_id: str,
) -> dict[str, Any]:
    """
    Return the financial summary for a verified customer.

    Possible statuses:
    - FOUND
    - NOT_FOUND

    This is a read-only database operation.
    """

    if not customer_id or not customer_id.strip():
        return {
            "status": "NOT_FOUND",
            "message": "Customer ID was not provided.",
            "customer_id": customer_id,
            "total_invoice_amount": "0.00",
            "total_amount_paid": "0.00",
            "total_outstanding": "0.00",
        }

    normalized_customer_id = customer_id.strip()

    with Session(engine) as session:
        customer_exists_statement = (
            select(Invoice.id)
            .where(
                Invoice.customer_id
                == normalized_customer_id
            )
            .limit(1)
        )

        customer_exists = (
            session.execute(
                customer_exists_statement
            ).first()
            is not None
        )

        if not customer_exists:
            return {
                "status": "NOT_FOUND",
                "message": (
                    "Customer ID was not found in the "
                    "finance database."
                ),
                "customer_id": normalized_customer_id,
                "total_invoice_amount": "0.00",
                "total_amount_paid": "0.00",
                "total_outstanding": "0.00",
            }

        statement = select(
            func.sum(Invoice.invoice_amount),
            func.sum(Invoice.amount_paid),
            func.sum(Invoice.outstanding_amount),
        ).where(
            Invoice.customer_id
            == normalized_customer_id
        )

        total_invoice, total_paid, total_outstanding = (
            session.execute(statement).one()
        )

    return {
        "status": "FOUND",
        "message": "Customer financial summary found.",
        "customer_id": normalized_customer_id,
        "total_invoice_amount": str(
            Decimal(total_invoice).quantize(
                Decimal("0.01")
            )
        ),
        "total_amount_paid": str(
            Decimal(total_paid).quantize(
                Decimal("0.01")
            )
        ),
        "total_outstanding": str(
            Decimal(total_outstanding).quantize(
                Decimal("0.01")
            )
        ),
    }


def get_customer_aging(
    customer_id: str,
) -> dict[str, Any]:
    """
    Return outstanding amounts grouped by aging bucket.

    Possible statuses:
    - FOUND
    - NOT_FOUND

    This is a read-only database operation.
    """

    if not customer_id or not customer_id.strip():
        return {
            "status": "NOT_FOUND",
            "message": "Customer ID was not provided.",
            "customer_id": customer_id,
            "aging": {},
            "total_outstanding": "0.00",
        }

    normalized_customer_id = customer_id.strip()

    with Session(engine) as session:
        customer_exists_statement = (
            select(Invoice.id)
            .where(
                Invoice.customer_id
                == normalized_customer_id
            )
            .limit(1)
        )

        customer_exists = (
            session.execute(
                customer_exists_statement
            ).first()
            is not None
        )

        if not customer_exists:
            return {
                "status": "NOT_FOUND",
                "message": (
                    "Customer ID was not found in the "
                    "finance database."
                ),
                "customer_id": normalized_customer_id,
                "aging": {},
                "total_outstanding": "0.00",
            }

        statement = (
            select(
                Invoice.aging_bucket,
                func.sum(
                    Invoice.outstanding_amount
                ),
            )
            .where(
                Invoice.customer_id
                == normalized_customer_id,
                Invoice.outstanding_amount > 0,
            )
            .group_by(Invoice.aging_bucket)
        )

        rows = session.execute(statement).all()

    aging = {
        aging_bucket: str(
            Decimal(amount).quantize(
                Decimal("0.01")
            )
        )
        for aging_bucket, amount in rows
    }

    total_outstanding = sum(
        (
            Decimal(amount)
            for amount in aging.values()
        ),
        Decimal("0.00"),
    )

    return {
        "status": "FOUND",
        "message": "Customer aging summary found.",
        "customer_id": normalized_customer_id,
        "aging": aging,
        "total_outstanding": str(
            total_outstanding.quantize(
                Decimal("0.01")
            )
        ),
    }