"""Seed the database with sample Indian listed companies.

Inserts three real NSE-listed companies (Reliance Industries, TCS, Infosys)
with pre-scraped-style financial snapshots so the valuation engine (Sprint 4)
has real data to compute against without waiting on the live Screener.in
scraper (Sprint 3).

Figures below are illustrative FY2024 consolidated figures in INR Cr, close
to (but not guaranteed to exactly match) real published results -- they exist
to exercise the schema and downstream DCF math, not as a source of financial
truth. `raw_html_payload` is a placeholder string; Sprint 3 fixtures (real
saved Screener.in HTML under tests/fixtures/screener/) will replace it when
the scraper lands, at which point this script can re-parse those fixtures
instead of hand-writing parsed_fields.

Run with `make seed` (invokes `python scripts/seed.py` inside the api
container).
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from app.db.session import AsyncSessionLocal
from app.models.company import Company
from app.models.financial_snapshot import FinancialSnapshot
from app.models.market_data_point import MarketDataPoint
from app.repositories.company import CompanyRepository
from app.repositories.market_data_point import MarketDataPointRepository

SEED_COMPANIES: list[dict[str, Any]] = [
    {
        "ticker": "RELIANCE",
        "exchange": "NSE",
        "name": "Reliance Industries Ltd",
        "industry": "Oil & Gas / Conglomerate",
        "market": {
            "price": 2980.50,
            "market_cap": 2018500.0,
            "pe_ratio": 27.4,
            "book_value": 1310.2,
        },
        "snapshots": [
            {
                "period": "FY2024",
                "parsed_fields": {
                    "revenue": 900000.0,
                    "operating_profit": 165000.0,
                    "net_profit": 79000.0,
                    "eps": 58.3,
                    "total_assets": 1720000.0,
                    "total_liabilities": 780000.0,
                    "total_debt": 310000.0,
                    "equity_capital": 6800.0,
                    "reserves": 890000.0,
                    "cash_and_equivalents": 21000.0,
                    "capex": 125000.0,
                    "operating_cash_flow": 175000.0,
                    "free_cash_flow": 50000.0,
                    "shares_outstanding": 1354.0,
                },
            },
            {
                "period": "FY2023",
                "parsed_fields": {
                    "revenue": 880000.0,
                    "operating_profit": 152000.0,
                    "net_profit": 73700.0,
                    "eps": 54.4,
                    "total_assets": 1650000.0,
                    "total_liabilities": 760000.0,
                    "total_debt": 305000.0,
                    "equity_capital": 6800.0,
                    "reserves": 815000.0,
                    "cash_and_equivalents": 19500.0,
                    "capex": 118000.0,
                    "operating_cash_flow": 160000.0,
                    "free_cash_flow": 42000.0,
                    "shares_outstanding": 1354.0,
                },
            },
        ],
    },
    {
        "ticker": "TCS",
        "exchange": "NSE",
        "name": "Tata Consultancy Services Ltd",
        "industry": "IT Services",
        "market": {
            "price": 3850.75,
            "market_cap": 1394000.0,
            "pe_ratio": 29.8,
            "book_value": 285.4,
        },
        "snapshots": [
            {
                "period": "FY2024",
                "parsed_fields": {
                    "revenue": 240900.0,
                    "operating_profit": 60600.0,
                    "net_profit": 46000.0,
                    "eps": 127.4,
                    "total_assets": 128000.0,
                    "total_liabilities": 42000.0,
                    "total_debt": 200.0,
                    "equity_capital": 366.0,
                    "reserves": 82000.0,
                    "cash_and_equivalents": 8800.0,
                    "capex": 3600.0,
                    "operating_cash_flow": 44000.0,
                    "free_cash_flow": 40400.0,
                    "shares_outstanding": 361.0,
                },
            },
            {
                "period": "FY2023",
                "parsed_fields": {
                    "revenue": 225500.0,
                    "operating_profit": 56600.0,
                    "net_profit": 42100.0,
                    "eps": 116.5,
                    "total_assets": 118000.0,
                    "total_liabilities": 39000.0,
                    "total_debt": 200.0,
                    "equity_capital": 366.0,
                    "reserves": 74500.0,
                    "cash_and_equivalents": 7900.0,
                    "capex": 3300.0,
                    "operating_cash_flow": 40200.0,
                    "free_cash_flow": 36900.0,
                    "shares_outstanding": 361.0,
                },
            },
        ],
    },
    {
        "ticker": "INFY",
        "exchange": "NSE",
        "name": "Infosys Ltd",
        "industry": "IT Services",
        "market": {"price": 1520.30, "market_cap": 631000.0, "pe_ratio": 25.1, "book_value": 210.6},
        "snapshots": [
            {
                "period": "FY2024",
                "parsed_fields": {
                    "revenue": 153670.0,
                    "operating_profit": 34700.0,
                    "net_profit": 26750.0,
                    "eps": 64.4,
                    "total_assets": 105000.0,
                    "total_liabilities": 38000.0,
                    "total_debt": 200.0,
                    "equity_capital": 2100.0,
                    "reserves": 64000.0,
                    "cash_and_equivalents": 12300.0,
                    "capex": 3100.0,
                    "operating_cash_flow": 27700.0,
                    "free_cash_flow": 24600.0,
                    "shares_outstanding": 415.0,
                },
            },
            {
                "period": "FY2023",
                "parsed_fields": {
                    "revenue": 146770.0,
                    "operating_profit": 32900.0,
                    "net_profit": 24100.0,
                    "eps": 58.0,
                    "total_assets": 98000.0,
                    "total_liabilities": 36500.0,
                    "total_debt": 200.0,
                    "equity_capital": 2100.0,
                    "reserves": 59500.0,
                    "cash_and_equivalents": 10800.0,
                    "capex": 2900.0,
                    "operating_cash_flow": 25100.0,
                    "free_cash_flow": 22200.0,
                    "shares_outstanding": 415.0,
                },
            },
        ],
    },
]


def _screener_url(ticker: str) -> str:
    return f"https://www.screener.in/company/{ticker}/consolidated/"


def _placeholder_html(ticker: str, period: str) -> str:
    return (
        f"<!-- placeholder raw_html_payload for {ticker} {period}. "
        "Real fixtures land in Sprint 3 under tests/fixtures/screener/ "
        "and the ingestion writer will overwrite this via upsert(). -->"
    )


async def seed() -> None:
    now = datetime.now(UTC)

    async with AsyncSessionLocal() as session:
        company_repo = CompanyRepository(session)
        market_repo = MarketDataPointRepository(session)

        for entry in SEED_COMPANIES:
            existing = await company_repo.get_by_ticker(entry["ticker"])
            if existing is not None:
                print(f"  - {entry['ticker']} already seeded, skipping")
                continue

            company = Company(
                ticker=entry["ticker"],
                exchange=entry["exchange"],
                name=entry["name"],
                industry=entry["industry"],
                screener_url=_screener_url(entry["ticker"]),
                use_consolidated=True,
            )
            company_repo.add(company)
            await session.flush()  # populate company.id for FK use below

            for snap in entry["snapshots"]:
                session.add(
                    FinancialSnapshot(
                        company_id=company.id,
                        ticker=company.ticker,
                        scraped_at=now,
                        period=snap["period"],
                        use_consolidated=True,
                        raw_html_payload=_placeholder_html(entry["ticker"], snap["period"]),
                        parsed_fields=snap["parsed_fields"],
                        ingested_at=now,
                    )
                )

            market = entry["market"]
            market_repo.add(
                MarketDataPoint(
                    ticker=company.ticker,
                    exchange=company.exchange,
                    price=market["price"],
                    market_cap=market["market_cap"],
                    pe_ratio=market["pe_ratio"],
                    book_value=market["book_value"],
                    fetched_at=now,
                    source="screener",
                )
            )

            print(f"  + seeded {entry['ticker']} ({len(entry['snapshots'])} snapshots)")

        await session.commit()

    print("Seed complete.")


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
