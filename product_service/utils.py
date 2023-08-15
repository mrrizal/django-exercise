from datetime import datetime
from django.utils import timezone


def to_indonesia_timezone(utc_time, datetime_format="%Y-%m-%dT%H:%M:%S.%f%z"):
    indonesia_timezone = timezone.get_fixed_timezone(7 * 60)
    utc_time = datetime.strptime(utc_time, datetime_format)
    indonesia_time = utc_time.astimezone(indonesia_timezone)
    return indonesia_time
