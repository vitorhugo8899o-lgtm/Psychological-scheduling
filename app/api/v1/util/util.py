from datetime import UTC, datetime, timedelta, timezone
from zoneinfo import ZoneInfo


def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def format_hour_br(date: datetime):
    br_tmz = ZoneInfo('America/Sao_Paulo')

    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)

    date_format = date.astimezone(br_tmz)

    return date_format.strftime('%d/%m/%Y às %H:%M')


def time_passed(date_compare: datetime) -> bool:
    return datetime.now(UTC) >= date_compare + timedelta(hours=24)
