"""Tests for payment date generation."""

from datetime import date

from core.services.payment_schedule import upcoming_payment_dates


def test_biweekly_skips_past_and_keeps_14_day_gap():
    dates = upcoming_payment_dates(
        frequency="biweekly",
        anchor=date(2026, 8, 7),
        due_date_day=None,
        today=date(2026, 9, 1),
        limit=4,
    )
    assert dates == [
        date(2026, 9, 4),
        date(2026, 9, 18),
        date(2026, 10, 2),
        date(2026, 10, 16),
    ]


def test_weekly_from_today():
    dates = upcoming_payment_dates(
        frequency="weekly",
        anchor=date(2026, 9, 1),
        due_date_day=None,
        today=date(2026, 9, 1),
        limit=3,
    )
    assert dates == [date(2026, 9, 1), date(2026, 9, 8), date(2026, 9, 15)]


def test_remaining_payments_caps_list():
    dates = upcoming_payment_dates(
        frequency="biweekly",
        anchor=date(2026, 9, 4),
        due_date_day=None,
        today=date(2026, 9, 1),
        remaining_payments=2,
        limit=12,
    )
    assert len(dates) == 2


def test_end_date_stops_schedule():
    dates = upcoming_payment_dates(
        frequency="biweekly",
        anchor=date(2026, 9, 4),
        due_date_day=None,
        today=date(2026, 9, 1),
        end_date=date(2026, 9, 20),
        limit=12,
    )
    assert dates == [date(2026, 9, 4), date(2026, 9, 18)]


def test_monthly_from_due_day():
    dates = upcoming_payment_dates(
        frequency=None,
        anchor=None,
        due_date_day=15,
        today=date(2026, 9, 1),
        limit=3,
    )
    assert dates[0] == date(2026, 9, 15)
    assert dates[1] == date(2026, 10, 15)


def test_no_rule_returns_empty():
    assert upcoming_payment_dates(
        frequency=None,
        anchor=None,
        due_date_day=None,
        today=date(2026, 9, 1),
    ) == []


def test_include_overdue_prepends_missed_biweekly():
    dates = upcoming_payment_dates(
        frequency="biweekly",
        anchor=date(2026, 8, 7),
        due_date_day=None,
        today=date(2026, 9, 1),
        limit=3,
        include_overdue=True,
    )
    assert dates[0] == date(2026, 8, 21)
    assert dates[1] == date(2026, 9, 4)


def test_include_overdue_prepends_missed_monthly():
    dates = upcoming_payment_dates(
        frequency=None,
        anchor=None,
        due_date_day=15,
        today=date(2026, 9, 1),
        limit=2,
        include_overdue=True,
    )
    assert dates[0] == date(2026, 8, 15)
    assert dates[1] == date(2026, 9, 15)
