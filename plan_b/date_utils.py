from calendar import monthrange
from datetime import date

from dateutil import rrule


def get_months_range(start_date: date, end_date: date):
    for d in rrule.rrule(
        freq=rrule.MONTHLY,
        dtstart=date(start_date.year, start_date.month, 1),
        until=end_date,
        bymonthday=1,
        cache=True
    ):
        yield d.date()


def get_month_workdays_count(start_date: date, end_date: date, production_calendar: dict):
    result = {}
    for d in get_months_range(start_date, end_date):
        workdays = 0

        _, last_month_day = monthrange(d.year, d.month)
        for day in rrule.rrule(
            freq=rrule.DAILY, bymonth=d.month, dtstart=d, until=date(d.year, d.month, last_month_day)
        ):
            production_calendar_for_month = production_calendar[d.year][d.month - 1]

            if day.date() < start_date:
                # skip days before start date
                continue

            if day.date() > end_date:
                # stop on end date
                break

            if (
                day.weekday() in (5, 6) or day.day in production_calendar_for_month['holidays']
            ) and day.day not in production_calendar_for_month['workdays']:
                # skip holidays
                continue

            workdays += 1

        result[d] = workdays

    return result
