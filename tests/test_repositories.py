"""Tests for the repository layer's typed async CRUD methods."""

from datetime import UTC, datetime

import pytest

from app.models.company import Company
from app.models.financial_snapshot import FinancialSnapshot
from app.models.market_data_point import MarketDataPoint
from app.models.user import User
from app.models.valuation_version import ValuationVersion
from app.repositories.company import CompanyRepository
from app.repositories.financial_snapshot import FinancialSnapshotRepository
from app.repositories.market_data_point import MarketDataPointRepository
from app.repositories.user import UserRepository
from app.repositories.valuation_version import ValuationVersionRepository

pytestmark = pytest.mark.asyncio


async def test_company_repository_get_by_ticker(db_session) -> None:
    repo = CompanyRepository(db_session)
    repo.add(
        Company(
            ticker="REPOCO",
            exchange="NSE",
            name="Repo Test Co",
            screener_url="https://www.screener.in/company/REPOCO/consolidated/",
        )
    )
    await repo.flush()

    found = await repo.get_by_ticker("repoco")  # case-insensitive on purpose
    assert found is not None
    assert found.name == "Repo Test Co"

    assert await repo.exists_by_ticker("REPOCO") is True
    assert await repo.exists_by_ticker("NOPE") is False


async def test_financial_snapshot_repository_list_ordered_desc(db_session) -> None:
    company_repo = CompanyRepository(db_session)
    company = company_repo.add(
        Company(
            ticker="ORDERCO",
            exchange="NSE",
            name="Order Test Co",
            screener_url="https://www.screener.in/company/ORDERCO/consolidated/",
        )
    )
    await company_repo.flush()

    snap_repo = FinancialSnapshotRepository(db_session)
    now = datetime.now(UTC)
    for period in ("FY2022", "FY2024", "FY2023"):
        snap_repo.add(
            FinancialSnapshot(
                company_id=company.id,
                ticker=company.ticker,
                scraped_at=now,
                period=period,
                raw_html_payload="<html></html>",
                parsed_fields={},
                ingested_at=now,
            )
        )
    await snap_repo.flush()

    snapshots = await snap_repo.list_for_company(company.id)
    assert [s.period for s in snapshots] == ["FY2024", "FY2023", "FY2022"]


async def test_financial_snapshot_repository_upsert_is_idempotent(db_session) -> None:
    company_repo = CompanyRepository(db_session)
    company = company_repo.add(
        Company(
            ticker="UPSERTCO",
            exchange="NSE",
            name="Upsert Test Co",
            screener_url="https://www.screener.in/company/UPSERTCO/consolidated/",
        )
    )
    await company_repo.flush()

    snap_repo = FinancialSnapshotRepository(db_session)
    now = datetime.now(UTC)

    first = await snap_repo.upsert(
        company_id=company.id,
        ticker=company.ticker,
        scraped_at=now,
        period="FY2024",
        raw_html_payload="<html>v1</html>",
        parsed_fields={"revenue": 100.0},
        ingested_at=now,
    )
    assert first.parsed_fields["revenue"] == 100.0

    # Re-ingesting the same (company_id, period) must update in place, not duplicate.
    second = await snap_repo.upsert(
        company_id=company.id,
        ticker=company.ticker,
        scraped_at=now,
        period="FY2024",
        raw_html_payload="<html>v2</html>",
        parsed_fields={"revenue": 150.0},
        ingested_at=now,
    )
    assert second.id == first.id
    assert second.parsed_fields["revenue"] == 150.0

    all_snapshots = await snap_repo.list_for_company(company.id)
    assert len(all_snapshots) == 1


async def test_market_data_point_repository_get_latest(db_session) -> None:
    repo = MarketDataPointRepository(db_session)
    older = datetime(2024, 1, 1, tzinfo=UTC)
    newer = datetime(2024, 6, 1, tzinfo=UTC)

    repo.add(
        MarketDataPoint(
            ticker="MKTCO", exchange="NSE", price=100.0, fetched_at=older, source="screener"
        )
    )
    repo.add(
        MarketDataPoint(
            ticker="MKTCO", exchange="NSE", price=200.0, fetched_at=newer, source="screener"
        )
    )
    await repo.flush()

    latest = await repo.get_latest_for_ticker("MKTCO")
    assert latest is not None
    assert float(latest.price) == 200.0


async def test_valuation_version_repository_next_version_number(db_session) -> None:
    company_repo = CompanyRepository(db_session)
    company = company_repo.add(
        Company(
            ticker="VERCO",
            exchange="NSE",
            name="Version Test Co",
            screener_url="https://www.screener.in/company/VERCO/consolidated/",
        )
    )
    await company_repo.flush()

    version_repo = ValuationVersionRepository(db_session)

    assert await version_repo.next_version_number(company.id) == 1

    version_repo.add(
        ValuationVersion(
            version_number=1,
            company_id=company.id,
            model="dcf",
            inputs_snapshot={},
            result_snapshot={},
        )
    )
    await version_repo.flush()

    assert await version_repo.next_version_number(company.id) == 2


async def test_user_repository_get_by_email(db_session) -> None:
    repo = UserRepository(db_session)
    repo.add(User(email="repo.user@example.com", hashed_password="hash"))
    await repo.flush()

    found = await repo.get_by_email("repo.user@example.com")
    assert found is not None
    assert await repo.exists_by_email("nobody@example.com") is False
