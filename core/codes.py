import re
from datetime import datetime, timedelta, timezone

CODE_RE_ACCOUNT = re.compile(r"^[A-Z]{4}_[A-Z0-9]{4}_[A-Z0-9]{4}_[A-Z0-9]{4}$")
CODE_RE_UNBAN = re.compile(r"^[A-Z]{4}_[A-Z]{4}_[A-Z]{4}_[A-Z]{4}$")


def is_valid_account_code(code: str) -> bool:
    return bool(CODE_RE_ACCOUNT.match(code))


def is_valid_unban_code(code: str) -> bool:
    return bool(CODE_RE_UNBAN.match(code))


def parse_duration(s: str):
    """60d, 12h, 2m -> datetime (UTC, timezone-aware)."""
    m = re.match(r"^(\d+)([hdm])$", s)
    if not m:
        return None
    n = int(m.group(1))
    unit = m.group(2)
    if unit == "h":
        delta = timedelta(hours=n)
    elif unit == "d":
        delta = timedelta(days=n)
    else:  # m
        delta = timedelta(days=n * 30)
    return datetime.now(timezone.utc) + delta


def now_utc():
    return datetime.now(timezone.utc)