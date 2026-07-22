"""initial schema: companies, financial_snapshots, market_data_points,
valuation_versions, users, refresh_tokens, export_jobs

Revision ID: 0001_initial_schema
Revises:
Create Date: 2025-01-01 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])

    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ticker", sa.String(length=32), nullable=False),
        sa.Column("exchange", sa.String(length=8), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("industry", sa.String(length=255), nullable=True),
        sa.Column("screener_url", sa.String(length=512), nullable=False),
        sa.Column(
            "use_consolidated", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("ticker", name="uq_companies_ticker"),
    )
    op.create_index("ix_companies_ticker", "companies", ["ticker"])

    op.create_table(
        "financial_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ticker", sa.String(length=32), nullable=False),
        sa.Column("scraped_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period", sa.String(length=16), nullable=False),
        sa.Column(
            "use_consolidated", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column("raw_html_payload", sa.Text(), nullable=False),
        sa.Column(
            "parsed_fields",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "company_id", "period", name="uq_financial_snapshot_company_period"
        ),
    )
    op.create_index(
        "ix_financial_snapshots_company_id", "financial_snapshots", ["company_id"]
    )
    op.create_index("ix_financial_snapshots_ticker", "financial_snapshots", ["ticker"])

    op.create_table(
        "market_data_points",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ticker", sa.String(length=32), nullable=False),
        sa.Column("exchange", sa.String(length=8), nullable=False),
        sa.Column("price", sa.Numeric(18, 4), nullable=False),
        sa.Column("market_cap", sa.Numeric(20, 2), nullable=True),
        sa.Column("pe_ratio", sa.Numeric(10, 2), nullable=True),
        sa.Column("book_value", sa.Numeric(18, 4), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "source", sa.String(length=32), nullable=False, server_default="screener"
        ),
    )
    op.create_index(
        "ix_market_data_points_ticker_fetched_at",
        "market_data_points",
        ["ticker", "fetched_at"],
    )

    op.create_table(
        "valuation_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("model", sa.String(length=32), nullable=False),
        sa.Column(
            "inputs_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column(
            "result_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column(
            "currency", sa.String(length=3), nullable=False, server_default="INR"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint(
            "company_id", "version_number", name="uq_valuation_version_company_num"
        ),
    )
    op.create_index(
        "ix_valuation_versions_company_id", "valuation_versions", ["company_id"]
    )

    export_job_status = postgresql.ENUM(
        "pending", "processing", "done", "failed", name="export_job_status"
    )
    export_job_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "export_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("valuation_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "processing",
                "done",
                "failed",
                name="export_job_status",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("file_path", sa.String(length=1024), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["valuation_version_id"], ["valuation_versions.id"], ondelete="CASCADE"
        ),
    )
    op.create_index("ix_export_jobs_user_id", "export_jobs", ["user_id"])
    op.create_index(
        "ix_export_jobs_valuation_version_id", "export_jobs", ["valuation_version_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_export_jobs_valuation_version_id", table_name="export_jobs")
    op.drop_index("ix_export_jobs_user_id", table_name="export_jobs")
    op.drop_table("export_jobs")
    postgresql.ENUM(name="export_job_status").drop(op.get_bind(), checkfirst=True)

    op.drop_index("ix_valuation_versions_company_id", table_name="valuation_versions")
    op.drop_table("valuation_versions")

    op.drop_index(
        "ix_market_data_points_ticker_fetched_at", table_name="market_data_points"
    )
    op.drop_table("market_data_points")

    op.drop_index("ix_financial_snapshots_ticker", table_name="financial_snapshots")
    op.drop_index(
        "ix_financial_snapshots_company_id", table_name="financial_snapshots"
    )
    op.drop_table("financial_snapshots")

    op.drop_index("ix_companies_ticker", table_name="companies")
    op.drop_table("companies")

    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
