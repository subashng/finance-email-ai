from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, Integer, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy database models."""

    pass


class Invoice(Base):
    """Represents one customer invoice record."""

    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    customer_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    customer_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    invoice_no: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    due_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    invoice_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    amount_paid: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    outstanding_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    aging_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    aging_bucket: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    payment_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )


class WorkflowRun(Base):
    """
    Stores one Finance Email AI workflow execution.

    Includes both the original audit fields and the new
    Final Communication Record fields.
    """

    __tablename__ = "workflow_runs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    created_at: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # =========================================================
    # EXISTING / LEGACY AUDIT FIELD
    # =========================================================

    sender_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # =========================================================
    # FINAL COMMUNICATION RECORD
    # =========================================================

    customer_email_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    incoming_message_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    gmail_thread_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    subject: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    original_customer_email: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    action_taken: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # =========================================================
    # WORKFLOW STATUS
    # =========================================================

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    stage: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    agent2_decision: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    guardrails_decision: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    can_send: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    final_send_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # =========================================================
    # PERFORMANCE
    # =========================================================

    agent1_ms: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    agent2_ms: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    guardrails_ms: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    agent3_ms: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    total_ms: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    # =========================================================
    # GMAIL SEND
    # =========================================================

    gmail_message_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    gmail_sent_thread_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )