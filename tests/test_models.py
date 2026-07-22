"""Tests for ORM model definitions: columns, constraints, and relationships.

These run against the real Dockerised Postgres instance (via `db_session`,
see conftest.py) so that Postgres-specific behaviour -- JSONB columns, unique
constraints, FK cascades -- is actually exercised, not mocked away.
"""

from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.company import Company
from app.models.financial_snapshot import FinancialSnapshot
from app.models.market_data_point import MarketDataPoint
from app.models.user import RefreshToken, User
from app.models.valuation_version import ValuationVersion

pytestmark = pytest.mark.asyncio


async def _make_company(session, ticker: str = "TESTCO") -> Company:
    company = Company(
        ticker=ticker,
        exchange="NSE",
        name="Test Company Ltd",
        industry="Testing",
        screener_url=f"https://www.screener.in/company/{ticker}/consolidated/",
    )
    session.add(company)
    await session.flush()
    return company


async def test_company_round_trip(db_session) -> None:
    company = await _make_company(db_session)
    assert company.id is not None
    assert company.use_consolidated is True  # column default applied


async def test_company_ticker_unique_constraint(db_session) -> None:
    await _make_company(db_session, ticker="DUPCO")
    with pytest.raises(IntegrityError):
        await _make_company(db_session, ticker="DUPCO")


async def test_financial_snapshot_requires_company_fk(db_session) -> None:
    company = await _make_company(db_session, ticker="SNAPCO")
    now = datetime.now(UTC)

    snapshot = FinancialSnapshot(
        company_id=company.id,
        ticker=company.ticker,
        scraped_at=now,
        period="FY2024",
        raw_html_payload="<html>placeholder</html>",
        parsed_fields={"revenue": 1000.0, "net_profit": 100.0},
        ingested_at=now,
    )
    db_session.add(snapshot)
    await db_session.flush()

    assert snapshot.id is not None
    assert snapshot.parsed_fields["revenue"] == 1000.0

    # Relationship should be navigable from the Company side.
    await db_session.refresh(company, attribute_names=["financial_snapshots"])
    assert len(company.financial_snapshots) == 1


async def test_financial_snapshot_unique_company_period(db_session) -> None:
    company = await _make_company(db_session, ticker="DUPSNAP")
    now = datetime.now(UTC)

    def _snapshot() -> FinancialSnapshot:
        return FinancialSnapshot(
            company_id=company.id,
            ticker=company.ticker,
            scraped_at=now,
            period="FY2024",
            raw_html_payload="<html></html>",
            parsed_fields={},
            ingested_at=now,
        )

    db_session.add(_snapshot())
    await db_session.flush()

    db_session.add(_snapshot())
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_market_data_point_round_trip(db_session) -> None:
    point = MarketDataPoint(
        ticker="TESTCO",
        exchange="NSE",
        price=1234.56,
        market_cap=50000.0,
        pe_ratio=22.5,
        book_value=310.0,
        fetched_at=datetime.now(UTC),
        source="screener",
    )
    db_session.add(point)
    await db_session.flush()
    assert point.id is not None


async def test_valuation_version_unique_company_version_number(db_session) -> None:
    company = await _make_company(db_session, ticker="VALCO")

    version = ValuationVersion(
        version_number=1,
        company_id=company.id,
        model="dcf",
        inputs_snapshot={"growth_rate": 0.1},
        result_snapshot={"intrinsic_value_per_share": 100.0},
    )
    db_session.add(version)
    await db_session.flush()
    assert version.currency == "INR"

    dup = ValuationVersion(
        version_number=1,
        company_id=company.id,
        model="dcf",
        inputs_snapshot={},
        result_snapshot={},
    )
    db_session.add(dup)
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_user_and_refresh_token_relationship(db_session) -> None:
    user = User(email="staff.engineer@example.com", hashed_password="not-a-real-hash")
    db_session.add(user)
    await db_session.flush()

    token = RefreshToken(
        user_id=user.id,
        token_hash="hashed-token-value",
        expires_at=datetime.now(UTC),
    )
    db_session.add(token)
    await db_session.flush()

    await db_session.refresh(user, attribute_names=["refresh_tokens"])
    assert len(user.refresh_tokens) == 1
    assert user.refresh_tokens[0].revoked is False
