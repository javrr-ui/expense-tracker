"""Generate future payment dates from a recurrence rule.

Dates are computed, not stored. A known anchor date (typically the next or last
payment) plus a frequency is enough to list upcoming dues.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from dateutil.relativedelta import relativedelta

from constants.payment_frequency import PaymentFrequency

DEFAULT_LIMIT = 24


def upcoming_payment_dates(
    *,
    frequency: Optional[str],
    anchor: Optional[date],
    due_date_day: Optional[int],
    today: date,
    end_date: Optional[date] = None,
    remaining_payments: Optional[int] = None,
    limit: int = DEFAULT_LIMIT,
    include_overdue: bool = False,
) -> list[date]:
    """Return upcoming due dates on or after today.

    When include_overdue is True, prepend the most recent missed date so the
    dashboard can flag a payment that is already late.
    """
    if remaining_payments is not None and remaining_payments <= 0:
        return []

    cap = limit if remaining_payments is None else min(limit, remaining_payments)

    if frequency == PaymentFrequency.WEEKLY:
        dates = _from_interval(anchor, timedelta(weeks=1), today, end_date, cap)
        step: timedelta | relativedelta | None = timedelta(weeks=1)
    elif frequency == PaymentFrequency.BIWEEKLY:
        dates = _from_interval(anchor, timedelta(weeks=2), today, end_date, cap)
        step = timedelta(weeks=2)
    elif frequency == PaymentFrequency.MONTHLY or due_date_day is not None:
        dates = _monthly(anchor, due_date_day, today, end_date, cap)
        step = relativedelta(months=1)
    else:
        return []

    if include_overdue:
        dates = _prepend_overdue(
            dates,
            today=today,
            end_date=end_date,
            step=step,
            due_date_day=due_date_day,
            anchor=anchor,
        )
        if remaining_payments is not None:
            dates = dates[:remaining_payments]
    return dates


def _prepend_overdue(
    dates: list[date],
    *,
    today: date,
    end_date: Optional[date],
    step: timedelta | relativedelta,
    due_date_day: Optional[int],
    anchor: Optional[date],
) -> list[date]:
    if not dates:
        return dates
    first = dates[0]
    previous = first - step
    if isinstance(step, relativedelta):
        day = anchor.day if anchor is not None else due_date_day
        if day is not None:
            previous = _clamp_day(previous.year, previous.month, day)
    if previous >= today:
        return dates
    if end_date is not None and previous > end_date:
        return dates
    if previous in dates:
        return dates
    return [previous] + dates


def _from_interval(
    anchor: Optional[date],
    step: timedelta,
    today: date,
    end_date: Optional[date],
    cap: int,
) -> list[date]:
    if anchor is None:
        return []
    cursor = anchor
    # Bound the catch-up so a very old anchor cannot loop forever.
    max_steps = 2000
    steps = 0
    while cursor < today and steps < max_steps:
        cursor += step
        steps += 1
    dates: list[date] = []
    while len(dates) < cap:
        if end_date is not None and cursor > end_date:
            break
        dates.append(cursor)
        cursor += step
    return dates


def _monthly(
    anchor: Optional[date],
    due_date_day: Optional[int],
    today: date,
    end_date: Optional[date],
    cap: int,
) -> list[date]:
    day = anchor.day if anchor is not None else due_date_day
    if day is None:
        return []

    if anchor is not None and anchor >= today:
        cursor = anchor
    else:
        year, month = today.year, today.month
        cursor = _clamp_day(year, month, day)
        if cursor < today:
            cursor = cursor + relativedelta(months=1)
            cursor = _clamp_day(cursor.year, cursor.month, day)

    dates: list[date] = []
    while len(dates) < cap:
        if end_date is not None and cursor > end_date:
            break
        dates.append(cursor)
        nxt = cursor + relativedelta(months=1)
        cursor = _clamp_day(nxt.year, nxt.month, day)
    return dates


def _clamp_day(year: int, month: int, day: int) -> date:
    import calendar

    last = calendar.monthrange(year, month)[1]
    return date(year, month, min(day, last))
