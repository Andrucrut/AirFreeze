#!/usr/bin/env python3
"""
Вставить в БД много тестовых рейсов (по умолчанию 80).

Запуск из корня репозитория (см. README в комментарии внизу файла).
"""

from __future__ import annotations

import argparse
import asyncio
import os
import random
import sys
from datetime import date, datetime, timedelta, timezone

# Задайте DATABASE_URL до импорта приложения (или положите в .env).
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://airfreeze:airfreeze@localhost:5433/airfreeze",
)

from app.db.session import async_session_maker, engine  # noqa: E402
from app.models.flight import Flight  # noqa: E402

CITIES = [
    "Moscow",
    "Saint Petersburg",
    "Novosibirsk",
    "Yekaterinburg",
    "Kazan",
    "Sochi",
    "Vladivostok",
    "Berlin",
    "Paris",
    "London",
    "Istanbul",
    "Dubai",
    "Tokyo",
    "Bangkok",
    "New York",
    "Barcelona",
    "Rome",
    "Vienna",
    "Prague",
    "Helsinki",
]


def _random_pair(rng: random.Random) -> tuple[str, str]:
    a, b = rng.sample(CITIES, 2)
    return a, b


def _random_dep_utc(rng: random.Random, base: date) -> datetime:
    offset_days = rng.randint(0, 150)
    d = base + timedelta(days=offset_days)
    hour = rng.randint(5, 23)
    minute = rng.choice([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55])
    return datetime(d.year, d.month, d.day, hour, minute, tzinfo=timezone.utc)


async def seed_flights(count: int, seed: int | None) -> None:
    rng = random.Random(seed)
    today_utc = datetime.now(timezone.utc).date()

    async with async_session_maker() as session:
        for _ in range(count):
            from_c, to_c = _random_pair(rng)
            dep = _random_dep_utc(rng, today_utc)
            duration_hours = rng.uniform(1.0, 14.0)
            arr = dep + timedelta(hours=duration_hours)
            price = round(rng.uniform(75.0, 1200.0), 2)
            stops = rng.randint(0, 2)
            session.add(
                Flight(
                    from_city=from_c,
                    to_city=to_c,
                    departure_time=dep,
                    arrival_time=arr,
                    price=price,
                    stops=stops,
                )
            )
        await session.commit()

    await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Insert many random Flight rows into PostgreSQL.")
    parser.add_argument(
        "--count",
        type=int,
        default=80,
        help="How many flights to insert (default: 80)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional RNG seed for reproducible data",
    )
    args = parser.parse_args()
    if args.count < 1:
        print("--count must be >= 1", file=sys.stderr)
        sys.exit(1)

    asyncio.run(seed_flights(args.count, args.seed))
    print(f"Inserted {args.count} flights.")


if __name__ == "__main__":
    main()
