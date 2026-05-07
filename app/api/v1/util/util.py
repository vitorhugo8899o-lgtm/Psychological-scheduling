from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def format_to_user(utc_time: str):
    date_today_utc = datetime.now(ZoneInfo('UTC')).replace(
        hour=utc_time.hout, minute=utc_time.minute
    )

    date_br = date_today_utc.astimezone(ZoneInfo('America/Sao_Paulo'))

    return date_br.strftime('%H:%M')


def format_conflit(utc_time: str):
    convert = utc_time.replace('Z', '+00:00')

    dt = datetime.fromisoformat(convert)

    hour_format = dt.strftime('%H:%M')

    return hour_format


def time_is_passad(time: datetime) -> bool:
    if time <= datetime.now(time.tzinfo):
        return True
    else:
        return False


def convert_datehour_to_date(date: datetime) -> datetime:
    return date.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)


def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def format_hour_br(date: datetime):
    br_tmz = ZoneInfo('America/Sao_Paulo')

    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)

    date_format = date.astimezone(br_tmz)

    return date_format.strftime("%d/%m/%Y às %H:%M")
