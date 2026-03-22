"""Проверка номера карты при добавлении (без хранения PAN/CVC)."""

from __future__ import annotations


def normalize_card_number(raw: str) -> str:
    s = "".join(c for c in raw if c.isdigit())
    if not (13 <= len(s) <= 19):
        raise ValueError("Card number must contain 13–19 digits")
    return s


def luhn_valid(number: str) -> bool:
    """Алгоритм Луна для проверки контрольной суммы номера."""
    digits = [int(c) for c in number]
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def last_four_digits(number: str) -> str:
    return number[-4:]


def validate_cvc(raw: str) -> None:
    s = raw.strip()
    if not s.isdigit() or len(s) not in (3, 4):
        raise ValueError("CVC must be 3 or 4 digits")
