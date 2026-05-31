from datetime import UTC, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from time import perf_counter
from functools import wraps


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


def cauculation_rate(total_appoinments: int, total_compared: int):
    if total_appoinments | total_compared == 0:
        return

    rate = (total_compared / total_appoinments) * 100

    return f'{rate:.2f}'.replace('.', ',')



def measure_time(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        init = perf_counter()

        result = await func(*args, **kwargs)

        end = perf_counter()
        print(f"{func.__name__} executou em {(end - init):.6f}s")

        return result

    return wrapper
