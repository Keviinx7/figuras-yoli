from datetime import datetime, timezone
from zoneinfo import ZoneInfo

LOCAL_ZONE=ZoneInfo('America/Guayaquil')

def localtime(value):
    if value is None: return '—'
    if value.tzinfo is None: value=value.replace(tzinfo=timezone.utc)
    return value.astimezone(LOCAL_ZONE).strftime('%d/%m/%Y %H:%M')+' (America/Guayaquil)'


def local_today():
    return datetime.now(LOCAL_ZONE).date()
